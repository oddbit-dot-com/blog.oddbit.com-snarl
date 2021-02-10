---
date: '2020-01-31'
filename: 2020-01-31-fixing-sourceforge-subversion.md
tags:
- bad_deas
- subversion
- git
- sourceforge
title: Fixing SourceForge subversion issues with function interposition

---

I ran into some problems while trying to clone [a large subversion repository][vice] from SourceForge using `git svn clone`.  While the process would start off just fine, it would eventually stop receiving data.  If I were to interrupt the process and then run `git svn fetch`, it would pick up where it left off but ultimately it would get stuck again.

[vice]: https://sourceforge.net/p/vice-emu/code/HEAD/tree/

My first inclination was just to wrap the `git svn fetch` command in something like this:

```
until giv svn fetch; do
  sleep 1
done
```

Unfortunately, it looks as if the existing timeout in `git svn` is ten minutes, which results in very slow progress.  Is there something we can do to force a shorter timeout when there hasn't been any read or write activity for a certain amount of time?

Spoiler: of course there is!

## Happiness through function interposition

Under Linux (and most other Unix-y operating systems), it is possible to use the dynamic loader to preload a shared library with predefined symbols that will override symbols of the same name in subsequent code. We call this _function interposition_ and we can use it to replace or wrap system calls such as `read` or `write` (or `epoll_wait`).

For example, if we wanted to override the `open()` system call so that any attempt to open a file would fail, we might write something like the following:

```=force_open_fail.c --file
#include <stdio.h>
#include <unistd.h>
#include <errno.h>

int open(const char *pathname, int flags) {
  fprintf(stderr, "No open for you!\n");
  errno = EACCES;
  return -1;
}
```

Note that the signature of our `open` function must match exactly the signature of the original.

From this we need to generate a shared library:

```=build_force_open_fail.sh --file
cc -fPIC   -c -o force_open_fail.o force_open_fail.c
ld -shared -o force_open_fail.so force_open_fail.o
```

Finally, we use `LD_PRELOAD` to preload this shared library before running our target code. This will cause calls to `open()` to fail with `EACCES` (and will print the message "No open for you!" on _stderr_):

```
$ LD_PRELOAD=$PWD/force_open_fail.so cat force_open_fail.c
No open for you!
cat: force_open_fail.c: Permission denied
```

What if we want to _wrap_ an existing system call, rather than _replace_ it? For example, what if we wanted to wrap the `open` call such that only attempts to open the file `target` would fail, but other uses of `open` would succeed?

In order to refer to the original symbol like this, we need the [dlsym][] function, which comes from the `dlfcn.h` header file. In on order to make all the symbols available that we will require, we also need to define `_GNU_SOURCE` before including the file:

[dlsym]: http://man7.org/linux/man-pages/man3/dlsym.3.html

```="include dlfcn.h"
#define _GNU_SOURCE
#include <dlfcn.h>
```

As part of our wrapper function, we will now to ensure that we obtain a reference to the original `open` function, like this:

```="get open reference"
static int (*real_open)(const char *, int) = NULL;

if (! real_open)
  real_open = dlsym(RTLD_NEXT, "open");
```

Later on, when we want to call the original `open` function, we instead call `real_open`:

```="call original open"
return real_open(pathname, flags);
```

```=fail_only_target.c --file
<<include dlfcn.h>>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

int open(const char *pathname, int flags) {
  <<get open reference>>

  if (strcmp(pathname, "target") == 0) {
    fprintf(stderr, "No open for you!\n");
    errno = EACCES;
    return -1;
  }

  <<call original open>>
}
```

Now that we're using the `dlsym()` function, we need to include the `dl` library when linking our shared library:

```=build_fail_only_target.sh --file
cc -fPIC   -c -o fail_only_target.o fail_only_target.c
ld -shared -o fail_only_target.so fail_only_target.o -ldl
```

Running `strace` on the process 

```
$ strace -p 2164758
strace: Process 2164758 attached
epoll_wait(4, [], 16, 500)              = 0
epoll_wait(4, [], 16, 500)              = 0
epoll_wait(4, [], 16, 500)              = 0
[...]
```

```
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/epoll.h>
#include <time.h>
#include <unistd.h>

#ifndef DEFAULT_IDLE_TIMEOUT
#define DEFAULT_IDLE_TIMEOUT 10
#endif // DEFAULT_IDLE_TIMEOUT

static time_t last_activity = 0;
static time_t idle_timeout = DEFAULT_IDLE_TIMEOUT;

static int (*real_epoll_wait)(int, struct epoll_event *, int, int) = NULL;
static ssize_t (*real_read)(int, void *, size_t) = NULL;
static ssize_t (*real_write)(int, void *, size_t) = NULL;

int epoll_wait(int epfd, struct epoll_event *events,
              int maxevents, int timeout) {
    time_t now;

    now = time(NULL);
    if (idle_timeout > 0 && (now - last_activity) > idle_timeout) {
        fprintf(stderr, "! idle timeout after ~ %d seconds\n", (int)idle_timeout);
        exit(1);
    }

    return real_epoll_wait(epfd, events, maxevents, timeout);
}


ssize_t read(int fd, void *buf, size_t count) {
    last_activity = time(NULL);
    return real_read(fd, buf, count);
}


ssize_t write(int fd, const void *buf, size_t count) {
    last_activity = time(NULL);
    return real_write(fd, (void *)buf, count);
}


static __attribute__((constructor)) void init_idlekiller(void) {
    real_epoll_wait = dlsym(RTLD_NEXT, "epoll_wait");
    real_read = dlsym(RTLD_NEXT, "read");
    real_write = dlsym(RTLD_NEXT, "write");

    if (getenv("IK_IDLE_TIMEOUT")) {
        idle_timeout = atoi(getenv("IK_IDLE_TIMEOUT"));
    }
}
```
