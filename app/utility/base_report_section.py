from reportlab.lib import colors
from reportlab.platypus import Image, Paragraph, Table, TableStyle
from reportlab.platypus.flowables import KeepTogetherSplitAtTop
from svglib.svglib import svg2rlg

from plugins.debrief.app.objects.c_story import Story


class BaseReportSection:
    def __init__(self):
        self.id = 'base-section-template'
        self.display_name = 'Base Section Template'
        self.description = 'Base class for debrief report section'
        self.section_title = 'BASE SECTION HEADER'

    def generate_section_title_and_description(self, styles):
        return KeepTogetherSplitAtTop([
            Paragraph(self.section_title, styles['Heading2']),
            Paragraph(self.description, styles['Normal']),
        ])

    @staticmethod
    def generate_graph(svg_path, width):
        Story.adjust_icon_svgs(svg_path)
        graph = svg2rlg(svg_path)
        aspect = graph.height / float(graph.width)
        return Image(graph, width=width, height=(width * aspect))

    @staticmethod
    def generate_table(data, col_widths):
        data[1:] = [[Story.get_table_object(val) for val in row] for row in data[1:]]
        tbl = Table(data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.maroon),
                                 ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                 ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                 ('FONTSIZE', (0, 1), (-1, -1), 8),
                                 ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                 ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
                                 ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                 ]))
        for each in range(1, len(data)):
            if each % 2 == 0:
                bg_color = colors.lightgrey
            else:
                bg_color = colors.whitesmoke

            tbl.setStyle(TableStyle([('BACKGROUND', (0, each), (-1, each), bg_color)]))
        return tbl

    @staticmethod
    def status_name(status):
        if status == 0:
            return 'success'
        elif status == -2:
            return 'discarded'
        elif status == 1:
            return 'failure'
        elif status == 124:
            return 'timeout'
        elif status == -3:
            return 'collected'
        elif status == -4:
            return 'untrusted'
        elif status == -5:
            return 'visibility'
        else:
            return 'queued'