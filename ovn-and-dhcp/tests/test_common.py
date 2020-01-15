import pytest
import re

testinfra_hosts = ['ansible://ovn']


def test_hostname(host, hostname):
    assert host.check_output('hostname -s') == hostname


def test_br_int_exists(host):
    with host.sudo():
        res = host.run('ovs-vsctl br-exists br-int')
        assert res.exit_status == 0


def test_ovn_remote(host):
    with host.sudo():
        res = host.run('ovs-vsctl get open_vswitch . external_ids:ovn-remote')
        assert res.exit_status == 0
        assert re.search(r'tcp:[\d.]+:6642', res.stdout)


def test_ovs_errors(host):
    with host.sudo():
        res = host.run('ovs-vsctl show')
        assert 'error:' not in res.stdout


@pytest.mark.parametrize('service',
                         ['ovs-vswitchd', 'ovsdb-server', 'ovn-controller'])
def test_services(host, service):
    with host.sudo():
        res = host.run(f'systemctl is-active {service}')
        assert res.exit_status == 0
