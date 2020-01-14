import pytest

testinfra_hosts = ['ansible://ovn_nodes']


ports = {
    ('port1', 'vm1', 'c0:ff:ee:00:00:11'),
    ('port2', 'vm2', 'c0:ff:ee:00:00:12'),
    ('port3', 'vm3', 'c0:ff:ee:00:00:13'),
}


@pytest.mark.parametrize('port,netns,mac', ports)
def test_port_mac(host, hostname, port, netns, mac):
    with host.sudo():
        res = host.run(f'ovs-vsctl list port {port}')
        if res.exit_status != 0:
            pytest.skip(f'port {port} is not bound on host {hostname}')
        res = host.run(f'ip netns exec {netns} cat /sys/class/net/{port}/address')
        assert res.stdout.strip() == mac


@pytest.mark.parametrize('port,netns,mac', ports)
@pytest.mark.parametrize(
    'addr',
    ['10.0.0.11', '10.0.0.12', '10.0.0.13'])
def test_port_ping(host, hostname, port, netns, mac, addr):
    with host.sudo():
        res = host.run(f'ovs-vsctl list port {port}')
        if res.exit_status != 0:
            pytest.skip(f'port {port} is not bound on host {hostname}')
        res = host.run(f'ip netns exec {netns} ping -c1 {addr}')
        assert res.exit_status == 0
