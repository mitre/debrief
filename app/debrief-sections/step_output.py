import logging

from html import escape
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.platypus.flowables import KeepTogetherSplitAtTop

from plugins.debrief.app.utility.base_report_section import BaseReportSection

OUTPUT_CHAR_LIMIT = 500
TRUNCATED_MSG = '... <font color="maroon"><i>(output truncated)</i></font>'


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'step-output'
        self.display_name = 'Step Output'
        self.section_title = 'STEP OUTPUT FOR OPERATION <font name=Courier-Bold size=17>%s</font>'
        self.description = 'The table below shows the command output (stdout) for each step in the operation. ' \
                           'Only steps that produced output are included. Output is truncated at %d characters.' \
                           % OUTPUT_CHAR_LIMIT
        self.log = logging.getLogger('DebriefStepOutput')

    async def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        if 'operations' not in kwargs:
            return flowable_list

        for op in kwargs.get('operations', []):
            table = self._generate_output_table(op)
            if table is None:
                continue  # skip section entirely when no output captured
            flowable_list.append(
                KeepTogetherSplitAtTop([
                    Paragraph(self.section_title % escape(op.name.upper()), styles['Heading2']),
                    Paragraph(self.description, styles['Normal'])
                ])
            )
            flowable_list.append(table)

        return flowable_list

    def _generate_output_table(self, operation):
        data = [['Step', 'Status', 'Agent', 'Output']]
        for link in operation.chain:
            output = self._get_output(link)
            if not output:
                continue
            if len(output) > OUTPUT_CHAR_LIMIT:
                output = output[:OUTPUT_CHAR_LIMIT] + TRUNCATED_MSG
            else:
                output = escape(output)
            data.append([
                getattr(link.ability, 'name', '') or '',
                self.status_name(link.status),
                link.paw,
                output,
            ])

        if len(data) == 1:
            return None  # no output to show

        return self.generate_table(data, [1.2*inch, .6*inch, .6*inch, 4.6*inch], escape_html=False)

    def _get_output(self, link):
        """Decode link output, returning empty string if unavailable."""
        raw = getattr(link, 'output', None)
        if not raw:
            return ''
        try:
            decoded = link.decode_bytes(raw)
            return decoded.strip() if decoded else ''
        except Exception:
            self.log.debug(f'Could not decode output for link {getattr(link, "id", "?")}')
            return ''
