import re

from collections import OrderedDict, defaultdict
from reportlab.lib import colors

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, NextPageTemplate, PageBreak, Table, TableStyle

from plugins.debrief.app.utility.base_report_section import BaseReportSection
from plugins.debrief.attack_mapper import Attack18Map


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'ttps-detections'
        self.display_name = 'TTPs & V18 Detections'
        self.section_title = 'TTPs and V18 Detections for <font name=Courier-Bold size=17>%s</font>'
        self.description = 'Ordered steps (TTPs) from the operation with their associated ATT&CK v18 Detections.'
        self.DATA_COL_WIDTHS = [
            0.9*inch, 0.8*inch, 0.9*inch, 1.9*inch, 1.1*inch, 1.0*inch, 1.3*inch, 1.1*inch, 1.6*inch
        ]
        self.DATA_FULL_WIDTH = sum(self.DATA_COL_WIDTHS)

    async def generate_section_elements(self, styles, **kwargs):
        """
        Build the Detections section pages. This method is required by the GUI to
        collect flowables for each report section.
        """
        self.styles = styles
        flows = []

        operations = kwargs.get('operations', []) or []
        if not operations:
            return flows

        # Switch to the landscape templates for this section
        flows.append(NextPageTemplate('LandscapeFirst'))
        flows.append(PageBreak())  # start section on a new landscape page

        a18 = BaseReportSection.load_attack18()
        agents = kwargs.get('agents', []) or []
        paw_to_platform = {getattr(a, 'paw', None): getattr(a, 'platform', None) for a in agents}

        for i, op in enumerate(operations):
            if i > 0:
                # separate operations within the section
                flows.append(PageBreak())

            # (Optional) a small section heading
            flows.append(Paragraph('Detections', styles['Heading2']))

            # After the first page, use the normal landscape template
            flows.append(NextPageTemplate('Landscape'))

            # Append the detection appendix for this operation
            flows.extend(self._generate_detection_appendix(op, a18, paw_to_platform))

        return flows

    def _generate_detection_appendix(self, operation, a18: Attack18Map, paw_to_platform):
        styles = self.styles
        flows = []

        # 1) Collect platforms actually seen for each parent technique in this op
        tech_plats = defaultdict(lambda: OrderedDict())
        for link in getattr(operation, 'chain', []) or []:
            if getattr(link, 'cleanup', False):
                continue
            tid = (getattr(getattr(link, 'ability', None), 'technique_id', '') or '').strip().upper()
            if not tid:
                continue
            ptid = tid.split('.')[0]
            plat = (paw_to_platform.get(getattr(link, 'paw', None)) or '').lower()
            if ptid and plat:
                tech_plats[ptid].setdefault(plat, None)

        op_ptids = list(tech_plats.keys())
        # union of platforms used anywhere in the op (fallback to [None] if none recorded)
        op_plats = sorted(set(p for pt in op_ptids for p in tech_plats.get(pt, {}).keys())) or [None]

        # 2) Build a unique set of DET strategies across all techniques in this op
        #    Keyed by normalized det_id (DET-####); fallback to object-id tail if needed.
        det_map = OrderedDict()  # det_id -> {'obj': s, 'name': ..., 'anchor': ...}
        for ptid in op_ptids:
            for s in (a18.get_strategies(ptid) or []):
                det_id = s.get('det_id')
                if not det_id:
                    ext = next((er.get('external_id', '') for er in (s.get('external_references') or [])), '')
                    m = re.match(r'^DET-?(\d{4})$', str(ext).strip(), flags=re.IGNORECASE)
                    det_id = f"DET-{m.group(1)}" if m else (s.get('id', '')[-8:] or '')
                if det_id not in det_map:
                    det_map[det_id] = {
                        'obj': s,
                        'name': s.get('name') or det_id,
                        'anchor': det_id.replace(':', '-'),
                    }

        # 3) Render one appendix block per DET (not per technique)
        for det_id, info in det_map.items():
            det_anchor = info['anchor']
            det_name = info['name']

            # Anchor + styled header block
            flows.append(Paragraph(f'<a name="{det_anchor}"/>', styles['Normal']))

            # Collect AN ids for this DET (for the gray “Analytic (AN-xxxx to AN-xxxx)” line)
            _an_ids = set()

            # Build data table header with grouped spans like the screenshot
            rows = []

            # Level-1 header row
            rows.append(['ID', 'AN', 'Platform', 'Detection Statement',
                         'Data Component (DC) Elements', '', '',
                         'Mutable Elements', ''])

            # Level-2 header row (subheaders)
            rows.append(['',  '',  '',  '',
                         'Name', 'Channel', 'Data Component (DC)',
                         'Field', 'Description'])

            # 3a) Gather analytics linked to ANY technique used in this op,
            #     but keep only analytics stamped with this det_id (attack_mapper sets arow['det_id'])
            seen_rows = set()  # (an, plat, dc_name, field, dc_chan)
            for plat in op_plats:
                op_analytics = []
                for ptid in op_ptids:
                    op_analytics.extend(a18.get_analytics(ptid, platform=plat) or [])

                for arow in op_analytics:
                    if (arow.get('det_id') or det_id) != det_id:
                        continue  # only show analytics for this DET

                    # IDs
                    det = det_id
                    an = arow.get('an_id') or (arow.get('id', '')[-8:] or '')
                    _an_ids.add(an)
                    plat_disp = (plat or arow.get('platform', '') or '').capitalize()
                    stmt = arow.get('statement', '') or ''
                    dcs = arow.get('dc_elements') or [{}]
                    tuns = arow.get('tunables') or [{}]

                    # Expand DC × Tunables
                    for d in dcs:
                        dc_name = d.get('name', '')
                        dc_chan = d.get('channel', '')
                        dc_comp = d.get('data_component', '')

                        if not tuns:
                            key = (an, plat_disp, dc_name, '', dc_chan)
                            if key in seen_rows:
                                continue
                            seen_rows.add(key)
                            rows.append([det, an, plat_disp, stmt, dc_name, dc_chan, dc_comp, '', ''])
                        else:
                            for t in tuns:
                                field = (t.get('field') if isinstance(t, dict) else str(t)) or ''
                                desc = (t.get('description') if isinstance(t, dict) else '') or ''
                                key = (an, plat_disp, dc_name, field, dc_chan)
                                if key in seen_rows:
                                    continue
                                seen_rows.add(key)
                                rows.append([det, an, plat_disp, stmt, dc_name, dc_chan, dc_comp, field, desc])

            flows.extend(self._build_det_header_block(det_id, det_name, sorted(_an_ids)))
            # Build the table with your existing column widths
            tbl = Table(
                rows,
                colWidths=self.DATA_COL_WIDTHS
            )

            # TableStyle
            header_bg = colors.Color(0.95, 0.45, 0.30)  # orange/red row background (tweak)
            tbl_style = TableStyle([
                # Header backgrounds
                ('BACKGROUND', (0, 0), (-1, 0), header_bg),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                ('BACKGROUND', (0, 1), (-1, 1), header_bg),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.whitesmoke),
                ('ALIGN', (0, 1), (-1, 1), 'CENTER'),

                # Spans
                ('SPAN', (0, 0), (0, 1)),  # ID
                ('SPAN', (1, 0), (1, 1)),  # AN
                ('SPAN', (2, 0), (2, 1)),  # Platform
                ('SPAN', (3, 0), (3, 1)),  # Detection Statement
                ('SPAN', (4, 0), (6, 0)),  # Data Component (DC) Elements (3 cols)
                ('SPAN', (7, 0), (8, 0)),  # Mutable Elements (2 cols)

                # Grid/padding
                ('BOX',           (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID',     (0, 0), (-1, -1), 0.25, colors.black),
                ('LEFTPADDING',   (0, 0), (-1, -1), 4),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
                ('TOPPADDING',    (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ])

            tbl.setStyle(tbl_style)
            flows.append(tbl)

        return flows

    def _generate_op_detections_table(self, operation, a18: Attack18Map, paw_to_platform):
        data = [['Technique', 'Ability', 'Detections (ATT&CK v18)']]

        # Collect abilities + platforms per technique
        tech_map = {}  # (ptid, tname) -> {'abilities': OrderedDict(), 'platforms': OrderedDict()}
        for link in getattr(operation, 'chain', []) or []:
            if getattr(link, 'cleanup', False):
                continue
            ab = getattr(link, 'ability', None)
            tid = (getattr(ab, 'technique_id', '') or '').strip().upper()
            tname = (getattr(ab, 'technique_name', '') or '').strip()
            ability = (getattr(ab, 'name', '') or '').strip()
            parent_tid = tid.split('.')[0] if tid else ''
            platform = (paw_to_platform.get(getattr(link, 'paw', None)) or '').lower()

            key = (parent_tid or '—', tname or '—')
            if key not in tech_map:
                tech_map[key] = {'abilities': OrderedDict(), 'platforms': OrderedDict()}
            if platform:
                tech_map[key]['platforms'].setdefault(platform, None)
            if ability:
                tech_map[key]['abilities'].setdefault(ability, None)

        # Emit rows (Technique shown once; all abilities underneath)
        for (ptid, tname) in sorted(tech_map.keys(), key=lambda k: (k[0], k[1])):
            bucket = tech_map[(ptid, tname)]
            abilities = list(bucket['abilities'].keys()) or ['—']

            # Build linked strategy refs once per technique
            det_refs = self._build_detection_refs(ptid, a18, list(bucket.get('platforms', {}).keys()))
            if det_refs:
                links = [f'<link href="#{did}">{did}</link>: {nm}' for did, nm in det_refs]
                detect_cell = Paragraph(", ".join(links), self.styles['Normal'])
            else:
                detect_cell = Paragraph("No mapped analytics", self.styles['Normal'])

            for idx, ability in enumerate(abilities):
                tech_cell = f"{ptid} {tname}".strip() if idx == 0 else ''
                det_out = detect_cell if idx == 0 else ''
                data.append([tech_cell, ability or '—', det_out])

        # 3 columns → set 3 widths
        return self.generate_table(data, [2.4 * inch, 2.0 * inch, 2.9 * inch])

    def _build_detection_refs(self, ptid: str, a18: Attack18Map, platforms: list[str]) -> list[tuple[str, str]]:
        """Return [(det_id, det_name)] for strategies detecting ptid.
        det_id is used as an in-PDF anchor (e.g., 'DET-0001').
        If the bundle lacks DET IDs, fall back to the object UUID last 8 chars."""
        strategies = a18.get_strategies(ptid) or []
        out = []
        for s in strategies:
            det_id = s.get('id') or ''
            # Prefer human-friendly external IDs if present
            ext = next((er.get('external_id') for er in s.get('external_references', []) or []
                        if er.get('external_id', '').startswith('DET-')), None)
            if ext:
                det_id = ext
            # anchor-safe id
            det_anchor = (det_id or (s.get('id', '')[-8:]) or f"DET-{ptid}").replace(':', '-')
            out.append((det_anchor, s.get('name') or det_id))
        return out

    def _format_an_range(self, an_ids: list[str]) -> str:
        """Format 'Analytic ( AN-0001 to AN-0005 )' from a list like ['AN-0001','AN-0003',...]."""
        nums = []
        for x in an_ids:
            m = re.match(r'AN-?(\d{4})$', str(x).strip(), flags=re.IGNORECASE)
            if m:
                nums.append(int(m.group(1)))
        if not nums:
            # fallback: show unique AN ids joined
            uniq = sorted(set(filter(None, an_ids)))
            return f"Analytic ( {', '.join(uniq) if uniq else '—'} )"
        return f"Analytic ( AN-{min(nums):04d} to AN-{max(nums):04d} )"

    def _build_det_header_block(self, det_id: str, det_name: str, an_ids: list[str]):
        """Return [Flowables] that render the black bar, gray 3-line meta, and the red 'Analytic Elements' band."""
        flows = []

        # 1) Black title bar: "Detection Strategy Elements"
        black = Table([[Paragraph('<b><font color="white">Detection Strategy Elements</font></b>', self.styles['Heading3'])]],
                      colWidths=[self.DATA_FULL_WIDTH])
        black.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        flows.append(black)

        # 2) Gray 3-line meta block (DET ID, Name, Analytic range)
        meta = Table([
            [Paragraph(f'Detection Strategy ID ({det_id})', self.styles['Normal'])],
            [Paragraph(f'Detection Strategy Name ( {det_name} )', self.styles['Normal'])],
            [Paragraph(self._format_an_range(list(an_ids or [])), self.styles['Normal'])]
        ], colWidths=[self.DATA_FULL_WIDTH])

        gray = colors.Color(0.35, 0.35, 0.35)
        meta.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), gray),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        flows.append(meta)

        # 3) Red "Analytic Elements" band (single cell, spans full width of data table)
        redband = Table(
            [[Paragraph('<b>Analytic Elements</b>', self.styles['Normal'])]],
            colWidths=[self.DATA_FULL_WIDTH]   # the same width as the data table
        )
        red = colors.Color(0.85, 0.25, 0.20)  # tweak to taste
        redband.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), red),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        flows.append(redband)

        return flows
