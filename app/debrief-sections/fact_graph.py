from reportlab.lib.units import inch
from reportlab.platypus import Spacer

from plugins.debrief.app.utility.base_report_section import BaseReportSection


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'fact-graph'
        self.display_name = 'Fact Graph'
        self.section_title = 'Fact Graph'
        self.description = 'This graph displays the facts discovered by the operations run. Facts are attached to ' \
                           'the operation where they were discovered. Facts are also attached to the facts that led ' \
                           'to their discovery. For readability, only the first 15 facts discovered in an operation ' \
                           'are included in the graph.'

    def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        if 'graph_files' in kwargs:
            graph_files = kwargs.get('graph_files', {})
            flowable_list.append(self.generate_section_title_and_description(styles))
            flowable_list.append(Spacer(1, 12))

            path = graph_files.get('fact')
            if path:
                flowable_list.append(self.generate_graph(path, 4*inch))

        return flowable_list
