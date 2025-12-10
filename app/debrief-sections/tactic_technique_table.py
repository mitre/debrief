import logging

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph

from plugins.debrief.app.utility.base_report_section import BaseReportSection
from plugins.debrief.app.debrief_svc import DebriefService


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'tactic-technique-table'
        self.display_name = 'Tactic and Technique Table'
        self.section_title = 'TACTICS AND TECHNIQUES'
        self.description = ''
        self.log = logging.getLogger('debrief_report_section')

    def _detection_ids_for_ptid(self, ptid: str, tid: str = None):
        """
        Return sorted, unique DET-#### IDs. Prefer exact technique (tid) if provided,
        then fall back to parent (ptid). Fallback to object-id tail when no DET ext id.
        """
        a18 = BaseReportSection.load_attack18()

        def _fetch(tid_like: str):
            ids = []
            strategies = a18.get_strategies(tid_like) or []
            for s in strategies:
                det_id = None
                for er in (s.get('external_references') or []):
                    ext = er.get('external_id', '')
                    if isinstance(ext, str) and ext.startswith('DET-'):
                        det_id = ext
                        break
                if not det_id:
                    det_id = (s.get('id', '') or '')[-8:] or ''
                if det_id:
                    ids.append(det_id)
            return ids

        out = []
        if tid:
            out.extend(_fetch(tid))
        out.extend(_fetch(ptid))
        return sorted(set(out))

    # ---------- Report generation ----------
    async def generate_section_elements(self, styles, **kwargs):
        flowable_list = []
        if 'operations' in kwargs:
            operations = kwargs.get('operations', [])
            ttps = DebriefService.generate_ttps(operations)
            flowable_list.append(self.group_elements([
                Paragraph(self.section_title, styles['Heading2']),
                self._generate_ttps_table(ttps)
            ]))
        return flowable_list

    def _generate_ttps_table(self, ttps):
        """
        Keep existing layout: one row per TACTIC.
        - Techniques column is a stacked list of "Txxxx: Name"
        - NEW Detection column is a stacked list aligned 1:1 with Techniques, each line a comma-joined list of DET IDs
        - Abilities stay as tactic['steps']
        """
        #               0         1           2            3
        ttp_data = [['Tactics', 'Techniques', 'Abilities', 'Detections']]

        for _tac_key, tactic in ttps.items():
            technique_lines = []  # stacked cell for Techniques
            detect_lines = []  # stacked cell for Detection (aligned with techniques)

            # tactic['techniques'] is {technique_name: technique_id}
            for name, tid in tactic.get('techniques', {}).items():
                # Off of parent technique ID (T1059.001 -> T1059)
                ptid = (tid or '').split('.')[0].strip().upper()
                technique_lines.append(f"{tid}: {name}")

                det_ids = self._detection_ids_for_ptid(ptid, tid=tid.upper() if tid else None)
                detect_lines.append(", ".join(det_ids) if det_ids else '—')

            # abilities
            abilities = tactic.get('steps', {})

            ttp_data.append([
                (tactic.get('name') or '').capitalize(),
                technique_lines,
                abilities,
                detect_lines
            ])

        # Column widths: nudge to fit a 4th column on Letter
        return self.generate_table(
            ttp_data,
            [1.25 * inch, 2.85 * inch, 1.10 * inch, 2.10 * inch]
        )

    @staticmethod
    def _get_operation_ttps(operations):
        """
        Aggregates 'steps' by tactic, not by technique.
        """
        ttps = dict()
        for op in operations:
            for link in getattr(op, 'chain', []) or []:
                if getattr(link, 'cleanup', False):
                    continue
                tactic_name = getattr(link.ability, 'tactic', None)
                tech_name = getattr(link.ability, 'technique_name', None)
                tech_id = getattr(link.ability, 'technique_id', None)
                step_name = getattr(link.ability, 'name', None)

                if not tactic_name:
                    # Skip links without a valid tactic
                    continue

                tactic = ttps.setdefault(tactic_name, dict(
                    name=tactic_name,
                    techniques={},
                    steps={}
                ))
                if tech_name and tech_id and tech_name not in tactic['techniques']:
                    tactic['techniques'][tech_name] = tech_id

                if step_name:
                    steps_for_op = tactic['steps'].setdefault(op.name, [])
                    steps_for_op.append(step_name)

        return dict(sorted(ttps.items()))
