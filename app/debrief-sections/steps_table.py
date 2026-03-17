from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.platypus.flowables import KeepTogetherSplitAtTop

from plugins.debrief.app.utility.base_report_section import BaseReportSection


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'steps-table'
        self.display_name = 'Steps Table'
        self.section_title = 'STEPS IN OPERATION <font name=Courier-Bold size=17>%s</font>'
        self.description = 'The table below shows detailed information about the steps taken in an operation and ' \
                           'whether the command run discovered any facts.'

    async def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        if 'operations' in kwargs:
            operations = kwargs.get('operations', [])
            for o in operations:
                flowable_list.append(
                    KeepTogetherSplitAtTop([
                        Paragraph(self.section_title % o.name.upper(), styles['Heading2']),
                        Paragraph(self.description, styles['Normal'])
                    ])
                )
                flowable_list.append(self._generate_op_steps_table(o))
        return flowable_list

    def _generate_op_steps_table(self, operation):
        steps = [['Time', 'Status', 'Agent', 'Tactic', 'Technique', 'Name', 'Command', 'Facts']]
        for link in operation.chain:
            tactic = getattr(getattr(link, 'ability', None), 'tactic', '') or ''
            technique = getattr(getattr(link, 'ability', None), 'technique_name', '') or ''
            steps.append([
                link.finish or '',
                self.status_name(link.status),
                link.paw,
                tactic,
                technique,
                link.ability.name,
                link.decode_bytes(link.command),
                'Yes' if len([f for f in link.facts if f.score > 0]) > 0 else 'No',
            ])

        return self.generate_table(steps, [
            .7*inch, .55*inch, .55*inch, .65*inch, .85*inch, .75*inch, 2.45*inch, .5*inch
        ])
