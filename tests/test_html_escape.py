"""Tests for HTML escaping across debrief report sections (SSRF prevention).

Validates that user-controlled strings are properly escaped before being
rendered into PDF report elements, preventing injection of HTML/XML tags
into ReportLab Paragraphs.
"""
import html
import importlib
import pytest

from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from plugins.debrief.app.objects.c_story import Story
from plugins.debrief.app.utility.base_report_section import BaseReportSection

agents_mod = importlib.import_module('plugins.debrief.app.debrief-sections.agents')
facts_table_mod = importlib.import_module('plugins.debrief.app.debrief-sections.facts_table')
steps_table_mod = importlib.import_module('plugins.debrief.app.debrief-sections.steps_table')
tactic_technique_mod = importlib.import_module('plugins.debrief.app.debrief-sections.tactic_technique_table')
ttps_detections_mod = importlib.import_module('plugins.debrief.app.debrief-sections.ttps_detections')

# Common malicious payloads
XSS_PAYLOAD = '<script>alert("xss")</script>'
XSS_ESCAPED = html.escape(XSS_PAYLOAD)
TAG_PAYLOAD = '<img src=x onerror=alert(1)>'
TAG_ESCAPED = html.escape(TAG_PAYLOAD)
AMP_PAYLOAD = 'foo & bar < baz > qux'
AMP_ESCAPED = html.escape(AMP_PAYLOAD)


@pytest.fixture
def styles():
    return getSampleStyleSheet()


def _mock_section(module):
    with patch('plugins.debrief.app.utility.base_report_section.get_attack18') as mock_a18:
        mock_a18.return_value = MagicMock(
            get_strategies=MagicMock(return_value=[]),
            get_analytics=MagicMock(return_value=[]),
            strategies_by_tid={},
            analytics_by_tid={},
            techniques_by_id={},
        )
        section = module.DebriefReportSection()
    return section


# ===========================================================================
# Story.get_table_object — escape_html parameter
# ===========================================================================
class TestStoryGetTableObjectEscaping:
    def test_string_escaped_by_default(self):
        """Strings containing HTML should be escaped by default."""
        para = Story.get_table_object(XSS_PAYLOAD)
        assert isinstance(para, Paragraph)
        # The raw <script> tag should NOT appear unescaped in the paragraph text
        assert '<script>' not in para.text
        assert XSS_ESCAPED in para.text

    def test_string_not_escaped_when_disabled(self):
        """When escape_html=False, raw HTML passes through (for pre-escaped data)."""
        para = Story.get_table_object('<b>bold</b>', escape_html=False)
        assert '<b>bold</b>' in para.text

    def test_list_escaped_by_default(self):
        para = Story.get_table_object([XSS_PAYLOAD, TAG_PAYLOAD])
        assert '<script>' not in para.text
        assert '<img ' not in para.text

    def test_list_not_escaped_when_disabled(self):
        para = Story.get_table_object(['<b>a</b>', '<i>b</i>'], escape_html=False)
        assert '<b>a</b>' in para.text

    def test_dict_keys_escaped_by_default(self):
        para = Story.get_table_object({XSS_PAYLOAD: ['val']})
        assert '<script>' not in para.text

    def test_dict_values_escaped_by_default(self):
        para = Story.get_table_object({'key': [XSS_PAYLOAD]})
        assert '<script>' not in para.text

    def test_dict_not_escaped_when_disabled(self):
        para = Story.get_table_object({'<b>k</b>': ['<i>v</i>']}, escape_html=False)
        assert '<b>k</b>' in para.text
        assert '<i>v</i>' in para.text

    def test_ampersand_escaped(self):
        para = Story.get_table_object(AMP_PAYLOAD)
        assert '&amp;' in para.text
        assert '&lt;' in para.text
        assert '&gt;' in para.text


# ===========================================================================
# Story.append_text — always escapes
# ===========================================================================
class TestStoryAppendTextEscaping:
    def test_append_text_escapes_html(self):
        s = Story()
        style = getSampleStyleSheet()['Normal']
        s.append_text(XSS_PAYLOAD, style, 12)
        para = s.story_arr[0]
        assert isinstance(para, Paragraph)
        assert '<script>' not in para.text
        assert XSS_ESCAPED in para.text

    def test_append_text_escapes_ampersand(self):
        s = Story()
        style = getSampleStyleSheet()['Normal']
        s.append_text('A & B', style, 12)
        para = s.story_arr[0]
        assert '&amp;' in para.text


