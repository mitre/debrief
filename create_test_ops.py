#!/usr/bin/env python3
"""Inject realistic multi-hop operations into running Caldera via API.

Usage:
    source ~/Desktop/CalderaVENVDebrief/bin/activate
    python create_test_ops.py

Creates two operations with realistic hostnames:
  1. "Corporate Pentest" — 4 hosts, 3 VLANs, 1 dual-homed pivot
  2. "Enterprise Red Team" — 10 hosts, 3 VLANs, 2 dual-homed pivots
"""
import requests

BASE = 'http://localhost:8888'


def login():
    s = requests.Session()
    s.post(f'{BASE}/enter', data={'username': 'admin', 'password': 'admin'}, allow_redirects=False)
    return s


def create_agent(s, paw, host, platform, ips, **kw):
    data = {
        'paw': paw, 'host': host, 'platform': platform,
        'host_ip_addrs': ips, 'group': kw.get('group', 'red'),
        'privilege': kw.get('privilege', 'User'),
        'username': kw.get('username', 'user'), 'exe_name': kw.get('exe', 'sandcat'),
        'contact': kw.get('contact', 'HTTP'),
        'sleep_min': 30, 'sleep_max': 60, 'watchdog': 0,
        'architecture': 'amd64', 'pid': abs(hash(paw)) % 60000 + 1000, 'ppid': 1,
        'executors': ['sh'] if platform == 'linux' else ['psh'],
        'location': f'/tmp/sandcat' if platform == 'linux' else f'C:\\Users\\{kw.get("username","user")}\\sandcat.exe',
    }
    r = s.post(f'{BASE}/api/v2/agents', json=data)
    print(f'    {paw:12} {host:20} {platform:8} {",".join(ips)}')


def create_op(s, name):
    adv = s.get(f'{BASE}/api/v2/adversaries').json()
    data = {
        'name': name,
        'adversary': {'adversary_id': adv[0]['adversary_id']},
        'planner': {'id': 'aaa7c857-44fa-4095-b5bf-525024300413'},
        'source': {'id': 'ed32b9c3-9593-4c33-b0db-e2007315096b'},
        'auto_close': False, 'state': 'running', 'group': 'red',
    }
    op = s.post(f'{BASE}/api/v2/operations', json=data).json()
    s.patch(f'{BASE}/api/v2/operations/{op["id"]}', json={'state': 'finished'})
    return op['id']


def main():
    s = login()
    print('Connected.\n')

    # === Operation 1: Corporate Pentest ===
    print('=== Corporate Pentest ===')
    print('  C2 → WEBPROD01 (DMZ) → INTFW01 (dual-homed) → YOURDC01 (Corp) → SQLPROD01 (DB)')
    print('  Agents:')
    create_agent(s, 'wp01', 'WEBPROD01', 'linux', ['10.10.1.50'],
                 username='www-data', privilege='User')
    create_agent(s, 'fw01', 'INTFW01', 'linux', ['10.10.1.1', '172.16.5.1'],
                 username='root', privilege='Elevated', contact='P2P')
    create_agent(s, 'dc01', 'YOURDC01', 'windows', ['172.16.5.10'],
                 username='CORP\\svc_admin', privilege='Elevated')
    create_agent(s, 'sql01', 'SQLPROD01', 'linux', ['172.16.10.20'],
                 username='postgres', privilege='User')
    op1 = create_op(s, 'Corporate Pentest')
    print(f'  Op: {op1}\n')

    # === Operation 2: Enterprise Red Team ===
    print('=== Enterprise Red Team ===')
    print('  3 VLANs: DMZ (10.50.1.0/24), Corp (172.20.5.0/24), Servers (172.20.10.0/24)')
    print('  2 dual-homed pivots, 10 hosts total')
    print('  Agents:')

    # DMZ — 10.50.1.0/24
    create_agent(s, 'web1', 'EXTWEBSRV01', 'linux', ['10.50.1.10'],
                 username='nginx', privilege='User')
    create_agent(s, 'mail1', 'MAILRELAY01', 'linux', ['10.50.1.20'],
                 username='postfix', privilege='User')
    # Dual-homed jump box: DMZ ↔ Corporate
    create_agent(s, 'jmp1', 'YOURJMPBOX01', 'linux', ['10.50.1.5', '172.20.5.1'],
                 username='root', privilege='Elevated', contact='P2P')

    # Corporate — 172.20.5.0/24
    create_agent(s, 'ws1', 'YOURWS001', 'windows', ['172.20.5.50'],
                 username='CORP\\jdoe', privilege='User')
    create_agent(s, 'ws2', 'YOURWS002', 'windows', ['172.20.5.51'],
                 username='CORP\\jsmith', privilege='User')
    create_agent(s, 'adc1', 'YOURDC01', 'windows', ['172.20.5.10'],
                 username='CORP\\admin', privilege='Elevated')
    create_agent(s, 'fs1', 'YOURFILES01', 'windows', ['172.20.5.100'],
                 username='CORP\\svc_file', privilege='User')

    # Dual-homed app server: Corporate ↔ Servers
    create_agent(s, 'app1', 'YOURAPP01', 'linux', ['172.20.5.2', '172.20.10.1'],
                 username='tomcat', privilege='Elevated', contact='P2P')

    # Servers/DB — 172.20.10.0/24
    create_agent(s, 'db1', 'SQLMASTER01', 'linux', ['172.20.10.50'],
                 username='postgres', privilege='User')
    create_agent(s, 'bk1', 'YOURBKUP01', 'linux', ['172.20.10.60'],
                 username='backup', privilege='User')

    op2 = create_op(s, 'Enterprise Red Team')
    print(f'  Op: {op2}\n')

    print(f'Done. Select operations in Debrief and press Play.')


if __name__ == '__main__':
    main()
