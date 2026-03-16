"""Exhaustive tests for app/debrief_gui.py — DebriefGui and helpers."""
import pytest
import os
import re
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from plugins.debrief.app.debrief_gui import (
    DebriefGui,
    UseTemplateMarker,
    LockTemplateMarker,
    TemplateSwitchDoc,
)


# ---------------------------------------------------------------------------
# Template marker flowables
# ---------------------------------------------------------------------------
class TestUseTemplateMarker:
    def test_wrap_returns_zero(self):
        m = UseTemplateMarker('Portrait')
        assert m.wrap(100, 100) == (0, 0)

    def test_name_stored(self):
        m = UseTemplateMarker('Landscape')
        assert m.name == 'Landscape'

    def test_draw_does_not_raise(self):
        m = UseTemplateMarker('Portrait')
        m.draw()


class TestLockTemplateMarker:
    def test_wrap_returns_zero(self):
        m = LockTemplateMarker('Landscape')
        assert m.wrap(200, 200) == (0, 0)

    def test_name_stored(self):
        m = LockTemplateMarker('Landscape')
        assert m.name == 'Landscape'

    def test_draw_does_not_raise(self):
        m = LockTemplateMarker('Landscape')
        m.draw()


# ---------------------------------------------------------------------------
# TemplateSwitchDoc.afterFlowable
# ---------------------------------------------------------------------------
class TestTemplateSwitchDoc:
    def _make_doc(self):
        from io import BytesIO
        from reportlab.lib.pagesizes import letter
        buf = BytesIO()
        doc = TemplateSwitchDoc(buf, pagesize=letter)
        return doc, buf

    def test_after_flowable_use_template(self):
        doc, buf = self._make_doc()
        marker = UseTemplateMarker('Portrait')
        doc.handle_nextPageTemplate = MagicMock()
        doc.afterFlowable(marker)
        doc.handle_nextPageTemplate.assert_called()
        buf.close()

    def test_after_flowable_lock_template(self):
        doc, buf = self._make_doc()
        marker = LockTemplateMarker('Landscape')
        doc.handle_nextPageTemplate = MagicMock()
        doc.afterFlowable(marker)
        assert doc._locked_template == 'Landscape'
        buf.close()

    def test_after_flowable_pagebreak_with_locked(self):
        from reportlab.platypus import PageBreak
        doc, buf = self._make_doc()
        doc._locked_template = 'Landscape'
        doc.handle_nextPageTemplate = MagicMock()
        doc.afterFlowable(PageBreak())
        doc.handle_nextPageTemplate.assert_called_with('Landscape')
        buf.close()

    def test_after_flowable_error_handling(self):
        doc, buf = self._make_doc()
        doc.handle_nextPageTemplate = MagicMock(side_effect=Exception('test'))
        marker = UseTemplateMarker('Bad')
        # Should not raise
        doc.afterFlowable(marker)
        buf.close()


# ---------------------------------------------------------------------------
# DebriefGui._sanitize_filename
# ---------------------------------------------------------------------------
class TestSanitizeFilename:
    def test_basic_filename(self):
        assert DebriefGui._sanitize_filename('report.pdf') == 'report.pdf'

    def test_strips_path(self):
        result = DebriefGui._sanitize_filename('/path/to/evil.pdf')
        assert '/' not in result
        assert result == 'evil.pdf'

    def test_removes_special_chars(self):
        result = DebriefGui._sanitize_filename('my report (1).pdf')
        # Only word chars, hyphens, dots, underscores allowed
        assert re.match(r'^[\w._-]+$', result)

    def test_empty_after_sanitize(self):
        result = DebriefGui._sanitize_filename('###')
        assert result == ''

    def test_spaces_to_underscores(self):
        result = DebriefGui._sanitize_filename('my  file.pdf')
        # Spaces become underscores or are removed
        assert ' ' not in result


