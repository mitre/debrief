from reportlab.lib.units import inch
from reportlab.platypus import Paragraph

from plugins.debrief.app.utility.base_report_section import BaseReportSection


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'default-graph'
        self.display_name = 'Operations Graph'
        self.section_title = 'OPERATIONS GRAPH'
        self.description = 'This is a graphical display of the agents connected to the command and control (C2), the ' \
                           'operations run, and the steps of each operation as they relate to the agents.'

    def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        path = kwargs.get('graph_files', {}).get('graph')
        if path:
            # Keep the title, description, and graph grouped together to avoid page break in the middle.
            flowable_list.append(self.generate_grouped_graph_section_flowables(styles, path, 4*inch))

        return flowable_list
