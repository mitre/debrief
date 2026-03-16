"""Tests for ALL debrief report section modules in app/debrief-sections/."""
import pytest
import importlib
from unittest.mock import patch, MagicMock, AsyncMock
from types import SimpleNamespace

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.flowables import KeepTogetherSplitAtTop

# Import section modules
agents_mod = importlib.import_module('plugins.debrief.app.debrief-sections.agents')
attackpath_mod = importlib.import_module('plugins.debrief.app.debrief-sections.attackpath_graph')
fact_graph_mod = importlib.import_module('plugins.debrief.app.debrief-sections.fact_graph')
facts_table_mod = importlib.import_module('plugins.debrief.app.debrief-sections.facts_table')
main_summary_mod = importlib.import_module('plugins.debrief.app.debrief-sections.main_summary')
statistics_mod = importlib.import_module('plugins.debrief.app.debrief-sections.statistics')
steps_graph_mod = importlib.import_module('plugins.debrief.app.debrief-sections.steps_graph')
steps_table_mod = importlib.import_module('plugins.debrief.app.debrief-sections.steps_table')
tactic_graph_mod = importlib.import_module('plugins.debrief.app.debrief-sections.tactic_graph')
tactic_technique_mod = importlib.import_module('plugins.debrief.app.debrief-sections.tactic_technique_table')
technique_graph_mod = importlib.import_module('plugins.debrief.app.debrief-sections.technique_graph')


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def styles():
    return getSampleStyleSheet()


def _mock_section(module):
    with patch('plugins.debrief.app.utility.base_report_section.get_attack18') as mock_a18:
        mock_a18.return_value = MagicMock(
            get_strategies=MagicMock(return_value=[]),
            get_analytics=MagicMock(return_value=[]),
            get_parent_strategies=MagicMock(return_value=[]),
            get_parent_analytics=MagicMock(return_value=[]),
            strategies_by_tid={},
            analytics_by_tid={},
            techniques_by_id={},
        )
        section = module.DebriefReportSection()
    return section


# ===========================================================================
# Agents Section
# ===========================================================================
class TestAgentsSection:
    def test_fields(self):
        section = _mock_section(agents_mod)
        assert section.id == 'agents'
        assert section.display_name == 'Agents'

    @pytest.mark.asyncio
    async def test_generate_with_agents(self, styles, make_agent):
        section = _mock_section(agents_mod)
        agents = [make_agent(paw='p1'), make_agent(paw='p2', unique='a2')]
        result = await section.generate_section_elements(styles, agents=agents)
        assert len(result) == 2  # title+desc, table

    @pytest.mark.asyncio
    async def test_generate_no_agents(self, styles):
        section = _mock_section(agents_mod)
        result = await section.generate_section_elements(styles)
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_empty_agents(self, styles):
        section = _mock_section(agents_mod)
        result = await section.generate_section_elements(styles, agents=[])
        # 'agents' key IS in kwargs even if empty, so section header + table still generated
        assert len(result) == 2


# ===========================================================================
# Attack Path Graph Section
# ===========================================================================
class TestAttackpathGraphSection:
    def test_fields(self):
        section = _mock_section(attackpath_mod)
        assert section.id == 'attackpath-graph'

    @pytest.mark.asyncio
    async def test_generate_no_graph(self, styles):
        section = _mock_section(attackpath_mod)
        result = await section.generate_section_elements(styles, graph_files={})
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_with_graph(self, styles, tmp_path):
        section = _mock_section(attackpath_mod)
        with patch.object(section, 'generate_grouped_graph_section_flowables',
                          return_value=MagicMock()) as mock_gen:
            result = await section.generate_section_elements(
                styles, graph_files={'attackpath': '/fake/path.svg'})
            assert len(result) == 1
            mock_gen.assert_called_once()


# ===========================================================================
# Fact Graph Section
# ===========================================================================
class TestFactGraphSection:
    def test_fields(self):
        section = _mock_section(fact_graph_mod)
        assert section.id == 'fact-graph'

    @pytest.mark.asyncio
    async def test_generate_no_graph(self, styles):
        section = _mock_section(fact_graph_mod)
        result = await section.generate_section_elements(styles, graph_files={})
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_with_graph(self, styles):
        section = _mock_section(fact_graph_mod)
        with patch.object(section, 'generate_grouped_graph_section_flowables',
                          return_value=MagicMock()):
            result = await section.generate_section_elements(
                styles, graph_files={'fact': '/fake/fact.svg'})
            assert len(result) == 1


