from reportlab.lib.units import inch
from reportlab.platypus import Spacer

from plugins.debrief.app.utility.base_report_section import BaseReportSection


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'technique-graph'
        self.display_name = 'Technique Graph'
        self.section_title = 'Technique Graph'
        self.description = 'This graph displays the order of techniques executed by the operation. A technique ' \
                           'explains the technical method or the "how" of a step.'

    def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        if 'graph_files' in kwargs:
            graph_files = kwargs.get('graph_files', {})
            flowable_list.append(self.generate_section_title_and_description(styles))
            flowable_list.append(Spacer(1, 12))

            path = graph_files.get('technique')
            if path:
                flowable_list.append(self.generate_graph(path, 4*inch))

        return flowable_list
