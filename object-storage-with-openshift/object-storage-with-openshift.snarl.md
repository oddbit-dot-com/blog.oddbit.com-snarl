---
categories:
- tech
date: '2021-02-09'
filename: 2021-02-09-object-storage-with-openshift.md
stub: object-storage-with-openshift
tags:
- openshift
- s3
- kubernetes
title: Object storage with OpenShift Container Storage

---

OpenShift Container Storage (OCS) from Red Hat deploys Ceph in your
OpenShift cluster (or allows you to integrate with an external Ceph
cluster). In addition to the file- and block- based volume services
provided by Ceph, OCS includes two S3-api compatible object storage
implementations.

The first option is the [Ceph Object Gateway][radosgw] (radosgw),
Ceph's native object storage interface. The second option called the
"[Multicloud Object Gateway][]", which is in fact a piece of software
named [Noobaa][], a storage abstraction layer that was [acquired by
Red Hat][] in 2018.  In this article I'd like to demonstrate how to
take advantage of these storage options.

[radosgw]: https://docs.ceph.com/en/latest/radosgw/
[noobaa]: https://www.noobaa.io/
[acquired by red hat]: https://www.redhat.com/en/blog/faq-red-hat-acquires-noobaa
[multicloud object gateway]: https://www.openshift.com/blog/introducing-multi-cloud-object-gateway-for-openshift

## What is object storage?

The storage we interact with regularly on our local computers is
block storage: data is stored as a collection of blocks on some sort
of storage device. Additional layers -- such as a filesystem driver --
are responsible for assembling those blocks into something useful.

Object storage, on the other hand, manages data as objects: a single
unit of data and associated metadata (such as access policies). An
object is identified by some sort of unique id. Object storage
generally provides an API that is largely independent of the physical
storage layer; data may live on a variety of devices attached to a
variety of systems, and you don't need to know any of those details in
order to access the data.

The most well known example of object storage service Amazon's
[S3][] service ("Simple Storage Service"), first introduced in 2006.
The S3 API has become a de-facto standard for object storage
implementations. The two services we'll be discussing in this article
provide S3-compatible APIs.

[s3]: https://aws.amazon.com/s3/

## Getting started: Creating buckets

The fundamental unit of object storage is called a "bucket".

Creating a bucket with OCS works a bit like creating a [persistent
volume][], although instead of starting with a `PersistentVolumeClaim`
you instead start with an `ObjectBucketClaim` ("`OBC`"). An `OBC`
looks something like this when using RGW:

[persistent volume]: https://kubernetes.io/docs/concepts/storage/persistent-volumes/

```yaml=obc-rgw.yml --file
apiVersion: objectbucket.io/v1alpha1
kind: ObjectBucketClaim
metadata:
  name: example-rgw
spec:
  generateBucketName: example-rgw
  storageClassName: ocs-storagecluster-ceph-rgw
```

Or like this when using Noobaa:

```yaml=obc-nooba.yml --file
apiVersion: objectbucket.io/v1alpha1
kind: ObjectBucketClaim
metadata:
  name: example-noobaa
spec:
  generateBucketName: example-noobaa
  storageClassName: openshift-storage.noobaa.io
```

With OCS 4.5, your out-of-the-box choices for `storageClassName` will be
`ocs-storagecluster-ceph-rgw`, if you choose to use Ceph Radosgw, or
`openshift-storage.noobaa.io`, if you choose to use the Noobaa S3 endpoint.

Because we set `generateName` in the `ObjectBucketClaim`, the above
configuration will result in a bucket named `mybucket-<some random
string>`. Because buckets exist in a flat namespace, the OCS documentation
recommends always using `generateName`, rather than explicitly setting
`bucketName`, in order to avoid unexpected conflicts.

This will create a bucket in your chosen backend, along with two other
resources:

- A `Secret` containing the AWS-style credentials for interacting with the
  bucket via the S3 API, and
- A `ConfigMap` containing information about the bucket.

Both will have the same name as your `OBC`.  The `Secret` contains
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` keys, like this:

```
apiVersion: v1
kind: Secret
metadata:
  name: mybucket
type: Opaque
data:
  AWS_ACCESS_KEY_ID: ...
  AWS_SECRET_ACCESS_KEY: ...
```

The `ConfigMap` contains a number of keys that provide you (or your code)
with the information necessary to access the bucket:


```
apiVersion: v1
kind: ConfigMap
metadata:
  name: mybucket
data:
  BUCKET_HOST: rook-ceph-rgw-ocs-storagecluster-cephobjectstore.openshift-storage.svc.cluster.local
  BUCKET_NAME: mybucket-3ffec462-3871-4963-a7e7-1eb7102ebef5
  BUCKET_PORT: '80'
  BUCKET_REGION: us-east-1
  BUCKET_SUBREGION: ''
```

Note that `BUCKET_HOST` contains the internal S3 API endpoint. You won't be
able to reach this from outside the cluster. We'll tackle that in just a
bit.

## Accessing a bucket from a pod

The easiest way to expose the credentials in a pod is to map the keys
from both the `ConfigMap` and `Secret` as environment variables using
the `envFrom` directive, like this:

```
apiVersion: v1
kind: Pod
metadata:
  name: bucket-example