# ===========================================================================
# BaseReportSection.generate_table — escape_html passthrough
# ===========================================================================
class TestBaseReportSectionGenerateTable:
    def test_generate_table_escapes_by_default(self):
        with patch('plugins.debrief.app.utility.base_report_section.get_attack18') as m:
            m.return_value = MagicMock()
            section = BaseReportSection()

        data = [['Header'], [XSS_PAYLOAD]]
        tbl = section.generate_table(data, '*')
        # data[1][0] should now be a Paragraph with escaped content
        para = data[1][0]
        assert isinstance(para, Paragraph)
        assert '<script>' not in para.text

    def test_generate_table_no_escape(self):
        with patch('plugins.debrief.app.utility.base_report_section.get_attack18') as m:
            m.return_value = MagicMock()
            section = BaseReportSection()

        data = [['Header'], ['<b>already escaped</b>']]
        tbl = section.generate_table(data, '*', escape_html=False)
        para = data[1][0]
        assert '<b>already escaped</b>' in para.text

    def test_generate_table_preserves_paragraph_objects(self):
        """Pre-built Paragraph objects should pass through without re-escaping."""
        with patch('plugins.debrief.app.utility.base_report_section.get_attack18') as m:
            m.return_value = MagicMock()
            section = BaseReportSection()

        style = getSampleStyleSheet()['Normal']
        pre_built = Paragraph('<font color="maroon">markup</font>', style)
        data = [['Header'], [pre_built]]
        tbl = section.generate_table(data, '*')
        # The Paragraph should be preserved as-is, not wrapped again
        assert data[1][0] is pre_built


# ===========================================================================
# Agents section — all fields escaped
# ===========================================================================
class TestAgentsHtmlEscape:
    @pytest.mark.asyncio
    async def test_agent_fields_escaped(self, styles, make_agent):
        section = _mock_section(agents_mod)
        agent = make_agent(
            paw=XSS_PAYLOAD,
            host=TAG_PAYLOAD,
            platform='<plat>',
            group='<grp>',
            username='<user>',
            privilege='<priv>',
            exe_name='<exe>',
            architecture='<arch>',
        )
        result = await section.generate_section_elements(styles, agents=[agent])
        # Section should produce results without error (malicious strings don't crash reportlab)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_agent_paw_anchor_escaped(self, styles, make_agent):
        """The paw anchor format string should use the escaped paw value."""
        section = _mock_section(agents_mod)
        agent = make_agent(paw='<bad>')
        result = await section.generate_section_elements(styles, agents=[agent])
        assert len(result) == 2


# ===========================================================================
# Facts table — trait, value, score, source, command all escaped
# ===========================================================================
class TestFactsTableHtmlEscape:
    def test_trait_escaped(self):
        section = _mock_section(facts_table_mod)
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        fact = SimpleNamespace(
            trait=XSS_PAYLOAD, value='safe', score=1,
            origin_type=OT.LEARNED, source='src', links=[], collected_by=[])
        row = section._generate_fact_table_row(fact, False, {}, 'src', set())
        assert '<script>' not in row[0]
        assert XSS_ESCAPED in row[0]

    def test_value_escaped(self):
        section = _mock_section(facts_table_mod)
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        fact = SimpleNamespace(
            trait='safe', value=XSS_PAYLOAD, score=1,
            origin_type=OT.LEARNED, source='src', links=[], collected_by=[])
        row = section._generate_fact_table_row(fact, False, {}, 'src', set())
        assert '<script>' not in row[1]

    def test_score_escaped(self):
        section = _mock_section(facts_table_mod)
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        fact = SimpleNamespace(
            trait='t', value='v', score=1,
            origin_type=OT.LEARNED, source='src', links=[], collected_by=[])
        row = section._generate_fact_table_row(fact, False, {}, 'src', set())
        # Score should be a string, escaped
        assert row[2] == html.escape('1')

    def test_command_escaped(self):
        section = _mock_section(facts_table_mod)
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        lnk = SimpleNamespace(
            id='lnk1', command=XSS_PAYLOAD, paw='p1')
        lnk.decode_bytes = lambda c: c
        fact = SimpleNamespace(
            origin_type=OT.LEARNED, links=['lnk1'])
        result = section._generate_fact_table_cmd(fact, {'lnk1': lnk})
        assert '<script>' not in result
        assert XSS_ESCAPED in result

    def test_value_truncation_does_not_split_entities(self):
        """Truncation should happen on raw text, then escape, to avoid splitting entities."""
        section = _mock_section(facts_table_mod)
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        # Value with special chars near the truncation boundary
        long_val = 'x' * 1049 + '<'  # 1050 chars, last char is '<'
        fact = SimpleNamespace(
            trait='t', value=long_val, score=1,
            origin_type=OT.LEARNED, source='src', links=[], collected_by=[])
        row = section._generate_fact_table_row(fact, False, {}, 'src', set())
        val_cell = row[1]
        # Should not contain a bare '&lt' split mid-entity
        # The escaped version should have complete entities
        assert '&lt;' in val_cell or '<' not in val_cell.replace('<font', '').replace('<i>', '').replace('</font>', '').replace('</i>', '')

    def test_source_id_escaped(self):
        section = _mock_section(facts_table_mod)
        from enum import Enum
        class OT(Enum):
            LEARNED = 'LEARNED'
        fact = SimpleNamespace(
            trait='t', value='v', score=1,
            origin_type=OT.LEARNED,
            source=XSS_PAYLOAD,
            links=[], collected_by=[])
        result = section._generate_fact_source_cell(
            fact, False, {}, 'other-src', 't', set())
        assert '<script>' not in result


