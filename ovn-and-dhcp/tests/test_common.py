testinfra_hosts = ['ansible://ovn']


def test_hostname(host, hostname):
    assert host.check_output('hostname -s') == hostname


def test_br_int_exists(host):
    res = host.run('ovs-vsctl br-exists br-int')
    assert res.exit_status == 0


def test_ovn_remote(host):
    res = host.run('ovs-vsctl get open_vswitch . external_ids:ovn-remote')
    assert res.exit_status == 0
    assert 'tcp:192.168.122.100:6642' in res.stdout
