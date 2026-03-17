#!/usr/bin/env python3
"""Create a fabricated multi-hop lateral movement operation for testing the topology view.

Usage: python create_test_operation.py [caldera_url]

Creates:
- 4 agents across 3 subnets (DMZ, Corporate, Servers)
- 1 P2P proxy pivot agent
- Lateral movement chain: C2 → web01 → proxy01(P2P) → dc01 → db01
- ~20 steps across the hosts
- Discovered hosts (no agents) via remote.host.ip facts
"""
import asyncio
import sys
import os

# Add caldera to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from base64 import b64encode
from datetime import datetime, timedelta

from app.objects.c_ability import Ability
from app.objects.c_adversary import Adversary
from app.objects.c_agent import Agent
from app.objects.c_operation import Operation
from app.objects.c_source import Source
from app.objects.c_objective import Objective
from app.objects.c_planner import Planner
from app.objects.secondclass.c_executor import Executor
from app.objects.secondclass.c_link import Link
from app.objects.secondclass.c_fact import Fact
from app.utility.base_object import BaseObject


def _encode(s):
    return b64encode(s.encode()).decode()


def _make_ability(name, tactic, tid, tname, platform='linux'):
    executor = Executor(name='sh' if platform == 'linux' else 'psh',
                        platform=platform, command='echo test')
    return Ability(
        ability_id=f'test-{name.replace(" ", "-").lower()}',
        tactic=tactic,
        technique_id=tid,
        technique_name=tname,
        name=name,
        description=f'Test ability: {name}',
        executors=[executor],
    )


def _make_link(ability, paw, status=0, cleanup=0, facts=None, idx=0):
    encoded = _encode(f'{ability.name} command')
    lnk = Link(command=encoded, plaintext_command=encoded, paw=paw,
                ability=ability, executor=ability.executors[0])
    lnk.pid = 1000 + idx
    base = datetime(2026, 3, 17, 8, 0, 0)
    lnk.decide = base + timedelta(minutes=idx * 2)
    lnk.collect = base + timedelta(minutes=idx * 2, seconds=30)
    lnk.finish = (base + timedelta(minutes=idx * 2 + 1)).strftime(BaseObject.TIME_FORMAT)
    lnk.status = status
    lnk.cleanup = cleanup
    if facts:
        lnk.facts.extend(facts)
    return lnk