spec:
  containers:
    - image: myimage
      env:
        - name: AWS_CA_BUNDLE
          value: /run/secrets/kubernetes.io/serviceaccount/service-ca.crt
      envFrom:
        - configMapRef:
            name: example-rgw
        - secretRef:
            name: example-rgw
      [...]
```

Note that we're also setting `AWS_CA_BUNDLE` here, which you'll need
if the internal endpoint referenced by `$BUCKET_HOST` is using SSL.

Inside the pod, we can run, for example, `aws` commands as long as we
provide an appropriate s3 endpoint. We can inspect the value of
`BUCKET_PORT` to determine if we need `http` or `https`:

```
$ [ "$BUCKET_PORT" = 80 ] && schema=http || schema=https
$ aws s3 ls --endpoint $schema://$BUCKET_HOST ls
2021-02-10 04:30:31 example-rgw-8710aa46-a47a-4a8b-8edd-7dabb7d55469
```

Python's `boto3` module can also make use of the same environment
variables:

```python
>>> import boto3
>>> import os
>>> bucket_host = os.environ['BUCKET_HOST']
>>> schema = 'http' if os.environ['BUCKET_PORT'] == 80 else 'https'
>>> s3 = boto3.client('s3', endpoint_url=f'{schema}://{bucket_host}')
>>> s3.list_buckets()['Buckets']
[{'Name': 'example-noobaa-...', 'CreationDate': datetime.datetime(...)}]

```

## External connections to S3 endpoints

External access to services in OpenShift is often managed via
[routes][].  If you look at the routes available in your
`openshift-storage` namespace, you'll find the following:

[routes]: https://docs.openshift.com/enterprise/3.0/architecture/core_concepts/routes.html

```
$ oc -n openshift-storage get route
NAME          HOST/PORT                                               PATH   SERVICES                                           PORT         TERMINATION   WILDCARD
noobaa-mgmt   noobaa-mgmt-openshift-storage.apps.example.com          noobaa-mgmt                                        mgmt-https   reencrypt     None
s3            s3-openshift-storage.apps.example.com                   s3                                                 s3-https     reencrypt     None
```

The `s3` route provides external access to your Noobaa S3 endpoint.
You'll note that in the list above there is no route registered for
radosgw[^ocs46]. There is a service registered for Radosgw named
`rook-ceph-rgw-ocs-storagecluster-cephobjectstore`, so we
can expose that service to create an external route by running
something like:

```
oc create route edge rgw --service rook-ceph-rgw-ocs-storagecluster-cephobjectstore
```

This will create a route with "edge" encryption (TLS termination is
handled by the default ingress router):

```
$ oc -n openshift storage get route
NAME          HOST/PORT                                               PATH   SERVICES                                           PORT         TERMINATION   WILDCARD
noobaa-mgmt   noobaa-mgmt-openshift-storage.apps.example.com          noobaa-mgmt                                        mgmt-https   reencrypt     None
rgw           rgw-openshift-storage.apps.example.com                  rook-ceph-rgw-ocs-storagecluster-cephobjectstore   http         edge          None
s3            s3-openshift-storage.apps.example.com                   s3                                                 s3-https     reencrypt     None
```

[^ocs46]: note that this may have changed in the recent OCS 4.6
  release

## Accessing a bucket from outside the cluster

Once we know the `Route` to our S3 endpoint, we can use the information
in the `ConfigMap` created for us when we provisioned the storage. We
just need to replace the `BUCKET_HOST` with the hostname in the route,
and we need to use port 443 regardless of what `BUCKET_PORT` tells us.

```python=getenv.py --file
import argparse
import base64

import kubernetes
import openshift.dynamic


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-n', '--namespace', required=True)
    p.add_argument('-N', '--route-namespace', default='openshift-storage')
    p.add_argument('-r', '--route')
    p.add_argument('obcname')
    return p.parse_args()


args = parse_args()
k8s_client = kubernetes.config.new_client_from_config()
dyn_client = openshift.dynamic.DynamicClient(k8s_client)

v1_configmap = dyn_client.resources.get(api_version='v1', kind='ConfigMap')
v1_secret = dyn_client.resources.get(api_version='v1', kind='Secret')
v1_route = dyn_client.resources.get(api_version='route.openshift.io/v1', kind='Route')

configmap = v1_configmap.get(name=args.obcname, namespace=args.namespace)
secret = v1_secret.get(name=args.obcname, namespace=args.namespace)

env = dict(configmap.data)
env.update({k: base64.b64decode(v).decode() for k, v in secret.data.items()})

if args.route:
    route = v1_route.get(name=args.route, namespace=args.route_namespace)
    env['BUCKET_PORT'] = 443
    env['BUCKET_HOST'] = route['spec']['host']

for k, v in env.items():
    print(f'{k}="{v}"')
```

This will output something like:

```sh
BUCKET_HOST="s3-openshift-storage.apps.cnv.massopen.cloud"
BUCKET_NAME="example-noobaa-2e1bca2f-ff49-431a-99b8-d7d63a8168b0"
BUCKET_PORT="443"
BUCKET_REGION=""
BUCKET_SUBREGION=""
AWS_ACCESS_KEY_ID="RrRd1aDjSoLkjXXvESyh"
AWS_SECRET_ACCESS_KEY="F/GW0yXTjL5wNl5fghxwZgy0EXeMGZssFkiowICx"
```

## Applying a bucket policy
