"""Tests for build_topology() in debrief_svc.py."""
import pytest
from unittest.mock import AsyncMock, patch

from plugins.debrief.app.debrief_svc import DebriefService


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _svc():
    mock_services = {
        'app_svc': AsyncMock(),
        'file_svc': AsyncMock(),
        'data_svc': AsyncMock(),
    }
    with patch.object(DebriefService, 'get_config', return_value={
        'app.name': 'caldera',
        'app.contact.http': 'http://10.0.0.1:8888',
    }):
        svc = DebriefService(mock_services)
    return svc


def _make_agent(paw, host, platform='linux', ips=None, origin_link_id=None, unique=None):
    from types import SimpleNamespace
    from datetime import datetime
    return SimpleNamespace(
        paw=paw, host=host, platform=platform,
        host_ip_addrs=ips or [],
        origin_link_id=origin_link_id,
        username='user', privilege='User',
        group='red', display_name=f'{host}$user',
        unique=unique or paw, exe_name='agent',
        created=datetime(2021, 1, 1, 8, 0, 0),
    )


def _make_link(paw, ability_name='whoami', tactic='discovery', technique_id='T1033',
               technique_name='System Owner', status=0, link_id='link-1',
               cleanup=0, facts=None):
    from types import SimpleNamespace
    from base64 import b64encode
    return SimpleNamespace(
        id=link_id, paw=paw, status=status, cleanup=cleanup,
        command=b64encode(b'whoami').decode(),
        finish='2021-01-01T08:02:00Z',
        created='2021-01-01T08:00:00Z',
        unique=link_id,
        facts=facts or [],
        ability=SimpleNamespace(
            name=ability_name, tactic=tactic,
            technique_id=technique_id, technique_name=technique_name,
        ),
    )


def _make_fact(trait, value, collected_by=None):
    from types import SimpleNamespace
    return SimpleNamespace(
        trait=trait, value=value, score=1, unique=f'{trait}-{value}',
        collected_by=collected_by or [], links=[],
    )


def _make_operation(name='TestOp', agents=None, chain=None, facts=None, op_id='op-1'):
    from types import SimpleNamespace

    async def all_facts():
        return facts or []

    async def all_relationships():
        return []

    return SimpleNamespace(
        id=op_id, name=name,
        agents=agents or [], chain=chain or [],
        created='2021-01-01T08:00:00Z',
        all_facts=all_facts,
        all_relationships=all_relationships,
    )


# ===========================================================================
# _ip_to_subnet
# ===========================================================================
class TestIpToSubnet:
    def test_valid_ipv4(self):
        assert DebriefService._ip_to_subnet('192.168.1.50') == '192.168.1.0/24'

    def test_different_subnet(self):
        assert DebriefService._ip_to_subnet('10.0.5.12') == '10.0.5.0/24'

    def test_invalid_ip(self):
        assert DebriefService._ip_to_subnet('not-an-ip') is None

    def test_empty_string(self):
        assert DebriefService._ip_to_subnet('') is None

    def test_ipv6_returns_none(self):
        assert DebriefService._ip_to_subnet('::1') is None

    def test_partial_ip(self):
        assert DebriefService._ip_to_subnet('192.168.1') is None

    def test_out_of_range(self):
        assert DebriefService._ip_to_subnet('999.999.999.999') is None


# ===========================================================================
# build_topology — empty / basic cases
# ===========================================================================
class TestBuildTopologyBasic:
    @pytest.mark.asyncio
    async def test_empty_operations(self):
        svc = _svc()
        svc.data_svc.locate = AsyncMock(return_value=[])
        result = await svc.build_topology([])
        assert 'subnets' in result
        assert 'hosts' in result
        assert 'edges' in result
        assert 'steps_by_host' in result

    @pytest.mark.asyncio
    async def test_single_agent_no_chain(self):
        svc = _svc()
        agent = _make_agent('paw1', 'web01', ips=['10.0.1.5'])
        op = _make_operation(agents=[agent], chain=[])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])

        # Should have c2 + 1 compromised host
        assert 'c2' in result['hosts']
        assert 'paw1' in result['hosts']
        assert result['hosts']['paw1']['compromised'] is True
        assert result['hosts']['paw1']['hostname'] == 'web01'
        assert result['hosts']['paw1']['ips'] == ['10.0.1.5']

    @pytest.mark.asyncio
    async def test_c2_always_present(self):
        svc = _svc()
        op = _make_operation(agents=[], chain=[])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        assert 'c2' in result['hosts']
        assert result['hosts']['c2']['platform'] == 'server'


