from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import KeepTogetherSplitAtTop
from svglib.svglib import svg2rlg

from plugins.debrief.app.objects.c_story import Story
from plugins.debrief.attack_mapper import get_attack18

# Available content width for portrait pages (letter 8.5" - 2×0.75" margins)
PORTRAIT_CONTENT_WIDTH = 7.0 * inch


class BaseReportSection:
    _status_names = {
        0: 'success',
        -2: 'discarded',
        1: 'failure',
        124: 'timeout',
        -3: 'collected',
        -4: 'untrusted',
        -5: 'visibility',
    }

    def __init__(self):
        self.id = 'base-section-template'
        self.display_name = 'Base Section Template'
        self.description = 'Base class for debrief report section'
        self.section_title = 'BASE SECTION HEADER'
        self._a18 = get_attack18()  # lazy-loaded ATT&CK v18 index

    def generate_section_title_and_description(self, styles):
        """Return grouped flowable containing section title and description."""

        flowable_list = [
            Paragraph(self.section_title, styles['Heading2']),
            Paragraph(self.description, styles['Normal']),
        ]
        return self.group_elements(flowable_list)

    def generate_grouped_graph_section_flowables(self, styles, graph_path, graph_width):
        """Return grouped flowable containing section title, description, and specified graph."""

        return self.group_elements([
            Paragraph(self.section_title, styles['Heading2']),
            Paragraph(self.description, styles['Normal']),
            Spacer(1, 10),
            self.generate_graph(graph_path, graph_width)
        ])

    @staticmethod
    def group_elements(flowable_list):
        """Group flowables together to avoid page breaks in the middle."""

        return KeepTogetherSplitAtTop(flowable_list)

    @staticmethod
    def generate_graph(svg_path, width):
        Story.adjust_icon_svgs(svg_path)
        graph = svg2rlg(svg_path)
        aspect = graph.height / float(graph.width)
        return Image(graph, width=width, height=(width * aspect))

    @staticmethod
    def generate_table(data, col_widths, escape_html=True):
        # Preserve pre-built Paragraph objects (e.g. cells with intentional markup)
        processed_rows = []
        for row in data[1:]:
            processed_row = []
            for val in row:
                if isinstance(val, Paragraph):
                    processed_row.append(val)
                else:
                    processed_row.append(Story.get_table_object(val, escape_html=escape_html))
            processed_rows.append(processed_row)
        data[1:] = processed_rows
        tbl = Table(data, colWidths=col_widths, repeatRows=1)
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.maroon),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEAFTER', (0, 0), (0, -1), 2, colors.maroon),
        ]
        for each in range(1, len(data)):
            bg_color = colors.lightgrey if each % 2 == 0 else colors.whitesmoke
            style_cmds.append(('BACKGROUND', (0, each), (-1, each), bg_color))
        tbl.setStyle(TableStyle(style_cmds))
        return tbl

    @staticmethod
    def status_name(status):
        return BaseReportSection._status_names.get(status, 'queued')
