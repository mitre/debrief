from plugins.debrief.app.utility.base_report_section import BaseReportSection, PORTRAIT_CONTENT_WIDTH


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'steps-graph'
        self.display_name = 'Steps Graph'
        self.section_title = 'STEPS GRAPH'
        self.description = 'This is a graphical display of the agents connected to the command and control (C2), the ' \
                           'operations run, and the steps of each operation as they relate to the agents.'

    async def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        path = kwargs.get('graph_files', {}).get('steps')
        if path:
            # Keep the title, description, and graph grouped together to avoid page break in the middle.
            flowable_list.append(self.generate_grouped_graph_section_flowables(styles, path, PORTRAIT_CONTENT_WIDTH))

        return flowable_list