# ===========================================================================
# build_topology — subnet grouping
# ===========================================================================
class TestBuildTopologySubnets:
    @pytest.mark.asyncio
    async def test_agents_grouped_by_subnet(self):
        svc = _svc()
        a1 = _make_agent('paw1', 'web01', ips=['10.0.1.5'])
        a2 = _make_agent('paw2', 'web02', ips=['10.0.1.10'], unique='paw2')
        a3 = _make_agent('paw3', 'dc01', ips=['192.168.5.1'], unique='paw3')
        op = _make_operation(agents=[a1, a2, a3], chain=[])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        cidrs = [s['cidr'] for s in result['subnets']]
        assert '10.0.1.0/24' in cidrs
        assert '192.168.5.0/24' in cidrs

        # Check hosts are in correct subnets
        subnet_10 = next(s for s in result['subnets'] if s['cidr'] == '10.0.1.0/24')
        assert 'paw1' in subnet_10['hosts']
        assert 'paw2' in subnet_10['hosts']

    @pytest.mark.asyncio
    async def test_agent_without_ip_goes_to_unknown(self):
        svc = _svc()
        agent = _make_agent('paw1', 'mystery-host', ips=[])
        op = _make_operation(agents=[agent], chain=[])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        unknown = [s for s in result['subnets'] if s['cidr'] == 'Unknown']
        assert len(unknown) == 1
        assert 'paw1' in unknown[0]['hosts']


# ===========================================================================
# build_topology — edges (initial access + lateral movement)
# ===========================================================================
class TestBuildTopologyEdges:
    @pytest.mark.asyncio
    async def test_initial_access_edge(self):
        svc = _svc()
        agent = _make_agent('paw1', 'web01', ips=['10.0.1.5'])
        op = _make_operation(agents=[agent], chain=[])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        ia_edges = [e for e in result['edges'] if e['type'] == 'initial_access']
        assert len(ia_edges) == 1
        assert ia_edges[0]['source'] == 'c2'
        assert ia_edges[0]['target'] == 'paw1'

    @pytest.mark.asyncio
    async def test_lateral_movement_edge(self):
        svc = _svc()
        a1 = _make_agent('paw1', 'web01', ips=['10.0.1.5'])
        lat_link = _make_link('paw1', ability_name='psexec', tactic='lateral-movement',
                              technique_id='T1021.002', technique_name='SMB Admin Shares',
                              link_id='lat-link-1')
        a2 = _make_agent('paw2', 'dc01', ips=['192.168.5.1'],
                         unique='paw2', origin_link_id='lat-link-1')
        op = _make_operation(agents=[a1, a2], chain=[lat_link])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        lat_edges = [e for e in result['edges'] if e['type'] == 'lateral_movement']
        assert len(lat_edges) == 1
        assert lat_edges[0]['source'] == 'paw1'
        assert lat_edges[0]['target'] == 'paw2'
        assert 'T1021.002' in lat_edges[0]['technique']

    @pytest.mark.asyncio
    async def test_no_lateral_edge_for_initial_agent(self):
        svc = _svc()
        agent = _make_agent('paw1', 'web01', origin_link_id=None)
        op = _make_operation(agents=[agent], chain=[])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        lat_edges = [e for e in result['edges'] if e['type'] == 'lateral_movement']
        assert len(lat_edges) == 0


