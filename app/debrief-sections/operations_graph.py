from reportlab.lib.units import inch

from plugins.debrief.app.utility.base_report_section import BaseReportSection


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'default-graph'
        self.display_name = 'Operations Graph'
        self.section_title = 'Operations Graph'
        self.description = 'This is a graphical display of the agents connected to the command and control (C2), the ' \
                           'operations run, and the steps of each operation as they relate to the agents.'

    def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        if 'graph_files' in kwargs:
            graph_files = kwargs.get('graph_files', {})
            flowable_list.append(self.generate_section_title_and_description(styles))
            path = graph_files.get('graph')
            if path:
                flowable_list.append(self.generate_graph(path, 4*inch))

        return flowable_list
