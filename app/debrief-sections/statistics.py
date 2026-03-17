from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from plugins.debrief.app.utility.base_report_section import BaseReportSection
from plugins.debrief.app.objects.c_story import Story


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'statistics'
        self.display_name = 'Statistics'
        self.section_title = 'STATISTICS'
        self.description = 'An operation\'s planner makes up the decision making process. It contains logic for how ' \
                           'a running operation should make decisions about which abilities to use and in what order.' \
                           ' An objective is a collection of fact targets, called goals, which can be tied to ' \
                           'adversaries. During the course of an operation, every time the planner is evaluated, the ' \
                           'current objective status is evaluated in light of the current knowledge of the ' \
                           'operation, with the operation completing should all goals be met.'

    async def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        if 'operations' not in kwargs:
            return flowable_list

        operations = kwargs.get('operations', [])
        flowable_list.append(self.generate_section_title_and_description(styles))

        # --- Campaign Summary ---
        flowable_list.append(self._build_campaign_summary(operations, styles))
        flowable_list.append(Spacer(1, 10))

        # --- Per-Operation Table ---
        data = [['Name', 'State', 'Planner', 'Objective', 'Time']]
        for o in operations:
            finish = o.finish if o.finish else 'Not finished'
            data.append([o.name, o.state, o.planner.name, o.objective.name, finish])
        flowable_list.append(self.generate_table(data, '*'))

        return flowable_list

    def _build_campaign_summary(self, operations, styles):
        """Build a key-value summary table with aggregate campaign metrics."""
        all_links = []
        all_agents = set()
        tactics = set()
        techniques = set()

        for op in operations:
            for link in (getattr(op, 'chain', []) or []):
                if getattr(link, 'cleanup', 0):
                    continue
                all_links.append(link)
                ability = getattr(link, 'ability', None)
                if ability:
                    tactic = getattr(ability, 'tactic', None)
                    tid = getattr(ability, 'technique_id', None)
                    if tactic:
                        tactics.add(tactic)
                    if tid:
                        techniques.add(tid)
            for agent in (getattr(op, 'agents', []) or []):
                paw = getattr(agent, 'paw', None)
                if paw:
                    all_agents.add(paw)

        # Status counts
        status_counts = {}
        for link in all_links:
            status = getattr(link, 'status', None)
            name = self.status_name(status)
            status_counts[name] = status_counts.get(name, 0) + 1

        status_str = ', '.join(f'{v} {k}' for k, v in sorted(status_counts.items(), key=lambda x: -x[1]))

        # Build key-value pairs
        rows = [
            ['Metric', 'Value'],
            ['Operations', str(len(operations))],
            ['Total Steps', str(len(all_links))],
            ['Steps by Status', status_str or 'N/A'],
            ['Unique Agents', str(len(all_agents))],
            ['Unique Tactics', str(len(tactics))],
            ['Unique Techniques', str(len(techniques))],
        ]

        rows[1:] = [[Story.get_table_object(val) for val in row] for row in rows[1:]]
        tbl = Table(rows, colWidths=[1.5 * inch, 5.5 * inch], repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.maroon),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        for i in range(1, len(rows)):
            bg = colors.lightgrey if i % 2 == 0 else colors.whitesmoke
            tbl.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), bg)]))
        return tbl