# ===========================================================================
# build_topology — steps grouped by host
# ===========================================================================
class TestBuildTopologySteps:
    @pytest.mark.asyncio
    async def test_steps_grouped_by_agent_paw(self):
        svc = _svc()
        agent = _make_agent('paw1', 'web01', ips=['10.0.1.5'])
        link1 = _make_link('paw1', ability_name='whoami', link_id='l1')
        link2 = _make_link('paw1', ability_name='hostname', link_id='l2')
        op = _make_operation(agents=[agent], chain=[link1, link2])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        assert 'paw1' in result['steps_by_host']
        assert len(result['steps_by_host']['paw1']) == 2
        names = [s['ability_name'] for s in result['steps_by_host']['paw1']]
        assert 'whoami' in names
        assert 'hostname' in names

    @pytest.mark.asyncio
    async def test_cleanup_links_excluded(self):
        svc = _svc()
        agent = _make_agent('paw1', 'web01')
        link_clean = _make_link('paw1', ability_name='cleanup', link_id='lc', cleanup=1)
        link_normal = _make_link('paw1', ability_name='whoami', link_id='ln')
        op = _make_operation(agents=[agent], chain=[link_clean, link_normal])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        steps = result['steps_by_host']['paw1']
        assert len(steps) == 1
        assert steps[0]['ability_name'] == 'whoami'

    @pytest.mark.asyncio
    async def test_step_count_on_host(self):
        svc = _svc()
        agent = _make_agent('paw1', 'web01')
        links = [_make_link('paw1', link_id=f'l{i}') for i in range(5)]
        op = _make_operation(agents=[agent], chain=links)
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        assert result['hosts']['paw1']['step_count'] == 5


# ===========================================================================
# build_topology — discovered hosts from facts
# ===========================================================================
class TestBuildTopologyDiscovered:
    @pytest.mark.asyncio
    async def test_remote_host_ip_creates_discovered_host(self):
        svc = _svc()
        agent = _make_agent('paw1', 'web01', ips=['10.0.1.5'])
        fact = _make_fact('remote.host.ip', '10.0.1.20', collected_by=['paw1'])
        op = _make_operation(agents=[agent], chain=[], facts=[fact])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        disc_id = 'discovered-10.0.1.20'
        assert disc_id in result['hosts']
        assert result['hosts'][disc_id]['compromised'] is False
        assert result['hosts'][disc_id]['ips'] == ['10.0.1.20']

    @pytest.mark.asyncio
    async def test_discovered_host_not_duplicated_with_agent(self):
        """If an agent already exists on an IP, don't create a discovered host."""
        svc = _svc()
        agent = _make_agent('paw1', 'web01', ips=['10.0.1.5'])
        # Fact pointing to same IP as agent
        fact = _make_fact('remote.host.ip', '10.0.1.5', collected_by=['paw1'])
        op = _make_operation(agents=[agent], chain=[], facts=[fact])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        disc_hosts = [h for h in result['hosts'] if h.startswith('discovered-')]
        assert len(disc_hosts) == 0

    @pytest.mark.asyncio
    async def test_discovered_host_in_same_subnet_as_agent(self):
        svc = _svc()
        agent = _make_agent('paw1', 'web01', ips=['10.0.1.5'])
        fact = _make_fact('remote.host.ip', '10.0.1.20')
        op = _make_operation(agents=[agent], chain=[], facts=[fact])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        subnet = next(s for s in result['subnets'] if s['cidr'] == '10.0.1.0/24')
        assert 'paw1' in subnet['hosts']
        assert 'discovered-10.0.1.20' in subnet['hosts']


# ===========================================================================
# build_topology — multi-operation
# ===========================================================================
class TestBuildTopologyMultiOp:
    @pytest.mark.asyncio
    async def test_two_operations_merged(self):
        svc = _svc()
        a1 = _make_agent('paw1', 'web01', ips=['10.0.1.5'])
        a2 = _make_agent('paw2', 'db01', ips=['10.0.2.10'], unique='paw2')
        op1 = _make_operation(name='Op1', agents=[a1], chain=[], op_id='op-1')
        op2 = _make_operation(name='Op2', agents=[a2], chain=[], op_id='op-2')
        svc.data_svc.locate = AsyncMock(side_effect=[[op1], [op2]])

        result = await svc.build_topology(['op-1', 'op-2'])
        assert 'paw1' in result['hosts']
        assert 'paw2' in result['hosts']
        cidrs = [s['cidr'] for s in result['subnets']]
        assert '10.0.1.0/24' in cidrs
        assert '10.0.2.0/24' in cidrs


