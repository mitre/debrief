"""Exhaustive tests for app/debrief_svc.py — DebriefService."""
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from plugins.debrief.app.debrief_svc import DebriefService


# ---------------------------------------------------------------------------
# Helper builders (lightweight, no Caldera imports)
# ---------------------------------------------------------------------------
def _svc(mock_services):
    with patch.object(DebriefService, 'get_config', return_value={'app.name': 'caldera', 'app.port': '8888'}):
        svc = DebriefService(mock_services)
    return svc


# ===========================================================================
# generate_ttps — static method, no async
# ===========================================================================
class TestGenerateTtps:
    def test_empty_operations(self):
        assert DebriefService.generate_ttps([]) == {}

    def test_single_operation_single_link(self, sample_operation):
        ttps = DebriefService.generate_ttps([sample_operation])
        assert 'discovery' in ttps
        entry = ttps['discovery']
        assert entry['name'] == 'discovery'
        assert 'System Information Discovery' in entry['techniques']
        assert 'TestOp' in entry['steps']
        assert 'Test ability' in entry['steps']['TestOp']

    def test_cleanup_links_excluded(self, make_ability, make_link, make_operation):
        ab = make_ability(tactic='execution')
        link_clean = make_link(ability=ab, cleanup=1, unique='clean1')
        op = make_operation(chain=[link_clean])
        ttps = DebriefService.generate_ttps([op])
        assert ttps == {}

    def test_multiple_operations_merge(self, multi_op_operations):
        ttps = DebriefService.generate_ttps(multi_op_operations)
        assert 'discovery' in ttps
        assert 'collection' in ttps
        disc = ttps['discovery']
        assert 'Op1' in disc['steps']
        assert 'Op2' in disc['steps']

    def test_key_by_tid(self, sample_operation):
        ttps = DebriefService.generate_ttps([sample_operation], key_by_tid=True)
        entry = ttps['discovery']
        assert 'T1082' in entry['techniques']

    def test_sorted_output(self, multi_op_operations):
        ttps = DebriefService.generate_ttps(multi_op_operations)
        keys = list(ttps.keys())
        assert keys == sorted(keys)

    def test_duplicate_ability_not_repeated(self, make_ability, make_link, make_operation):
        ab = make_ability(tactic='discovery', name='Same ability')
        l1 = make_link(ability=ab, unique='u1')
        l2 = make_link(ability=ab, unique='u2')
        op = make_operation(chain=[l1, l2])
        ttps = DebriefService.generate_ttps([op])
        assert len(ttps['discovery']['steps']['TestOp']) == 1

    def test_multiple_techniques_same_tactic(self, make_ability, make_link, make_operation):
        ab1 = make_ability(tactic='discovery', technique_id='T1082', technique_name='SysInfo', name='A1')
        ab2 = make_ability(tactic='discovery', technique_id='T1016', technique_name='System Network Config', name='A2')
        l1 = make_link(ability=ab1, unique='u1')
        l2 = make_link(ability=ab2, unique='u2')
        op = make_operation(chain=[l1, l2])
        ttps = DebriefService.generate_ttps([op])
        assert len(ttps['discovery']['techniques']) == 2