# ===========================================================================
# Facts Table Section
# ===========================================================================
class TestFactsTableSection:
    def test_fields(self):
        section = _mock_section(facts_table_mod)
        assert section.id == 'facts-table'

    @pytest.mark.asyncio
    async def test_generate_no_operations(self, styles):
        section = _mock_section(facts_table_mod)
        result = await section.generate_section_elements(styles)
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_with_operation(self, styles, make_operation, make_fact):
        section = _mock_section(facts_table_mod)
        f1 = make_fact(trait='host.user', value='admin')
        op = make_operation(facts=[f1])
        with patch.object(section, 'generate_table', return_value=MagicMock()):
            result = await section.generate_section_elements(styles, operations=[op])
            assert len(result) >= 2  # title + table per operation

    @pytest.mark.asyncio
    async def test_generate_multiple_operations(self, styles, make_operation, make_fact):
        section = _mock_section(facts_table_mod)
        f1 = make_fact(trait='t1', value='v1')
        op1 = make_operation(name='Op1', op_id='o1', facts=[f1])
        op2 = make_operation(name='Op2', op_id='o2', facts=[])
        with patch.object(section, 'generate_table', return_value=MagicMock()):
            result = await section.generate_section_elements(styles, operations=[op1, op2])
            assert len(result) >= 4  # title + table for each


class TestFactsTableHelpers:
    def test_origin_name_enum(self):
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        section = _mock_section(facts_table_mod)
        fact = SimpleNamespace(origin_type=OT.LEARNED)
        assert section._origin_name(fact) == 'LEARNED'

    def test_origin_name_none(self):
        section = _mock_section(facts_table_mod)
        fact = SimpleNamespace(origin_type=None)
        assert section._origin_name(fact) is None

    def test_generate_fact_table_cmd_no_links(self):
        section = _mock_section(facts_table_mod)
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        fact = SimpleNamespace(origin_type=OT.LEARNED, links=[])
        result = section._generate_fact_table_cmd(fact, {})
        assert 'No Command' in result

    def test_generate_fact_table_cmd_with_link(self, make_link):
        section = _mock_section(facts_table_mod)
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        lnk = make_link(command='whoami')
        lnk.decode_bytes = lambda c: c
        fact = SimpleNamespace(origin_type=OT.LEARNED, links=['lnk1'])
        result = section._generate_fact_table_cmd(fact, {'lnk1': lnk})
        assert 'whoami' in result

    def test_value_truncation(self):
        section = _mock_section(facts_table_mod)
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        long_val = 'x' * 2000
        fact = SimpleNamespace(
            trait='t', value=long_val, score=1, origin_type=OT.LEARNED,
            source='src', links=[], collected_by=[])
        row = section._generate_fact_table_row(
            fact, False, {}, 'src', set(), set())
        assert len(row[1]) < len(long_val), "Long values should be truncated"


# ===========================================================================
# Main Summary Section
# ===========================================================================
class TestMainSummarySection:
    def test_fields(self):
        section = _mock_section(main_summary_mod)
        assert section.id == 'main-summary'
        assert section.display_name == 'Main Summary'

    @pytest.mark.asyncio
    async def test_generate_returns_flowables(self, styles):
        section = _mock_section(main_summary_mod)
        result = await section.generate_section_elements(styles)
        assert len(result) == 1
        assert isinstance(result[0], KeepTogetherSplitAtTop)


# ===========================================================================
# Statistics Section
# ===========================================================================
class TestStatisticsSection:
    def test_fields(self):
        section = _mock_section(statistics_mod)
        assert section.id == 'statistics'

    @pytest.mark.asyncio
    async def test_generate_no_operations(self, styles):
        section = _mock_section(statistics_mod)
        result = await section.generate_section_elements(styles)
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_with_operation(self, styles, make_operation):
        section = _mock_section(statistics_mod)
        op = make_operation()
        with patch.object(section, 'generate_table', return_value=MagicMock()):
            result = await section.generate_section_elements(styles, operations=[op])
            assert len(result) >= 2  # title+desc, table

    @pytest.mark.asyncio
    async def test_unfinished_operation(self, styles, make_operation):
        section = _mock_section(statistics_mod)
        op = make_operation(finish=None)
        with patch.object(section, 'generate_table', return_value=MagicMock()):
            result = await section.generate_section_elements(styles, operations=[op])
            assert len(result) >= 2


# ===========================================================================
# Steps Graph Section
# ===========================================================================
class TestStepsGraphSection:
    def test_fields(self):
        section = _mock_section(steps_graph_mod)
        assert section.id == 'steps-graph'

    @pytest.mark.asyncio
    async def test_generate_no_graph(self, styles):
        section = _mock_section(steps_graph_mod)
        result = await section.generate_section_elements(styles, graph_files={})
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_with_graph(self, styles):
        section = _mock_section(steps_graph_mod)
        with patch.object(section, 'generate_grouped_graph_section_flowables',
                          return_value=MagicMock()):
            result = await section.generate_section_elements(
                styles, graph_files={'steps': '/fake/steps.svg'})
            assert len(result) == 1