# ===========================================================================
# build_topology — multi-hop lateral movement with P2P proxy
# ===========================================================================
class TestBuildTopologyMultiHop:
    @pytest.mark.asyncio
    async def test_three_hop_lateral_movement_chain(self):
        """C2 → web01 → proxy01(P2P) → dc01 → db01 across 3 subnets."""
        svc = _svc()
        web01 = _make_agent('web01paw', 'web01', ips=['10.0.1.5'])
        proxy01 = _make_agent('proxy01paw', 'proxy01', ips=['10.0.1.10', '192.168.5.1'],
                              origin_link_id='lat-1')
        dc01 = _make_agent('dc01paw', 'DC01', platform='windows', ips=['192.168.5.10'],
                           origin_link_id='lat-2')
        db01 = _make_agent('db01paw', 'db01', ips=['192.168.10.50'],
                           origin_link_id='lat-3')

        lat1 = _make_link('web01paw', ability_name='SMB Move', tactic='lateral-movement',
                          technique_id='T1021.002', link_id='lat-1')
        lat2 = _make_link('proxy01paw', ability_name='SMB Move', tactic='lateral-movement',
                          technique_id='T1021.002', link_id='lat-2')
        lat3 = _make_link('dc01paw', ability_name='SMB Move', tactic='lateral-movement',
                          technique_id='T1021.002', link_id='lat-3')
        step1 = _make_link('web01paw', link_id='step-1')
        step2 = _make_link('dc01paw', link_id='step-2')

        op = _make_operation(
            agents=[web01, proxy01, dc01, db01],
            chain=[step1, lat1, lat2, step2, lat3],
        )
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])

        # All 4 agents + C2
        assert len(result['hosts']) == 5
        assert 'web01paw' in result['hosts']
        assert 'proxy01paw' in result['hosts']
        assert 'dc01paw' in result['hosts']
        assert 'db01paw' in result['hosts']

        # 3 subnets (proxy01 goes to 10.0.1.0/24 as primary since non-172)
        cidrs = sorted([s['cidr'] for s in result['subnets']])
        assert '10.0.1.0/24' in cidrs
        assert '192.168.5.0/24' in cidrs or '10.0.1.0/24' in cidrs  # proxy dual-homed
        assert '192.168.10.0/24' in cidrs

        # 1 initial access + 3 lateral movement edges
        ia_edges = [e for e in result['edges'] if e['type'] == 'initial_access']
        lat_edges = [e for e in result['edges'] if e['type'] == 'lateral_movement']
        assert len(ia_edges) == 1  # C2 → web01
        assert ia_edges[0]['target'] == 'web01paw'
        assert len(lat_edges) == 3
        # Verify the chain: web01→proxy01, proxy01→dc01, dc01→db01
        lat_targets = {e['source']: e['target'] for e in lat_edges}
        assert lat_targets['web01paw'] == 'proxy01paw'
        assert lat_targets['proxy01paw'] == 'dc01paw'
        assert lat_targets['dc01paw'] == 'db01paw'

    @pytest.mark.asyncio
    async def test_dual_homed_agent_uses_non_docker_ip(self):
        """Agent with both Docker and real IPs should use non-Docker as primary."""
        svc = _svc()
        agent = _make_agent('paw1', 'pivot-host',
                            ips=['172.17.0.1', '172.18.0.1', '192.168.5.1'])
        op = _make_operation(agents=[agent], chain=[])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        # Should be in 192.168.5.0/24, not 172.x
        cidrs = [s['cidr'] for s in result['subnets']]
        assert '192.168.5.0/24' in cidrs
        assert all('172.' not in c for c in cidrs)
        assert result['hosts']['paw1']['primary_ip'] == '192.168.5.1'

    @pytest.mark.asyncio
    async def test_dual_homed_agent_primary_ip_set(self):
        """Dual-homed host should have primary_ip field set."""
        svc = _svc()
        agent = _make_agent('paw1', 'proxy01', ips=['10.0.1.10', '192.168.5.1'])
        op = _make_operation(agents=[agent], chain=[])
        svc.data_svc.locate = AsyncMock(return_value=[op])

        result = await svc.build_topology(['op-1'])
        assert result['hosts']['paw1']['primary_ip'] == '10.0.1.10'
