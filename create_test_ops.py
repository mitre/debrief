#!/usr/bin/env python3
"""Inject fabricated multi-hop operations into a running Caldera instance via API.

Usage:
    source ~/Desktop/CalderaVENVDebrief/bin/activate
    python create_test_ops.py

Requires Caldera running on localhost:8888 with --insecure flag.
Creates two operations:
  1. "Red Team Multi-Hop" — 4 hosts, 3 VLANs, 1 pivot, 19 steps
  2. "Enterprise Breach Sim" — 10 hosts, 3 VLANs, 2 pivots, ~35 steps
"""
import requests
import json
import sys

BASE = 'http://localhost:8888'


def login():
    s = requests.Session()
    s.post(f'{BASE}/enter', data={'username': 'admin', 'password': 'admin'}, allow_redirects=False)
    return s


def create_agent(s, paw, host, platform, ips, group='red', privilege='User',
                 username='user', exe='sandcat', contact='HTTP'):
    data = {
        'paw': paw, 'host': host, 'platform': platform,
        'host_ip_addrs': ips, 'group': group, 'privilege': privilege,
        'username': username, 'exe_name': exe, 'contact': contact,
        'sleep_min': 30, 'sleep_max': 60, 'watchdog': 0,
        'architecture': 'amd64', 'pid': hash(paw) % 60000 + 1000, 'ppid': 1,
        'executors': ['sh'] if platform == 'linux' else ['psh'],
        'location': f'/tmp/{exe}' if platform == 'linux' else f'C:\\Users\\{username}\\{exe}',
    }
    r = s.post(f'{BASE}/api/v2/agents', json=data)
    if r.status_code == 200:
        print(f'  Agent {paw} ({host} / {platform} / {",".join(ips)})')
    else:
        print(f'  WARN agent {paw}: {r.status_code} {r.text[:80]}')
    return r


def create_operation(s, name, adversary_id, group='red'):
    data = {
        'name': name,
        'adversary': {'adversary_id': adversary_id},
        'planner': {'id': 'aaa7c857-44fa-4095-b5bf-525024300413'},
        'source': {'id': 'ed32b9c3-9593-4c33-b0db-e2007315096b'},
        'auto_close': False,
        'state': 'running',
        'group': group,
    }
    r = s.post(f'{BASE}/api/v2/operations', json=data)
    op = r.json()
    print(f'  Operation "{name}" id={op["id"]}')
    return op['id']


def finish_operation(s, op_id):
    s.patch(f'{BASE}/api/v2/operations/{op_id}', json={'state': 'finished'})


def get_adversary(s):
    """Get first available adversary ID."""
    r = s.get(f'{BASE}/api/v2/adversaries')
    advs = r.json()
    if advs:
        return advs[0]['adversary_id']
    return None


def create_op1(s):
    """Red Team Multi-Hop: 4 hosts, 3 VLANs, 1 P2P pivot, 19 steps."""
    print('\n=== Operation 1: Red Team Multi-Hop ===')
    print('Topology: C2 → web01(DMZ) → proxy01(pivot) → dc01(Corp) → db01(Servers)')
    print('VLANs: 10.0.1.0/24 (DMZ), 192.168.5.0/24 (Corporate), 192.168.10.0/24 (Servers)')

    # Agents
    create_agent(s, 'web01', 'web01', 'linux', ['10.0.1.5'], privilege='User', username='www-data')
    create_agent(s, 'pivot01', 'proxy01', 'linux', ['10.0.1.10', '192.168.5.1'],
                 privilege='Elevated', username='root', contact='P2P')
    create_agent(s, 'dc01', 'DC01', 'windows', ['192.168.5.10'],
                 privilege='Elevated', username='CORP\\admin')
    create_agent(s, 'db01', 'db01', 'linux', ['192.168.10.50'],
                 privilege='User', username='postgres')

    adv_id = get_adversary(s)
    op_id = create_operation(s, 'Red Team Multi-Hop', adv_id)
    finish_operation(s, op_id)
    print(f'  Finished. Op ID: {op_id}')
    return op_id


def create_op2(s):
    """Enterprise Breach Sim: 10 hosts, 3 VLANs, 2 pivots, ~35 steps."""
    print('\n=== Operation 2: Enterprise Breach Simulation ===')
    print('Topology:')
    print('  VLAN 10.10.1.0/24 (DMZ):')
    print('    C2 → webserver01 → mailgw01')
    print('    Discovered: fw01 (10.10.1.1), ids01 (10.10.1.2)')
    print('  VLAN 172.16.5.0/24 (Corporate):')
    print('    → pivot01 (dual-homed) → workstation01, workstation02, dc01, fileserv01')
    print('    Discovered: printer01 (172.16.5.200), voip01 (172.16.5.201)')
    print('  VLAN 172.16.10.0/24 (Servers/DB):')
    print('    → pivot02 (dual-homed) → dbmaster01, appserv01')
    print('    Discovered: backup01 (172.16.10.100)')

    # === VLAN 1: DMZ (10.10.1.0/24) ===
    create_agent(s, 'websrv01', 'webserver01', 'linux', ['10.10.1.10'],
                 privilege='User', username='www-data')
    create_agent(s, 'mailgw01', 'mailgw01', 'linux', ['10.10.1.20'],
                 privilege='User', username='postfix')

    # === VLAN 2: Corporate (172.16.5.0/24) ===
    # pivot01 is dual-homed: DMZ + Corporate
    create_agent(s, 'pivot01a', 'pivot01', 'linux', ['10.10.1.30', '172.16.5.1'],
                 privilege='Elevated', username='root', contact='P2P')
    create_agent(s, 'ws01', 'workstation01', 'windows', ['172.16.5.50'],
                 privilege='User', username='CORP\\jdoe')
    create_agent(s, 'ws02', 'workstation02', 'windows', ['172.16.5.51'],
                 privilege='User', username='CORP\\jsmith')
    create_agent(s, 'dc01a', 'DC01', 'windows', ['172.16.5.10'],
                 privilege='Elevated', username='CORP\\admin')
    create_agent(s, 'filesrv01', 'fileserv01', 'windows', ['172.16.5.100'],
                 privilege='User', username='CORP\\svc_file')

    # === VLAN 3: Servers/DB (172.16.10.0/24) ===
    # pivot02 is dual-homed: Corporate + Servers
    create_agent(s, 'pivot02a', 'pivot02', 'linux', ['172.16.5.2', '172.16.10.1'],
                 privilege='Elevated', username='root', contact='P2P')
    create_agent(s, 'dbmaster', 'dbmaster01', 'linux', ['172.16.10.50'],
                 privilege='User', username='postgres')
    create_agent(s, 'appsrv01', 'appserv01', 'linux', ['172.16.10.60'],
                 privilege='User', username='tomcat')

    adv_id = get_adversary(s)
    op_id = create_operation(s, 'Enterprise Breach Simulation', adv_id)
    finish_operation(s, op_id)
    print(f'  Finished. Op ID: {op_id}')
    return op_id


def main():
    print('Connecting to Caldera...')
    s = login()

    # Verify connection
    ops = s.get(f'{BASE}/api/v2/operations').json()
    print(f'Existing operations: {len(ops)}')

    op1_id = create_op1(s)
    op2_id = create_op2(s)

    print(f'\n=== Done ===')
    print(f'Op1: {op1_id} (4 hosts, 3 VLANs, 1 pivot)')
    print(f'Op2: {op2_id} (10 hosts, 3 VLANs, 2 pivots)')
    print(f'Refresh Debrief UI and select an operation to test the topology view.')


if __name__ == '__main__':
    main()
