from datetime import datetime, timezone
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

    async def generate_section_elements(self, styles, **kwargs):
        title = styles['Heading1']
        title.fontName = 'Helvetica-Bold'
        title.textColor = 'maroon'
        title.fontSize = 24
        timestamp = "<i>Generated on %s</i>" % datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        flowables = [
            Paragraph(self.section_title, title),
            Spacer(1, 6),
            Paragraph(timestamp, styles['Normal']),
            Spacer(1, 12),
            Paragraph(self.description, styles['Normal']),
        ]

        # Campaign summary on cover page
        operations = kwargs.get('operations', [])
        if operations:
            flowables.append(Spacer(1, 16))
            summary = self._build_cover_summary(operations)
            flowables.append(Paragraph(summary, styles['Normal']))

        return [KeepTogetherSplitAtTop(flowables)]

    def _build_cover_summary(self, operations):
        """Build a brief campaign summary for the cover page."""
        op_names = ', '.join(f'<b>{o.name}</b>' for o in operations)

        total_steps = 0
        agents = set()
        for op in operations:
            for link in (getattr(op, 'chain', []) or []):
                if not getattr(link, 'cleanup', 0):
                    total_steps += 1
            for agent in (getattr(op, 'agents', []) or []):
                paw = getattr(agent, 'paw', None)
                if paw:
                    agents.add(paw)

        lines = [
            f'<b>Operations:</b> {op_names}',
            f'<b>Agents:</b> {len(agents)} &nbsp;&nbsp; <b>Steps:</b> {total_steps}',
        ]
        return '<br/>'.join(lines)
