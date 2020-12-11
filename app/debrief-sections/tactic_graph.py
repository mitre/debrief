from reportlab.lib.units import inch
from reportlab.platypus import Spacer

from plugins.debrief.app.utility.base_report_section import BaseReportSection


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'tactic-graph'
        self.display_name = 'Tactic Graph'
        self.section_title = 'Tactic Graph'
        self.description = 'This graph displays the order of tactics executed by the operation. A tactic explains ' \
                           'the general purpose or the "why" of a step.'

    def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        if 'graph_files' in kwargs:
            graph_files = kwargs.get('graph_files', {})
            flowable_list.append(self.generate_section_title_and_description(styles))
            path = graph_files.get('tactic')
            if path:
                flowable_list.append(self.generate_graph(path, 4*inch))

        return flowable_list
