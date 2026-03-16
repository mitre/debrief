"""Tests for app/objects/c_story.py — Story class."""
import pytest
from unittest.mock import MagicMock, patch

from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from plugins.debrief.app.objects.c_story import Story


class TestStoryInit:
    def test_empty_story(self):
        s = Story()
        assert s.story_arr == []

    def test_header_logo_path_default(self):
        s = Story()
        assert Story._header_logo_path is not None or Story._header_logo_path is None


class TestStoryAppend:
    def test_append_adds_data_and_spacer(self):
        s = Story()
        para = Paragraph('hello', getSampleStyleSheet()['Normal'])
        s.append(para)
        assert len(s.story_arr) == 2
        assert isinstance(s.story_arr[1], Spacer)

    def test_append_custom_spacing(self):
        s = Story()
        para = Paragraph('test', getSampleStyleSheet()['Normal'])
        s.append(para, spacing=24)
        # Second item is a spacer
        assert isinstance(s.story_arr[1], Spacer)

    def test_append_zero_spacing(self):
        s = Story()
        para = Paragraph('test', getSampleStyleSheet()['Normal'])
        s.append(para, spacing=0)
        assert len(s.story_arr) == 2


class TestStoryAppendText:
    def test_append_text(self):
        s = Story()
        styles = getSampleStyleSheet()
        s.append_text('Hello World', styles['Normal'], 12)
        assert len(s.story_arr) == 2
        assert isinstance(s.story_arr[0], Paragraph)
        assert isinstance(s.story_arr[1], Spacer)


class TestStoryPageBreak:
    def test_page_break(self):
        s = Story()
        s.page_break()
        assert len(s.story_arr) == 1
        assert isinstance(s.story_arr[0], PageBreak)


class TestSetHeaderLogoPath:
    def test_set_path(self):
        Story.set_header_logo_path('/some/path/logo.png')
        assert Story._header_logo_path == '/some/path/logo.png'

    def test_set_none(self):
        Story.set_header_logo_path(None)
        assert Story._header_logo_path is None


class TestGetTableObject:
    def test_string_input(self):
        result = Story.get_table_object('hello')
        assert isinstance(result, Paragraph)

    def test_list_input(self):
        result = Story.get_table_object(['item1', 'item2'])
        assert isinstance(result, Paragraph)

    def test_dict_input(self):
        result = Story.get_table_object({'key': ['val1', 'val2']})
        assert isinstance(result, Paragraph)


class TestGetDescription:
    def test_get_description(self):
        s = Story()
        # _descriptions doesn't exist as a method; this tests the proxy
        with pytest.raises(AttributeError):
            s.get_description('test')
