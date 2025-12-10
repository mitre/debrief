from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.platypus.flowables import KeepTogetherSplitAtTop

from html import escape

from plugins.debrief.app.utility.base_report_section import BaseReportSection

TABLE_CHAR_LIMIT = 1050


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
                selected_sections = kwargs.get('selected_sections', [])
                flowable_list.append(await self._generate_facts_table(o, selected_sections))
        return flowable_list

    def _origin_name(self, f):
        ot = getattr(f, 'origin_type', None)
        return getattr(ot, 'name', None) or (str(ot).split('.')[-1].split(':')[0].strip('>') if ot else None)

    async def _generate_facts_table(self, operation, selected_sections, whitecard_metrics=None):
        include_agent_links = ('agents' in (selected_sections or []))

        # Header
        fact_data = [['Trait', 'Value', 'Score', 'Source', 'Command Run']]
        exceeds_msg = '... <font color="maroon"><i>(Value exceeds table cell character limit)</i></font>'
        link_by_id = {getattr(lnk, 'id', None): lnk for lnk in (getattr(operation, 'chain', []) or [])}

        # Normalize op source id once
        op_source_id = str(getattr(getattr(operation, 'source', None), 'id', '') or '')

        # Build a whitelist of traits that truly came from the op's white-card source (if provided)
        white_traits = {str(m.get('trait')).strip()
                        for m in (whitecard_metrics or [])
                        if m.get('trait')}

        facts = await operation.all_facts()

        for f in facts:
            # --- fields ---
            trait = (getattr(f, 'trait', '') or '').replace('\n', '').replace('\r', '')
            raw_value = getattr(f, 'value', '')
            score = getattr(f, 'score', 0)

            origin = (self._origin_name(f) or '').upper()
            fact_source_id = str(getattr(f, 'source', '') or '')
            source_cell = None

            # --- provenance: White Card vs Imported vs runtime PAWs ---
            is_whitecard = (
                origin == 'IMPORTED' and
                fact_source_id == op_source_id and
                (not white_traits or trait in white_traits)
            )

            if is_whitecard:
                source_cell = 'White Card'
            elif origin == 'IMPORTED':
                source_cell = 'Imported'
            else:
                # Runtime -> show PAWs that collected the fact
                paws = set(getattr(f, 'collected_by', []) or [])
                if not paws:
                    for lid in (getattr(f, 'links', []) or []):
                        lnk = link_by_id.get(lid)
                        if lnk and getattr(lnk, 'paw', None):
                            paws.add(lnk.paw)
                if paws:
                    paws = sorted(paws)
                    if include_agent_links:
                        source_cell = ', '.join(f'<link href="#agent-{escape(p)}" color="blue">{escape(p)}</link>' for p in paws)
                    else:
                        source_cell = ', '.join(escape(p) for p in paws)
            if not source_cell:
                src = fact_source_id
                source_cell = (f'{src[:3]}..{src[-3:]}' if len(src) >= 6 else (src or '—'))

            # --- commands ---
            commands = set()
            for lid in (getattr(f, 'links', []) or []):
                lnk = link_by_id.get(lid)
                if lnk and getattr(lnk, 'command', None):
                    try:
                        commands.add(lnk.decode_bytes(lnk.command))
                    except Exception:
                        commands.add(str(lnk.command))
            command_value = '<br />'.join(sorted(c for c in commands if c)) if commands else f'No Command ({origin or "UNKNOWN"})'

            # --- value truncation for layout ---
            if isinstance(raw_value, str):
                val_cell = raw_value if len(raw_value) < TABLE_CHAR_LIMIT else (raw_value[:TABLE_CHAR_LIMIT] + exceeds_msg)
            else:
                sval = str(raw_value) if raw_value is not None else ''
                val_cell = sval if len(sval) < TABLE_CHAR_LIMIT else (sval[:TABLE_CHAR_LIMIT] + exceeds_msg)

            fact_data.append([trait, val_cell, str(score), source_cell, command_value])

        # Slightly wider Source/Command columns
        return self.generate_table(fact_data, [1*inch, 2*inch, .6*inch, 1.25*inch, 2.5*inch])
