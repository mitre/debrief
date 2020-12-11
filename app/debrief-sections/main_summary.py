from datetime import datetime
from reportlab.platypus import Paragraph, Spacer
from reportlab.platypus.flowables import KeepTogetherSplitAtTop

from plugins.debrief.app.utility.base_report_section import BaseReportSection


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'main-summary'
        self.display_name = 'Main Summary'
        self.section_title = 'OPERATIONS DEBRIEF'
        self.description = 'This document covers the overall campaign analytics made up of the selected set of ' \
                           'operations. The below sections contain general metadata about the selected operations ' \
                           'as well as graphical views of the operations, the techniques and tactics used, and the ' \
                           'facts discovered by the operations. The following sections include a more in depth ' \
                           'review of each specific operation ran.'

    def generate_section_elements(self, styles, **kwargs):
        title = styles['Heading1']
        title.fontName = 'VeraBd'
        title.textColor = 'maroon'
        title.fontSize = 24
        timestamp = "<i>Generated on %s</i>" % datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        return [
            KeepTogetherSplitAtTop([
                Paragraph(self.section_title, title),
                Spacer(1, 6),
                Paragraph(timestamp, styles['Normal']),
                Spacer(1, 12),
                Paragraph(self.description, styles['Normal'])
            ])
        ]