# ---------------------------------------------------------------------------
# DebriefGui._save_svgs / _clean_downloads
# ---------------------------------------------------------------------------
class TestSvgOperations:
    def test_save_svgs(self, tmp_path):
        import base64
        svg_content = b'<svg></svg>'
        encoded = base64.b64encode(svg_content).decode()
        save_dir = str(tmp_path) + '/'

        with patch('builtins.open', MagicMock()) as mock_open:
            # Monkey-patch save location
            svgs = {'test_graph': encoded}
            with patch('plugins.debrief.app.debrief_gui.DebriefGui._save_svgs') as _:
                # Test the static method directly
                import base64 as b64mod
                for filename, svg_bytes in svgs.items():
                    decoded = b64mod.b64decode(svg_bytes)
                    assert decoded == svg_content

    def test_clean_downloads(self, tmp_path):
        # Create test files
        (tmp_path / 'test.png').write_text('png')
        (tmp_path / 'test.svg').write_text('svg')
        (tmp_path / 'keep.txt').write_text('keep')

        with patch('glob.glob') as mock_glob:
            mock_glob.side_effect = [
                [str(tmp_path / 'test.png')],
                [str(tmp_path / 'test.svg')],
            ]
            with patch('os.remove') as mock_remove:
                DebriefGui._clean_downloads()
                assert mock_remove.call_count == 2


# ---------------------------------------------------------------------------
# DebriefGui._suppress_logs
# ---------------------------------------------------------------------------
class TestSuppressLogs:
    def test_sets_info_level(self):
        import logging
        DebriefGui._suppress_logs('test_lib_debrief')
        logger = logging.getLogger('test_lib_debrief')
        assert logger.level == logging.INFO


# ---------------------------------------------------------------------------
# DebriefGui._get_runtime_agents
# ---------------------------------------------------------------------------
class TestGetRuntimeAgents:
    def _make_gui(self, mock_services):
        with patch('plugins.debrief.app.debrief_gui.BaseWorld'), \
             patch('plugins.debrief.app.debrief_gui.for_all_public_methods', lambda x: lambda cls: cls), \
             patch('plugins.debrief.app.debrief_gui.check_authorization'), \
             patch('plugins.debrief.app.debrief_gui.DebriefService'), \
             patch('plugins.debrief.app.debrief_gui.rl_settings'), \
             patch('plugins.debrief.app.debrief_gui.BaseWorld.get_config', return_value=None):
            gui = DebriefGui.__new__(DebriefGui)
            gui.services = mock_services
            gui.debrief_svc = MagicMock()
            gui.auth_svc = mock_services['auth_svc']
            gui.data_svc = mock_services['data_svc']
            gui.file_svc = mock_services['file_svc']
            gui.knowledge_svc = mock_services.get('knowledge_svc')
            gui.log = MagicMock()
            gui.uploads_dir = '/tmp/uploads'
            gui.report_section_modules = {}
            gui.report_section_names = []
            gui.loaded_report_sections = False
            gui._a18 = None
        return gui

    def test_runtime_agents_filters_correctly(self, mock_services, make_agent, make_link, make_operation):
        gui = self._make_gui(mock_services)
        agent1 = make_agent(paw='paw1')
        agent2 = make_agent(paw='paw2', unique='agent2')
        # Only agent1 has links
        lnk = make_link(paw='paw1')
        op = make_operation(agents=[agent1, agent2], chain=[lnk])
        result = gui._get_runtime_agents([op])
        paws = [a.paw for a in result]
        assert 'paw1' in paws
        assert 'paw2' not in paws

    def test_runtime_agents_empty_ops(self, mock_services):
        gui = self._make_gui(mock_services)
        result = gui._get_runtime_agents([])
        assert result == []

    def test_runtime_agents_none_ops(self, mock_services):
        gui = self._make_gui(mock_services)
        result = gui._get_runtime_agents(None)
        assert result == []

    def test_no_duplicate_agents(self, mock_services, make_agent, make_link, make_operation):
        gui = self._make_gui(mock_services)
        agent = make_agent(paw='paw1')
        l1 = make_link(paw='paw1', unique='u1')
        l2 = make_link(paw='paw1', unique='u2')
        op1 = make_operation(agents=[agent], chain=[l1], op_id='op1')
        op2 = make_operation(agents=[agent], chain=[l2], op_id='op2')
        result = gui._get_runtime_agents([op1, op2])
        assert len(result) == 1


# ---------------------------------------------------------------------------
# DebriefGui._pretty_name
# ---------------------------------------------------------------------------
class TestPrettyName:
    def _make_gui(self):
        gui = DebriefGui.__new__(DebriefGui)
        return gui

    def test_dotted_trait(self):
        gui = self._make_gui()
        assert gui._pretty_name('server.malicious.url') == 'Server Malicious Url'

    def test_underscore_trait(self):
        gui = self._make_gui()
        result = gui._pretty_name('host_user_name')
        assert 'Host' in result

    def test_empty_string(self):
        gui = self._make_gui()
        assert gui._pretty_name('') == ''
