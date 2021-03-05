from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.platypus.flowables import KeepTogetherSplitAtTop

from plugins.debrief.app.utility.base_report_section import BaseReportSection

TABLE_CHAR_LIMIT = 1800


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'facts-table'
        self.display_name = 'Operation Facts Table'
        self.section_title = 'FACTS FOUND IN OPERATION <font name=Courier-Bold size=17>%s</font>'
        self.description = 'The table below displays the facts found in the operation, the command run and the agent ' \
                           'that found the fact. Every fact, by default, gets a score of 1. If a host.user.password ' \
                           'fact is important or has a high chance of success if used, you may assign it a score of ' \
                           '5. When an ability uses a fact to fill in a variable, it will use those with the highest ' \
                           'scores first. A fact with a score of 0, is blacklisted - meaning it cannot be used in ' \
                           'an operation.'

    def generate_section_elements(self, styles, **kwargs):
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
                flowable_list.append(self._generate_facts_table(o))
        return flowable_list

    def _generate_facts_table(self, operation):
        fact_data = [['Trait', 'Value', 'Score', 'Paw', 'Command Run']]
        exceeds_cell_msg = '... <font color="maroon"><i>(Value exceeds table cell character limit)</i></font>'
        for lnk in operation.chain:
            if len(lnk.facts) > 0:
                for f in lnk.facts:
                    fact_data.append(
                        [f.trait,
                         f.value if len(f.value) < TABLE_CHAR_LIMIT else f.value[:TABLE_CHAR_LIMIT] + exceeds_cell_msg,
                         str(f.score),
                         '<link href="#agent-{0}" color="blue">{0}</link>'.format(lnk.paw),
                         lnk.decode_bytes(lnk.command)])
        return self.generate_table(fact_data, [1 * inch, 2.1 * inch, .6 * inch, .6 * inch, 2.1 * inch])
