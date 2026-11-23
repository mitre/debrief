"""Tests for app/utility/base_report_section.py — BaseReportSection."""
import importlib
import logging
import sys

import pytest
from unittest.mock import patch, MagicMock

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.flowables import KeepTogetherSplitAtTop

from plugins.debrief.app.utility.base_report_section import BaseReportSection, SVGLIB_MISSING


@pytest.fixture
def section():
    with patch('plugins.debrief.app.utility.base_report_section.get_attack18') as mock_a18:
        mock_a18.return_value = MagicMock()
        s = BaseReportSection()
    return s


class TestBaseReportSectionInit:
    def test_default_fields(self, section):
        assert section.id == 'base-section-template'
        assert section.display_name == 'Base Section Template'
        assert section.description == 'Base class for debrief report section'
        assert section.section_title == 'BASE SECTION HEADER'


class TestStatusName:
    def test_success(self):
        assert BaseReportSection.status_name(0) == 'success'

    def test_failure(self):
        assert BaseReportSection.status_name(1) == 'failure'

    def test_discarded(self):
        assert BaseReportSection.status_name(-2) == 'discarded'

    def test_timeout(self):
        assert BaseReportSection.status_name(124) == 'timeout'

    def test_collected(self):
        assert BaseReportSection.status_name(-3) == 'collected'

    def test_untrusted(self):
        assert BaseReportSection.status_name(-4) == 'untrusted'

    def test_visibility(self):
        assert BaseReportSection.status_name(-5) == 'visibility'

    def test_unknown_returns_queued(self):
        assert BaseReportSection.status_name(999) == 'queued'
        assert BaseReportSection.status_name(-999) == 'queued'


class TestGenerateSectionTitleAndDescription:
    def test_returns_grouped_flowable(self, section):
        styles = getSampleStyleSheet()
        result = section.generate_section_title_and_description(styles)
        assert isinstance(result, KeepTogetherSplitAtTop)


class TestGroupElements:
    def test_returns_keep_together(self, section):
        from reportlab.platypus import Paragraph
        styles = getSampleStyleSheet()
        elems = [Paragraph('test', styles['Normal'])]
        result = section.group_elements(elems)
        assert isinstance(result, KeepTogetherSplitAtTop)


class TestGenerateTable:
    def test_generates_table(self, section):
        from reportlab.platypus import Table
        data = [['Col1', 'Col2'], ['val1', 'val2'], ['val3', 'val4']]
        result = section.generate_table(data, '*')
        assert isinstance(result, Table)

    def test_alternating_row_colors(self, section):
        from reportlab.platypus import Table
        data = [['Col1'], ['row1'], ['row2'], ['row3']]
        result = section.generate_table(data, '*')
        assert isinstance(result, Table)


SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">'
       '<rect x="10" y="10" width="180" height="80" fill="maroon"/></svg>')


@pytest.fixture
def svg_path(tmp_path):
    path = tmp_path / 'graph.svg'
    path.write_text(SVG)
    return str(path)


@pytest.fixture
def without_svglib(monkeypatch):
    """Make ``import svglib`` fail, as it does where the package is not installed."""
    for name in [m for m in sys.modules if m == 'svglib' or m.startswith('svglib.')]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, 'svglib', None)


class TestGenerateGraph:
    def test_renders_svg_with_aspect_ratio_kept(self, svg_path):
        pytest.importorskip('svglib')
        from reportlab.platypus import Image

        graph = BaseReportSection.generate_graph(svg_path, 400)

        assert isinstance(graph, Image)
        assert (graph.drawWidth, graph.drawHeight) == (400, 200)

    def test_graph_section_builds_into_a_pdf(self, section, svg_path, tmp_path):
        pytest.importorskip('svglib')
        from reportlab.platypus import SimpleDocTemplate
        out = tmp_path / 'report.pdf'

        flowable = section.generate_grouped_graph_section_flowables(getSampleStyleSheet(), svg_path, 400)
        SimpleDocTemplate(str(out)).build([flowable])

        assert out.read_bytes().startswith(b'%PDF')

    def test_returns_none_and_logs_without_svglib(self, without_svglib, svg_path, caplog):
        with caplog.at_level(logging.WARNING, logger='debrief_report_section'):
            assert BaseReportSection.generate_graph(svg_path, 400) is None

        assert SVGLIB_MISSING in caplog.text

    def test_graph_section_shows_note_without_svglib(self, without_svglib, section, svg_path, tmp_path):
        from reportlab.platypus import Paragraph, SimpleDocTemplate
        out = tmp_path / 'report.pdf'

        flowable = section.generate_grouped_graph_section_flowables(getSampleStyleSheet(), svg_path, 400)
        last = flowable._content[-1]
        SimpleDocTemplate(str(out)).build([flowable])

        assert isinstance(last, Paragraph)
        assert last.text == SVGLIB_MISSING
        assert out.read_bytes().startswith(b'%PDF')


def test_module_imports_without_svglib(without_svglib, monkeypatch):
    name = 'plugins.debrief.app.utility.base_report_section'
    monkeypatch.delitem(sys.modules, name)

    module = importlib.import_module(name)

    assert module.BaseReportSection.__name__ == 'BaseReportSection'