def create_test_operation():
    """Build a multi-hop operation with lateral movement and P2P proxy."""

    # --- Agents across 3 subnets ---
    web01 = Agent(
        sleep_min=30, sleep_max=60, watchdog=0, platform='linux',
        host='web01', username='www-data', architecture='amd64', group='red',
        location='/tmp/sandcat', pid=100, ppid=1, executors=['sh'],
        privilege='User', exe_name='sandcat', contact='HTTP', paw='web01paw',
        host_ip_addrs=['10.0.1.5'],
    )

    # P2P proxy pivot agent — in DMZ but acts as proxy to Corporate
    proxy01 = Agent(
        sleep_min=30, sleep_max=60, watchdog=0, platform='linux',
        host='proxy01', username='root', architecture='amd64', group='red',
        location='/tmp/sandcat', pid=200, ppid=1, executors=['sh'],
        privilege='Elevated', exe_name='sandcat', contact='HTTP', paw='proxy01paw',
        host_ip_addrs=['10.0.1.10', '192.168.5.1'],  # dual-homed
    )

    dc01 = Agent(
        sleep_min=30, sleep_max=60, watchdog=0, platform='windows',
        host='DC01', username='CORP\\admin', architecture='amd64', group='red',
        location='C:\\Users\\admin\\sandcat.exe', pid=300, ppid=1, executors=['psh'],
        privilege='Elevated', exe_name='sandcat.exe', contact='HTTP', paw='dc01paw',
        host_ip_addrs=['192.168.5.10'],
    )

    db01 = Agent(
        sleep_min=30, sleep_max=60, watchdog=0, platform='linux',
        host='db01', username='postgres', architecture='amd64', group='red',
        location='/tmp/sandcat', pid=400, ppid=1, executors=['sh'],
        privilege='User', exe_name='sandcat', contact='HTTP', paw='db01paw',
        host_ip_addrs=['192.168.10.50'],
    )

    # Set origin_link_ids for lateral movement chain
    # web01 → (lat move) → proxy01 → (lat move) → dc01 → (lat move) → db01
    proxy01.origin_link_id = 'lat-link-1'
    dc01.origin_link_id = 'lat-link-2'
    db01.origin_link_id = 'lat-link-3'

    # --- Abilities ---
    recon = _make_ability('Network Scan', 'discovery', 'T1046', 'Network Service Discovery')
    enum_users = _make_ability('Enumerate Domain Users', 'discovery', 'T1087.002', 'Domain Account Discovery', 'windows')
    cred_dump = _make_ability('Dump LSASS', 'credential-access', 'T1003.001', 'LSASS Memory', 'windows')
    smb_move = _make_ability('SMB Lateral Movement', 'lateral-movement', 'T1021.002', 'SMB/Windows Admin Shares')
    p2p_proxy = _make_ability('Start P2P Proxy', 'command-and-control', 'T1090.001', 'Internal Proxy')
    whoami = _make_ability('Identify User', 'discovery', 'T1033', 'System Owner/User Discovery')
    privesc = _make_ability('Sudo Exploit', 'privilege-escalation', 'T1548.001', 'Setuid and Setgid')
    exfil = _make_ability('Exfiltrate Data', 'exfiltration', 'T1041', 'Exfiltration Over C2 Channel')
    persist = _make_ability('Install Cron Backdoor', 'persistence', 'T1053.003', 'Cron')
    find_files = _make_ability('Find Sensitive Files', 'collection', 'T1005', 'Data from Local System')
    db_dump = _make_ability('Dump Database', 'collection', 'T1213', 'Data from Information Repositories')

    # --- Facts discovered ---
    fact_remote_ip_1 = Fact(trait='remote.host.ip', value='10.0.1.20')  # discovered host in DMZ
    fact_remote_ip_2 = Fact(trait='remote.host.ip', value='192.168.5.25')  # discovered host in Corp
    fact_remote_ip_3 = Fact(trait='remote.host.ip', value='192.168.10.100')  # discovered host in Servers
    fact_cred = Fact(trait='domain.user.password', value='P@ssw0rd123')
    fact_user = Fact(trait='domain.user.name', value='CORP\\svc_admin')

    # --- Links (steps) across hosts ---
    links = [
        # web01: initial recon
        _make_link(whoami, 'web01paw', idx=0),
        _make_link(recon, 'web01paw', idx=1, facts=[fact_remote_ip_1]),
        _make_link(p2p_proxy, 'web01paw', idx=2),
        # Lateral move to proxy01
        _make_link(smb_move, 'web01paw', idx=3),  # lat-link-1
        # proxy01: pivot point
        _make_link(whoami, 'proxy01paw', idx=4),
        _make_link(privesc, 'proxy01paw', idx=5),
        _make_link(recon, 'proxy01paw', idx=6, facts=[fact_remote_ip_2]),
        # Lateral move to dc01
        _make_link(smb_move, 'proxy01paw', idx=7),  # lat-link-2
        # dc01: domain controller
        _make_link(whoami, 'dc01paw', idx=8),
        _make_link(enum_users, 'dc01paw', idx=9, facts=[fact_user]),
        _make_link(cred_dump, 'dc01paw', idx=10, facts=[fact_cred]),
        _make_link(recon, 'dc01paw', idx=11, facts=[fact_remote_ip_3]),
        # Lateral move to db01
        _make_link(smb_move, 'dc01paw', idx=12),  # lat-link-3
        # db01: database server
        _make_link(whoami, 'db01paw', idx=13),
        _make_link(find_files, 'db01paw', idx=14),
        _make_link(db_dump, 'db01paw', idx=15),
        _make_link(exfil, 'db01paw', idx=16),
        _make_link(persist, 'db01paw', idx=17),
        # Back on web01: cleanup
        _make_link(persist, 'web01paw', idx=18),
    ]

    # Set the lateral movement link IDs to match origin_link_id
    links[3].id = 'lat-link-1'  # web01 → proxy01
    links[7].id = 'lat-link-2'  # proxy01 → dc01
    links[12].id = 'lat-link-3'  # dc01 → db01

    adversary = Adversary(adversary_id='test-multihop', name='Multi-Hop Test',
                          description='Multi-hop lateral movement test', atomic_ordering=[])

    op = Operation(
        name='Red Team Multi-Hop Campaign',
        agents=[web01, proxy01, dc01, db01],
        adversary=adversary,
    )
    op.set_start_details()
    op.chain = links

    return op


if __name__ == '__main__':
    op = create_test_operation()
    print(f'Operation: {op.name}')
    print(f'Agents: {len(op.agents)}')
    print(f'Links: {len(op.chain)}')
    for agent in op.agents:
        print(f'  {agent.paw} | {agent.host} | {agent.platform} | IPs: {agent.host_ip_addrs} | origin: {agent.origin_link_id}')
    for link in op.chain:
        print(f'  [{link.id[:10]}] {link.paw} | {link.ability.name} ({link.ability.tactic})')