# ===========================================================================
# _generate_new_tactic_entry / _update_tactic_entry — static helpers
# ===========================================================================
class TestTacticEntryHelpers:
    def test_generate_new_tactic_entry(self, sample_operation, sample_link):
        entry = DebriefService._generate_new_tactic_entry(
            sample_operation, 'discovery', sample_link)
        assert entry['name'] == 'discovery'
        assert 'System Information Discovery' in entry['techniques']
        assert entry['techniques']['System Information Discovery'] == 'T1082'

    def test_generate_new_tactic_entry_key_by_tid(self, sample_operation, sample_link):
        entry = DebriefService._generate_new_tactic_entry(
            sample_operation, 'discovery', sample_link, key_by_tid=True)
        assert 'T1082' in entry['techniques']

    def test_update_tactic_entry_new_technique(self, make_ability, make_link):
        entry = {'name': 'discovery', 'techniques': {'SysInfo': 'T1082'}, 'steps': {'Op': ['A1']}}
        ab = make_ability(technique_id='T1016', technique_name='NetConfig', name='A2')
        lnk = make_link(ability=ab)
        DebriefService._update_tactic_entry(entry, 'Op', lnk)
        assert 'NetConfig' in entry['techniques']
        assert 'A2' in entry['steps']['Op']

    def test_update_tactic_entry_new_op(self, sample_link):
        entry = {'name': 'discovery', 'techniques': {'SysInfo': 'T1082'}, 'steps': {'Op1': ['A1']}}
        DebriefService._update_tactic_entry(entry, 'Op2', sample_link)
        assert 'Op2' in entry['steps']

    def test_update_tactic_entry_tid_stripped_and_uppercased(self, make_ability, make_link):
        ab = make_ability(technique_id='  t1082  ', technique_name='SysInfo')
        lnk = make_link(ability=ab)
        entry = DebriefService._generate_new_tactic_entry(
            SimpleNamespace(name='Op'), 'discovery', lnk, key_by_tid=True)
        assert 'T1082' in entry['techniques']


# ===========================================================================
# _add_agents_to_d3 — static method
# ===========================================================================
class TestAddAgentsToD3:
    def test_adds_agent_node_and_link(self, sample_agent):
        id_store = {'c2': 0}
        graph = {'nodes': [], 'links': []}
        DebriefService._add_agents_to_d3([sample_agent], id_store, graph)
        assert len(graph['nodes']) == 1
        assert graph['nodes'][0]['type'] == 'agent'
        assert len(graph['links']) == 1
        assert graph['links'][0]['source'] == 0

    def test_no_duplicate_agents(self, sample_agent):
        id_store = {'c2': 0}
        graph = {'nodes': [], 'links': []}
        DebriefService._add_agents_to_d3([sample_agent, sample_agent], id_store, graph)
        assert len(graph['nodes']) == 1

    def test_multiple_agents(self, sample_agent, sample_agent_linux):
        id_store = {'c2': 0}
        graph = {'nodes': [], 'links': []}
        DebriefService._add_agents_to_d3([sample_agent, sample_agent_linux], id_store, graph)
        assert len(graph['nodes']) == 2
        assert len(graph['links']) == 2


# ===========================================================================
# _format_timestamp
# ===========================================================================
class TestFormatTimestamp:
    def test_replaces_space_with_t(self):
        assert DebriefService._format_timestamp('2021-01-01 08:00:00') == '2021-01-01T08:00:00'

    def test_already_formatted(self):
        assert DebriefService._format_timestamp('2021-01-01T08:00:00') == '2021-01-01T08:00:00'


# ===========================================================================
# _get_by_prop_order
# ===========================================================================
class TestGetByPropOrder:
    def test_single_link(self, sample_link):
        result = DebriefService._get_by_prop_order([sample_link], 'tactic')
        assert len(result) == 1
        assert result[0][0] == 'discovery'
        assert result[0][1] == [sample_link]

    def test_two_different_tactics(self, two_op_chain):
        result = DebriefService._get_by_prop_order(two_op_chain, 'tactic')
        assert len(result) == 2
        assert result[0][0] == 'discovery'
        assert result[1][0] == 'collection'

    def test_same_tactic_grouped(self, make_ability, make_link):
        ab1 = make_ability(tactic='discovery', name='A1')
        ab2 = make_ability(tactic='discovery', name='A2')
        l1 = make_link(ability=ab1, unique='u1', cleanup=0)
        l2 = make_link(ability=ab2, unique='u2', cleanup=0)
        result = DebriefService._get_by_prop_order([l1, l2], 'tactic')
        assert len(result) == 1
        assert len(result[0][1]) == 2

    def test_prop_technique_name(self, two_op_chain):
        result = DebriefService._get_by_prop_order(two_op_chain, 'technique_name')
        assert len(result) == 2