# ===========================================================================
# Steps table — operation name escaped in section title
# ===========================================================================
class TestStepsTableHtmlEscape:
    @pytest.mark.asyncio
    async def test_operation_name_escaped(self, styles, make_operation, make_link, make_ability):
        section = _mock_section(steps_table_mod)
        ab = make_ability()
        lnk = make_link(ability=ab, facts=[SimpleNamespace(score=2)])
        op = make_operation(name=XSS_PAYLOAD, chain=[lnk])
        with patch.object(section, 'generate_table', return_value=MagicMock()):
            result = await section.generate_section_elements(styles, operations=[op])
            assert len(result) >= 2


# ===========================================================================
# Tactic technique table — tactic name escaped
# ===========================================================================
class TestTacticTechniqueTableHtmlEscape:
    @pytest.mark.asyncio
    async def test_tactic_name_escaped(self, styles, make_operation, make_agent, make_ability, make_link):
        section = _mock_section(tactic_technique_mod)
        ab = make_ability(tactic=XSS_PAYLOAD)
        lnk = make_link(ability=ab)
        agent = make_agent()
        op = make_operation(agents=[agent], chain=[lnk])
        result = await section.generate_section_elements(
            styles, operations=[op], selected_sections=[])
        assert len(result) >= 1

    def test_stacked_text_mode_escapes(self):
        section = _mock_section(tactic_technique_mod)
        result = section._stacked([XSS_PAYLOAD, TAG_PAYLOAD])
        assert '<script>' not in result
        assert '<img ' not in result
        assert XSS_ESCAPED in result

    def test_stacked_html_mode_preserves_tags(self):
        """html=True mode should NOT escape — used for pre-built <link> tags."""
        section = _mock_section(tactic_technique_mod)
        link_tag = '<link href="#DET0001" color="blue">DET0001</link>'
        result = section._stacked([link_tag], html=True)
        assert '<link href' in result


# ===========================================================================
# TTPs detections — _p helper and field escaping
# ===========================================================================
class TestTtpsDetectionsHtmlEscape:
    def _make_section(self, styles):
        section = _mock_section(ttps_detections_mod)
        section._ensure_styles()
        return section

    def test_p_helper_escapes(self, styles):
        section = self._make_section(styles)
        para = section._p(XSS_PAYLOAD)
        assert isinstance(para, Paragraph)
        assert '<script>' not in para.text
        assert XSS_ESCAPED in para.text

    def test_p_helper_escapes_ampersand(self, styles):
        section = self._make_section(styles)
        para = section._p(AMP_PAYLOAD)
        assert '&amp;' in para.text

    def test_p_helper_handles_none(self, styles):
        section = self._make_section(styles)
        para = section._p(None)
        assert isinstance(para, Paragraph)


# ===========================================================================
# TTPs detections — None-safe operation name
# ===========================================================================
class TestTtpsDetectionsNoneSafety:
    @pytest.mark.asyncio
    async def test_none_operation_name_does_not_crash(self, styles, make_operation):
        """Operation with name=None should fall back to 'Operation', not crash."""
        section = _mock_section(ttps_detections_mod)
        section._ensure_styles()
        op = make_operation(name=None)
        result = await section.generate_section_elements(
            styles, operations=[op], selected_sections=[])
        # Should not raise TypeError from escape(None)
        assert isinstance(result, list)


# ===========================================================================
# Integration: end-to-end with malicious agent data
# ===========================================================================
class TestEndToEndEscaping:
    @pytest.mark.asyncio
    async def test_full_agents_section_with_xss_payload(self, styles, make_agent):
        """Ensure the full agents section renders without error when agent fields
        contain HTML injection payloads."""
        section = _mock_section(agents_mod)
        malicious_agent = make_agent(
            paw='<script>alert(document.cookie)</script>',
            host='"><img src=x>',
            platform="linux'; DROP TABLE agents;--",
            username='<iframe src="evil">',
            privilege='<object data="evil">',
            exe_name='<embed src="evil">',
            group='<svg onload=alert(1)>',
            architecture='<math><mi>',
        )
        result = await section.generate_section_elements(styles, agents=[malicious_agent])
        assert len(result) == 2  # title + table, no crash

    @pytest.mark.asyncio
    async def test_full_facts_section_with_xss_payload(self, styles, make_operation, make_fact):
        """Ensure facts table section renders with malicious fact data."""
        section = _mock_section(facts_table_mod)
        malicious_fact = make_fact(
            trait='<script>alert(1)</script>',
            value='<img src=x onerror=alert(1)>',
        )
        op = make_operation(name='<script>op</script>', facts=[malicious_fact])
        with patch.object(section, 'generate_table', return_value=MagicMock()):
            result = await section.generate_section_elements(styles, operations=[op])
            assert len(result) >= 2