# ===========================================================================
# Steps Table Section
# ===========================================================================
class TestStepsTableSection:
    def test_fields(self):
        section = _mock_section(steps_table_mod)
        assert section.id == 'steps-table'

    @pytest.mark.asyncio
    async def test_generate_no_operations(self, styles):
        section = _mock_section(steps_table_mod)
        result = await section.generate_section_elements(styles)
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_with_operation(self, styles, make_operation, make_link, make_ability):
        section = _mock_section(steps_table_mod)
        ab = make_ability()
        lnk = make_link(ability=ab, facts=[SimpleNamespace(score=2)])
        op = make_operation(chain=[lnk])
        with patch.object(section, 'generate_table', return_value=MagicMock()):
            result = await section.generate_section_elements(styles, operations=[op])
            assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_step_with_no_facts(self, styles, make_operation, make_link):
        section = _mock_section(steps_table_mod)
        lnk = make_link(facts=[])
        op = make_operation(chain=[lnk])
        with patch.object(section, 'generate_table', return_value=MagicMock()):
            result = await section.generate_section_elements(styles, operations=[op])
            assert len(result) >= 2


# ===========================================================================
# Tactic Graph Section
# ===========================================================================
class TestTacticGraphSection:
    def test_fields(self):
        section = _mock_section(tactic_graph_mod)
        assert section.id == 'tactic-graph'

    @pytest.mark.asyncio
    async def test_generate_no_graph(self, styles):
        section = _mock_section(tactic_graph_mod)
        result = await section.generate_section_elements(styles, graph_files={})
        assert result == []


# ===========================================================================
# Technique Graph Section
# ===========================================================================
class TestTechniqueGraphSection:
    def test_fields(self):
        section = _mock_section(technique_graph_mod)
        assert section.id == 'technique-graph'

    @pytest.mark.asyncio
    async def test_generate_no_graph(self, styles):
        section = _mock_section(technique_graph_mod)
        result = await section.generate_section_elements(styles, graph_files={})
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_with_graph(self, styles):
        section = _mock_section(technique_graph_mod)
        with patch.object(section, 'generate_grouped_graph_section_flowables',
                          return_value=MagicMock()):
            result = await section.generate_section_elements(
                styles, graph_files={'technique': '/fake/tech.svg'})
            assert len(result) == 1


# ===========================================================================
# Tactic/Technique Table Section
# ===========================================================================
class TestTacticTechniqueTableSection:
    def test_fields(self):
        section = _mock_section(tactic_technique_mod)
        assert section.id == 'tactic-technique-table'

    @pytest.mark.asyncio
    async def test_generate_no_operations(self, styles):
        section = _mock_section(tactic_technique_mod)
        result = await section.generate_section_elements(styles)
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_with_operation(self, styles, make_operation):
        section = _mock_section(tactic_technique_mod)
        op = make_operation()
        result = await section.generate_section_elements(
            styles, operations=[op], selected_sections=[])
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_generate_with_detections_link(self, styles, make_operation):
        section = _mock_section(tactic_technique_mod)
        op = make_operation()
        result = await section.generate_section_elements(
            styles, operations=[op], selected_sections=['ttps-detections'])
        assert len(result) >= 1

    def test_stacked_text(self):
        section = _mock_section(tactic_technique_mod)
        result = section._stacked(['line1', 'line2'])
        assert 'line1' in result
        assert '<br/>' in result

    def test_stacked_html(self):
        section = _mock_section(tactic_technique_mod)
        result = section._stacked(['<link>A</link>'], html=True)
        assert '<link>' in result

    def test_stacked_empty(self):
        section = _mock_section(tactic_technique_mod)
        assert section._stacked([]) == '\u2014'
        assert section._stacked(None) == '\u2014'

    def test_generate_ttp_detection_info_no_strategies(self, styles):
        section = _mock_section(tactic_technique_mod)
        section._a18 = MagicMock()
        section._a18.get_strategies.return_value = []
        section.styles = styles
        section.tt_body = MagicMock()
        result = section._generate_ttp_detection_info('T9999', False)
        assert result == ['\u2014']

    def test_generate_ttp_detection_info_with_strategies(self, styles):
        section = _mock_section(tactic_technique_mod)
        section._a18 = MagicMock()
        section._a18.get_strategies.return_value = [
            {'det_id': 'DET0001', 'name': 'Test Strategy'}
        ]
        section.styles = styles
        section.tt_body = MagicMock()
        result = section._generate_ttp_detection_info('T1082', include_det_links=False)
        assert 'DET0001' in result[0]

    def test_generate_ttp_detection_info_with_links(self, styles):
        section = _mock_section(tactic_technique_mod)
        section._a18 = MagicMock()
        section._a18.get_strategies.return_value = [
            {'det_id': 'DET0001', 'name': 'Test Strategy'}
        ]
        section.styles = styles
        section.tt_body = MagicMock()
        result = section._generate_ttp_detection_info('T1082', include_det_links=True)
        assert 'href' in result[0].lower(), "Detection info with links should contain href attributes"

    def test_parent_fallback(self, styles):
        section = _mock_section(tactic_technique_mod)
        section._a18 = MagicMock()
        # No sub-technique strategies, has parent
        section._a18.get_strategies.side_effect = lambda tid: (
            [] if '.' in tid else [{'det_id': 'DET0002', 'name': 'Parent'}])
        section.styles = styles
        section.tt_body = MagicMock()
        result = section._generate_ttp_detection_info('T1547.001', False)
        # Should contain DET0002 with parent TID reference
        assert 'DET0002' in result[0]
        assert 'T1547' in result[0]