# ===========================================================================
# _link_nontargeted_facts
# ===========================================================================
class TestLinkNontargetedFacts:
    def test_untargeted_fact_gets_link(self):
        nodes = [{'id': 10, 'name': 'fact1'}, {'id': 11, 'name': 'fact2'}]
        links = [{'source': 1, 'target': 10, 'type': 'relationship'}]
        DebriefService._link_nontargeted_facts(nodes, links, op_id=1)
        assert len(links) == 2
        assert links[1]['target'] == 11
        assert links[1]['source'] == 1

    def test_all_targeted_no_extra_links(self):
        nodes = [{'id': 10, 'name': 'fact1'}]
        links = [{'source': 1, 'target': 10, 'type': 'relationship'}]
        DebriefService._link_nontargeted_facts(nodes, links, op_id=1)
        assert len(links) == 1


# ===========================================================================
# build_steps_d3 — async
# ===========================================================================
class TestBuildStepsD3:
    @pytest.mark.asyncio
    async def test_empty_operations(self, mock_services):
        svc = _svc(mock_services)
        mock_services['data_svc'].locate.return_value = []
        result = await svc.build_steps_d3([])
        assert result['nodes'][0]['type'] == 'c2'
        assert len(result['links']) == 0

    @pytest.mark.asyncio
    async def test_single_operation(self, mock_services, sample_operation):
        svc = _svc(mock_services)
        mock_services['data_svc'].locate.return_value = [sample_operation]
        result = await svc.build_steps_d3(['op-1'])
        node_types = [n['type'] for n in result['nodes']]
        assert 'c2' in node_types
        assert 'agent' in node_types
        assert 'link' in node_types

    @pytest.mark.asyncio
    async def test_cleanup_link_labeled(self, mock_services, make_ability, make_link, make_operation):
        svc = _svc(mock_services)
        ab = make_ability(name='DoClean')
        lnk = make_link(ability=ab, cleanup=1, unique='cl1')
        op = make_operation(chain=[lnk])
        mock_services['data_svc'].locate.return_value = [op]
        result = await svc.build_steps_d3(['op-1'])
        link_nodes = [n for n in result['nodes'] if n['type'] == 'link']
        assert any('(cleanup)' in n['attrs']['name'] for n in link_nodes)

    @pytest.mark.asyncio
    async def test_multiple_links_chained(self, mock_services, make_operation, two_op_chain):
        svc = _svc(mock_services)
        op = make_operation(chain=two_op_chain)
        mock_services['data_svc'].locate.return_value = [op]
        result = await svc.build_steps_d3(['op-1'])
        next_links = [l for l in result['links'] if l['type'] == 'next_link']
        assert len(next_links) >= 2


# ===========================================================================
# build_tactic_d3 / build_technique_d3 — async
# ===========================================================================
class TestBuildTacticAndTechniqueD3:
    @pytest.mark.asyncio
    async def test_tactic_d3(self, mock_services, sample_operation):
        svc = _svc(mock_services)
        mock_services['data_svc'].locate.return_value = [sample_operation]
        result = await svc.build_tactic_d3(['op-1'])
        tactic_nodes = [n for n in result['nodes'] if n['type'] == 'tactic']
        assert len(tactic_nodes) >= 1

    @pytest.mark.asyncio
    async def test_technique_d3(self, mock_services, sample_operation):
        svc = _svc(mock_services)
        mock_services['data_svc'].locate.return_value = [sample_operation]
        result = await svc.build_technique_d3(['op-1'])
        technique_nodes = [n for n in result['nodes'] if n['type'] == 'technique_name']
        assert len(technique_nodes) >= 1

    @pytest.mark.asyncio
    async def test_empty_chain(self, mock_services, make_operation):
        svc = _svc(mock_services)
        op = make_operation(chain=[])
        mock_services['data_svc'].locate.return_value = [op]
        result = await svc.build_tactic_d3(['op-1'])
        # Only operation node, no tactic nodes
        assert len([n for n in result['nodes'] if n['type'] == 'tactic']) == 0


