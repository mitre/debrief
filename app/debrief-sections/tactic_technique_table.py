import logging
import re
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, TableStyle, Table
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from html import escape

from plugins.debrief.app.utility.base_report_section import BaseReportSection
from plugins.debrief.app.debrief_svc import DebriefService


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'tactic-technique-table'
        self.display_name = 'Tactic and Technique Table'
        self.section_title = 'TACTICS AND TECHNIQUES'
        self.description = ''
        self.log = logging.getLogger('DebriefTacticsTechniqueTable')

    # ---------- Report generation ----------
    async def generate_section_elements(self, styles, **kwargs):
        self.tt_body = ParagraphStyle(
            name='tt-body',
            parent=styles['Normal'],
            textColor=colors.black,
            fontSize=10,
            leading=12,
            spaceBefore=0,
            spaceAfter=0,
            alignment=0,
        )

        flowable_list = []
        self.styles = styles

        if 'operations' in kwargs:
            self.log.debug('Generating Tactic and Technique Table section')
            self.log.debug(f'  - Operations count: {len(kwargs.get('operations', []))}')

            operations = kwargs.get('operations', [])
            ttps = DebriefService.generate_ttps(operations, key_by_tid=True) or {}

            # ----------------------------------------------------------
            # PREDECLARE DET ANCHORS — must go INSIDE the KeepTogether block
            # ----------------------------------------------------------
            anchors = []
            predeclared = set()

            for tactic in ttps.values():
                tech_map = tactic.get('techniques') or {}

                for tid, tname in tech_map.items():
                    strategies = self._a18.get_strategies(tid) or []

                    for s in strategies:
                        det = self._normalize_det_id(s.get('det_id') or '')
                        if not det or det in predeclared:
                            continue

                        anchor = self._anchor_for_det(det)
                        anchors.append(Paragraph(f'<a name="{anchor}"/>', styles['Normal']))
                        predeclared.add(det)
                        self.log.debug(f'[TT-PREDECL] emitted anchor for {det} -> {anchor}')

            # ----------------------------------------------------------
            # Build section as ONE KeepTogether block containing:
            #   - anchors
            #   - section title
            #   - final table
            # ----------------------------------------------------------
            block = self.group_elements(
                anchors + [
                    Paragraph(self.section_title, styles['Heading2']),
                    self._generate_ttps_table(ttps, operations)
                ]
            )

            flowable_list.append(block)

        return flowable_list

    # Use child technique strategies first; fallback to parent strategies.
    # Only DETs present in ATT&CK strategies are allowed.
    # Analytics guide choosing between multiple strategy DETs,
    # but analytics do NOT create new DETs.
    def _generate_ttp_detection_link(self, tid):
        # --- Child technique strategies ---
        ptid = (tid or '').split('.')[0].strip().upper()
        child_strats = self._a18.get_strategies(tid) or []
        parent_strats = self._a18.get_strategies(ptid) or []

        if child_strats:
            strategies = child_strats
            self.log.debug(f'[TTP-07] Using CHILD strategies for {tid}: {len(strategies)} found')
        else:
            strategies = parent_strats
            self.log.debug(f'[TTP-07] Using PARENT strategies for {tid}: {len(strategies)} found')

        # Collect allowed DETs from strategies (appendix will render only these)
        valid_strategy_dets = []
        for s in strategies:
            det_id = self._normalize_det_id(s.get('det_id') or '')
            if det_id:
                valid_strategy_dets.append(det_id)

        self.log.debug(f'[TTP-07] Strategy DETs: {valid_strategy_dets}')

        if not valid_strategy_dets:
            self.log.warn(f'[TTP-08] No valid strategy DETs for {tid} — using placeholder')
            return '—'

        # Analytics: used only for ranking selection
        analytics = self._a18.get_analytics(tid, platform=None) or []
        self.log.debug(f'[TTP-07] Analytics loaded for {tid}: {len(analytics)} items')

        # Prefer DETs whose analytics match the exact sub-technique
        child_hits = []

        for det in valid_strategy_dets:
            for row in analytics:
                row_det = self._normalize_det_id(row.get('det_id') or '')
                if row_det != det:
                    continue
                child_hits.append(det)

        if child_hits:
            det_label = child_hits[0]
            self.log.debug(f'[TTP-08] Choosing child-hit DET for {tid}: {det_label}')
        else:
            det_label = valid_strategy_dets[0]
            self.log.debug(f'[TTP-08] No child-hit analytics; defaulting DET for {tid}: {det_label}')

        # Build the PDF link (safe: appendix WILL contain this anchor)
        try:
            det_anchor = self._anchor_for_det(det_label)
            link = f'<link href="#{escape(det_anchor)}" color="blue">{escape(det_label)}</link>'
            return link
        except Exception:
            self.log.exception('[ERR-TTP-09] DET link building failed')
            raise

    def _generate_ttps_table(self, ttps, operations):
        '''
        One row per TACTIC.
        - Techniques: stacked 'Txxxx: Name'
        - Detections: stacked DET IDs (as links) aligned 1:1 with Techniques
        - Abilities: stacked ability names (operation name stripped)
        '''

        ttp_data = [['Tactics', 'Techniques', 'Abilities', 'Detections']]

        for _tac_key, tactic in ttps.items():
            technique_lines = []
            detect_lines = []
            tech_map = tactic.get('techniques') or {}

            for tid, tname in tech_map.items():
                self.log.debug(f'  - Processing technique: TID={tid}, Name={tname}')
                self.log.debug(f'[TTP-05] Technique loop: tid={tid}, tname={tname}')

                # ------------------------------------------------------------------
                # TECHNIQUE LABEL
                # ------------------------------------------------------------------
                try:
                    label = f'{tid}: {tname}' if (tid and tname) else (tid or tname or '—')
                    technique_lines.append(label)
                except Exception:
                    self.log.exception('[ERR-TTP-06] Failed building technique label')
                    raise

                # ------------------------------------------------------------------
                # DETECTION SELECTION
                # ------------------------------------------------------------------
                try:
                    link = self._generate_ttp_detection_link(tid)
                    detect_lines.append(link)
                    self.log.debug(f'[TTP-09] DET link built: {link}')
                except Exception:
                    self.log.exception('[ERR-TTP-08] DET selection failed')
                    raise

            # ----------------------------------------------------------------------
            # ABILITIES
            # ----------------------------------------------------------------------
            raw_steps = []
            for _opname, steps in (tactic.get('steps') or {}).items():
                raw_steps.extend(steps or [])
                self.log.debug(f'    - Found steps for op {_opname}: {steps}')

            cleaned_steps = []
            for ability in raw_steps:
                a = ability or ''
                a = re.sub(r'^[^:]+:\s*', '', a)
                a = re.sub(r'\s*\((?:operation|op)[^)]*\)\s*$', '', a, flags=re.I)
                cleaned_steps.append(a.strip() or '—')

            # ----------------------------------------------------------------------
            # Build Paragraphs
            # ----------------------------------------------------------------------
            t_para = Paragraph(self._stacked(technique_lines), self.tt_body)
            a_para = Paragraph(self._stacked(cleaned_steps),   self.tt_body)
            d_style = ParagraphStyle('tt-body-center', parent=self.tt_body, alignment=1)
            d_para = Paragraph(self._stacked(detect_lines, html=True), d_style)

            ttp_data.append([
                (tactic.get('name') or '').capitalize(),
                t_para, a_para, d_para
            ])

        # --------------------------------------------------------------------------
        # TABLE LAYOUT
        # --------------------------------------------------------------------------
        tbl = Table(
            ttp_data,
            colWidths=[
                0.75*inch,  # Tactics
                2.85*inch,  # Techniques
                1.75*inch,  # Abilities
                0.90*inch   # Detections
            ],
            hAlign='LEFT'
        )

        header_bg = colors.maroon
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN',      (0, 0), (-1, 0), 'CENTER'),

            ('VALIGN',     (0, 1), (-1, -1), 'TOP'),
            ('TEXTCOLOR',  (0, 1), (-1, -1), colors.black),

            ('ALIGN',      (0, 1), (0, -1), 'CENTER'),
            ('ALIGN',      (1, 1), (2, -1), 'LEFT'),
            ('ALIGN',      (3, 1), (3, -1), 'CENTER'),

            ('BOX',        (0, 0), (-1, -1), 0.75, colors.black),
            ('INNERGRID',  (0, 0), (-1, -1), 0.25, colors.black),

            ('LEFTPADDING',   (0, 0), (-1, -1), 4),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        self.log.debug(f'Generated TTP table with {len(ttp_data)-1} tactics')

        return tbl

    # ---------- small helpers ----------
    @staticmethod
    def _stacked(lines, *, html=False):
        '''
        Join a list of strings into a single Paragraph body with <br/>.
        If html=True, assume strings already contain reportlab para XML (e.g., <link>).
        '''
        if html:
            # DO NOT escape – preserve tags like <link href="#AN-0006">AN-0006</link>
            clean = [str(s or '') for s in (lines or [])]
        else:
            # Safe text mode
            clean = [escape(str(s or '')) for s in (lines or [])]
        return '<br/>'.join(clean) or '—'

    @staticmethod
    def _anchor_for_det(det_id):
        return (det_id or '').upper().replace('DET-', 'DET')

    def _normalize_det_id(self, det_id: str, fallback=None):
        if not det_id:
            return fallback

        s = det_id.upper().replace('DET', '')
        digits = ''.join(ch for ch in s if ch.isdigit())

        if digits:
            return f'DET{digits}'  # <-- NO DASH
        return fallback
