"""Tests for app/utility/base_report_section.py — BaseReportSection."""
import pytest
from unittest.mock import patch, MagicMock

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.flowables import KeepTogetherSplitAtTop

from plugins.debrief.app.utility.base_report_section import BaseReportSection


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