# ===========================================================================
# build_fact_d3 — async
# ===========================================================================
class TestBuildFactD3:
    @pytest.mark.asyncio
    async def test_fact_graph_with_facts(self, mock_services, make_operation, make_fact, make_source):
        svc = _svc(mock_services)
        f1 = make_fact(trait='host.user', value='admin', unique='f1')
        src = make_source(facts=[f1])
        op = make_operation(facts=[f1], source=src)
        mock_services['data_svc'].locate.return_value = [op]
        result = await svc.build_fact_d3(['op-1'])
        fact_nodes = [n for n in result['nodes'] if n['type'] == 'fact']
        assert len(fact_nodes) == 1

    @pytest.mark.asyncio
    async def test_fact_graph_no_facts(self, mock_services, make_operation):
        svc = _svc(mock_services)
        op = make_operation(facts=[], relationships=[])
        mock_services['data_svc'].locate.return_value = [op]
        result = await svc.build_fact_d3(['op-1'])
        fact_nodes = [n for n in result['nodes'] if n['type'] == 'fact']
        assert len(fact_nodes) == 0

    @pytest.mark.asyncio
    async def test_fact_relationship_links(self, mock_services, make_operation, make_fact, make_source):
        svc = _svc(mock_services)
        f1 = make_fact(trait='host.user', value='admin', unique='f1')
        f2 = make_fact(trait='host.password', value='pass', unique='f2')
        rel = SimpleNamespace(edge='has_password', source=f1, target=f2)
        src = make_source(facts=[f1])
        op = make_operation(facts=[f1, f2], relationships=[rel], source=src)
        mock_services['data_svc'].locate.return_value = [op]
        result = await svc.build_fact_d3(['op-1'])
        rel_links = [l for l in result['links'] if l['type'] == 'relationship']
        assert len(rel_links) >= 1


# ===========================================================================
# build_attackpath_d3 — async
# ===========================================================================
class TestBuildAttackpathD3:
    @pytest.mark.asyncio
    async def test_empty_operations(self, mock_services):
        svc = _svc(mock_services)
        mock_services['data_svc'].locate.return_value = []
        result = await svc.build_attackpath_d3([])
        assert result['nodes'][0]['type'] == 'c2'

    @pytest.mark.asyncio
    async def test_agent_with_origin_link(self, mock_services, make_operation, make_agent, make_link, make_ability):
        svc = _svc(mock_services)
        ab = make_ability(tactic='lateral-movement', technique_id='T1021',
                          technique_name='Remote Services')
        # link paw must match parent_agent.paw, and agent.unique used as id_store key
        parent_agent = make_agent(paw='paw1', unique='paw1')
        lnk = make_link(paw='paw1', ability=ab, unique='origin-lnk', link_id='origin-lnk')
        spawned_agent = make_agent(paw='paw2', unique='paw2', origin_link_id='origin-lnk')
        op = make_operation(agents=[parent_agent, spawned_agent], chain=[lnk])
        mock_services['data_svc'].locate.return_value = [op]
        mock_services['app_svc'].find_op_with_link.return_value = op
        result = await svc.build_attackpath_d3(['op-1'])
        link_nodes = [n for n in result['nodes'] if n['type'] == 'link']
        assert len(link_nodes) >= 1


# ===========================================================================
# _get_pub_attrs — static
# ===========================================================================
class TestGetPubAttrs:
    def test_filters_private_attrs(self, make_fact):
        f = make_fact()
        # add a private attr
        f._private = 'hidden'
        result = DebriefService._get_pub_attrs(f)
        assert '_private' not in result
        assert 'trait' in result

    def test_origin_type_name(self, make_fact):
        f = make_fact()
        result = DebriefService._get_pub_attrs(f)
        assert result['origin_type'] == 'LEARNED'
