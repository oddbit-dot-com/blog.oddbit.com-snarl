import json
import pytest

testinfra_hosts = ['ansible://ovn_central']

ports = {
    ('port1', 'c0:ff:ee:00:00:11'),
    ('port2', 'c0:ff:ee:00:00:12'),
    ('port3', 'c0:ff:ee:00:00:13'),
}


@pytest.mark.parametrize('service', ['ovn-northd'])
def test_services(host, service):
    with host.sudo():
        res = host.run(f'systemctl is-active {service}')
        assert res.exit_status == 0


def test_ovnsb_connection(host):
    with host.sudo():
        res = host.run('ovn-sbctl get-connection')
        assert 'ptcp:6642' in res.stdout


def test_net0_exists(host):
    with host.sudo():
        res = host.run('ovn-nbctl list logical_switch net0')
        assert res.exit_status == 0


@pytest.mark.parametrize('port', ['port1', 'port2', 'port3'])
def test_port_exists(host, port):
    with host.sudo():
        res = host.run(f'ovn-nbctl list logical_switch_port {port}')
        assert res.exit_status == 0


@pytest.mark.parametrize('port,mac', ports)
def test_port_mac(host, port, mac):
    with host.sudo():
        res = host.run(f'ovn-nbctl --columns=name,address -f json '
                       f'list logical_switch_port {port}')
        assert res.exit_status == 0
        data = json.loads(res.stdout)
        data = dict(data['data'])
        assert data[port].split()[0] == mac


@pytest.mark.parametrize('port', ['port1', 'port2', 'port3'])
def test_port_bound(host, port):
    with host.sudo():
        res = host.run(f'ovn-sbctl -t 5 list port_binding {port}')
        assert res.exit_status == 0


def test_dhcp_options_exist(host):
    with host.sudo():
        res = host.run('ovn-nbctl -f json --columns _uuid '
                       'find dhcp_options cidr=10.0.0.0/24')
        data = json.loads(res.stdout)
        data = dict(data['data'][0])

        assert 'uuid' in data


@pytest.mark.parametrize('port', ['port1', 'port2', 'port3'])
def test_port_has_dhcp_options(host, port):
    with host.sudo():
        res = host.run('ovn-nbctl -f json --columns _uuid '
                       'find dhcp_options cidr=10.0.0.0/24')
        data = json.loads(res.stdout)
        data = dict(data['data'][0])
        options_uuid = data['uuid']

        res = host.run('ovn-nbctl -f json --columns dhcpv4_options '
                       f'list logical_switch_port {port}')
        data = json.loads(res.stdout)
        data = dict(data['data'][0])
        assert data['uuid'] == options_uuid
