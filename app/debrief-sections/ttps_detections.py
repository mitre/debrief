import logging
import re

from collections import defaultdict, OrderedDict
from reportlab.lib import colors

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, PageBreak, Table, TableStyle
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from plugins.debrief.app.utility.base_report_section import BaseReportSection


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'ttps-detections'
        self.display_name = 'Detection Strategies'
        self.section_title = 'TTPs and V18 Detections for <font name=Courier-Bold size=17>%s</font>'
        self.description = 'Ordered steps (TTPs) from the operation with their associated ATT&CK v18 Detections.'
        self.log = logging.getLogger('DebriefTTPsDetectionsTable')

        if not hasattr(self, 'styles') or self.styles is None:
            self.styles = getSampleStyleSheet()

        self.DATA_COL_WIDTHS = [
            0.53*inch,  # AN
            0.60*inch,  # Platform
            2.10*inch,  # Detection Statement
            0.85*inch,  # Name
            1.10*inch,  # Channel
            1.20*inch,  # Data Component
            1.41*inch,  # Field
            1.70*inch,  # Description
        ]
        self.DATA_FULL_WIDTH = sum(self.DATA_COL_WIDTHS)
        self.cell_style = ParagraphStyle(
            name='DetectionsCell',
            parent=None,
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            wordWrap='CJK',
            spaceBefore=0,
            spaceAfter=0,
        )

    def _section_band(self, title_text: str):
        red = colors.maroon
        band = Table([[Paragraph(title_text, self.styles['Heading2'])]],
                     colWidths=[self.DATA_FULL_WIDTH], hAlign='CENTER')
        band.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), red),
            ('TEXTCOLOR',     (0, 0), (-1, -1), colors.whitesmoke),
            ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 14),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return band

    def _p(self, text: str):
        text = str(text or '')

        # Light escape to avoid accidental tag parsing
        text = (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))
        return Paragraph(text, self.cell_style)

    def _ensure_styles(self):
        '''(Re)ensure custom styles exist on the CURRENT stylesheet instance.'''
        if not hasattr(self, 'styles') or self.styles is None:
            self.styles = getSampleStyleSheet()

        # If the stylesheet object changed since last time, force a rebuild.
        if getattr(self, '_style_sheet_id', None) != id(self.styles):
            self._styles_init = False
            self._style_sheet_id = id(self.styles)

        if getattr(self, '_styles_init', False):
            # Even if marked init'd, verify the named styles exist on THIS stylesheet.
            # If any are missing (e.g., new stylesheet), clear the flag and rebuild.
            needed = {'HdrTitle', 'HdrMeta', 'HdrBand'}
            have = set(getattr(self.styles, 'byName', {}) or {})
            if not needed.issubset(have):
                self._styles_init = False

        if self._styles_init:
            return

        base = self.styles['Normal']

        # --- Body paragraph styles used in tables ---
        # Left-aligned body cell (used for AN labels, etc.)
        self.sty_cell = ParagraphStyle(
            'det-cell',
            parent=base,
            fontName='Helvetica',
            fontSize=8,
            leading=9.5,
            spaceBefore=0, spaceAfter=0,
            alignment=TA_LEFT,
        )
        # Centered body cell (platform, statement center variants, etc.)
        self.sty_cell_center = ParagraphStyle(
            'det-cell-center',
            parent=base,
            fontName='Helvetica',
            fontSize=8,
            leading=9.5,
            spaceBefore=0, spaceAfter=0,
            alignment=TA_CENTER,
        )

        # --- Header band styles used by _build_det_header_block ---
        if 'HdrTitle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='HdrTitle', parent=base,
                fontName='Helvetica-Bold', fontSize=14, leading=13, alignment=1,
                textColor=colors.whitesmoke, spaceBefore=0, spaceAfter=0
            ))
        if 'HdrMeta' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='HdrMeta', parent=base,
                fontName='Helvetica', fontSize=8, leading=9,
                textColor=colors.whitesmoke, spaceBefore=0, spaceAfter=0
            ))
        if 'HdrBand' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='HdrBand', parent=base,
                fontName='Helvetica-Bold', fontSize=10, leading=11, alignment=1,
                textColor=colors.whitesmoke, spaceBefore=0, spaceAfter=0
            ))

        self._styles_init = True

    async def generate_section_elements(self, styles, **kwargs):
        '''
        Build the Detections section pages. This method is required by the GUI to
        collect flowables for each report section.
        '''
        self.styles = styles or getattr(self, 'styles', None) or getSampleStyleSheet()
        self._ensure_styles()

        flows = []
        operations = kwargs.get('operations', [])
        if not operations:
            return flows

        op_name = (getattr(operations[0], 'name', None) or 'Operation').strip()
        flows.append(self._section_band(f'Detections for {op_name}'))

        # Add the intro paragraph here (not per DET)
        flows.append(Paragraph(
            'This section lists mapping of Analytic Elements to Data Components and their tunable fields for the selected operation.',
            ParagraphStyle(
                name='DetectionsIntro',
                parent=self.styles['Normal'],
                fontName='Helvetica',
                fontSize=9,
                leading=11,
                alignment=TA_CENTER,
                spaceBefore=6,
                spaceAfter=10,
            )
        ))

        agents = kwargs.get('agents', []) or []
        paw_to_platform = {getattr(a, 'paw', None): getattr(a, 'platform', None) for a in agents}
        self.log.debug(f'[DET] agents={len(agents)} paw_to_platform={paw_to_platform}')

        for i, op in enumerate(operations):
            if i > 0:
                flows.append(PageBreak())
            flows.extend(self._generate_detection_appendix(op, paw_to_platform))

        return flows

    @staticmethod
    def _get_op_platforms_and_tids(operation, paw_to_platform):
        tid_to_platforms = defaultdict(set)
        tids = set()

        for link in getattr(operation, 'chain', []) or []:
            if getattr(link, 'cleanup', False):
                continue

            tid = getattr(getattr(link, 'ability', None), 'technique_id', '').strip().upper()
            if not tid:
                continue

            plat = paw_to_platform.get(getattr(link, 'paw', None), '').lower()

            if plat:
                tid_to_platforms[tid].add(plat)
            tids.add(tid)

        return (tid_to_platforms, tids)

    def _get_technique_detection_refs(self, tid):
        # Try each exact sub-technique first; fall back to parent if none hit
        refs = self._build_detection_refs(tid)
        if not refs:
            # Fall back to parent
            ptid = tid.split('.')[0].strip().upper()
            if ptid != tid:
                refs = self._build_detection_refs(ptid)
                if refs:
                    self.log.debug(f'Fell back to parent TID: {ptid}')
        return refs

    def _build_det_appendix_rows(self, ref, platforms):
        det_id = ref['det_id']
        tid = ref['tid']

        # header rows
        rows = [
            [
                'AN', 'Platform', 'Detection Statement',
                'Data Component Elements (DC)', '', '',
                'Mutable Elements', ''
            ],
            ['', '', '', 'Name', 'Channel', 'Data Component', 'Field', 'Description']
        ]

        an_ids = set()
        seen_rows = set()

        # --------------------------------------------------------------
        # analytics_by_plat uses EXACT technique IDs
        # --------------------------------------------------------------
        analytics_by_plat = OrderedDict()
        for plat in platforms:
            analytics_by_plat[plat] = self._a18.get_analytics(tid, platform=plat) or []

        # --------------------------------------------------------------
        # Process analytic rows for this DET
        # --------------------------------------------------------------
        for plat, analytics in analytics_by_plat.items():
            self.log.debug(f'[DET] analytics for {tid} plat={plat} → {len(analytics)} rows')

            for a_row in analytics:
                an_id = a_row.get('an_id')
                if not an_id:
                    self.log.warn(f'No analytic ID found for analytic object: {a_row.get('id')}')
                    continue

                self.log.debug(f'  [DET] row det_id={a_row.get('det_id')} an_id={an_id} tech={tid}')
                row_det_id = a_row.get('det_id', '').strip()

                # DET matching logic
                if row_det_id:
                    if row_det_id != det_id:
                        self.log.warn(f'Mismatching analytic detection ID {row_det_id} and referenced detection ID {det_id}')
                        continue
                else:
                    self.log.warn(f'Did not find detection ID for analytic {an_id}')
                    continue

                stmt = Paragraph(
                    (str(a_row.get('statement', '') or '')
                        .replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')),
                    self.sty_cell_center,
                )

                # ensure platform filled for AN mapping
                if plat and not a_row.get('platform'):
                    a_row = dict(a_row)
                    a_row['platform'] = plat

                an_ids.add(an_id)
                plat_disp = (plat or a_row.get('platform', '') or '').capitalize()
                an_cell = Paragraph(an_id, self.sty_cell_center)
                plat_cell = Paragraph(plat_disp, self.sty_cell_center)

                dcs = a_row.get('dc_elements') or [{}]
                tuns = a_row.get('tunables') or [None]

                for d in dcs:
                    dc_name = d.get('name', '')
                    dc_chan = d.get('channel', '')
                    dc_comp = d.get('data_component', '')

                    for t in tuns:
                        if t is None:
                            field_val = ''
                            desc_val = ''
                        else:
                            field_val = t.get('field', '').strip()
                            desc_val = t.get('description', '').strip()

                        key = (an_id, plat_disp, dc_name, field_val, dc_chan)
                        if key in seen_rows:
                            continue
                        seen_rows.add(key)

                        rows.append([
                            an_cell, plat_cell, stmt,
                            self._p(dc_name), self._p(dc_chan), self._p(dc_comp),
                            self._p(field_val), self._p(desc_val)
                        ])

        self.log.debug(f'[ANs] for {det_id}: {sorted(an_ids)}')
        return rows, an_ids

    def _generate_detection_appendix(self, operation, paw_to_platform):
        flows = []
        self._ensure_styles()

        # Collect platforms and TID → sub-technique TIDs used in operation
        tid_to_platforms, tids = self._get_op_platforms_and_tids(operation, paw_to_platform)

        # For EACH (sub)technique, build DET appendix
        for tid in sorted(tids):
            self.log.debug(f'[DET] Building DET appendix for technique {tid}')

            # Determine platforms used for this technique
            observed_platforms = sorted(tid_to_platforms.get(tid, []))

            self.log.debug(f'[DET] Using observed platforms for technique: {observed_platforms}')

            refs = self._get_technique_detection_refs(tid)
            if not refs:
                self.log.warn(f'[DET] No detection strategies found for TID {tid} or parent)')
                continue

            self.log.debug(f'[DET] Built {len(refs)} unique detection strategy references for TID {tid}')

            # ------------------------------------------------------------------
            # Build appendix table PER DET strategy
            # ------------------------------------------------------------------
            processed_refs = set()
            for ref in refs:
                det_id = ref.get('det_id', '')
                det_name = ref.get('det_name', '')
                if not det_id or det_id in processed_refs:
                    continue

                processed_refs.add(det_id)
                rows, an_ids = self._build_det_appendix_rows(ref, observed_platforms)

                if len(rows) <= 2:
                    rows.append(['', '', self._p('No analytics for the selected OS scope.'), '', '', '', '', ''])

                tbl = self._build_det_table(rows)
                tbl.spaceBefore = 0
                tbl.spaceAfter = 0

                flows.append(Paragraph(f'<a name="{det_id}"></a>', self.styles['Normal']))
                hdr_block = self._build_det_header_block(det_id, det_name, sorted(an_ids))
                flows.append(KeepTogether(hdr_block + [tbl]))
        return flows

    def _build_det_header_block(self, det_id: str, det_name: str, an_ids: list[str]):
        self._ensure_styles()
        flows = []

        full_w = self.DATA_FULL_WIDTH
        left_w = full_w * 0.5
        right_w = full_w * 0.5
        det_anchor = (det_id or '').replace(':', '-')
        flows.append(Paragraph(f'<a name="{det_anchor}"></a>', self.styles['Normal']))
        left_title = Paragraph('Detection Strategies', self.styles['HdrTitle'])

        # Right gray meta table (with white horizontal rules)
        meta_rows = [
            [Paragraph(f'Detection Strategy ID ({det_id})', self.styles['HdrMeta'])],
            [Paragraph(f'Detection Strategy Name ({det_name})', self.styles['HdrMeta'])],
            [Paragraph(self._format_an_range(list(an_ids or [])), self.styles['HdrMeta'])],
        ]
        meta_tbl = Table(meta_rows, colWidths=[right_w], hAlign='CENTER')
        meta_gray = colors.Color(0.35, 0.35, 0.35)
        meta_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), meta_gray),
            ('TEXTCOLOR',     (0, 0), (-1, -1), colors.whitesmoke),
            ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
            ('TOPPADDING',    (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            # white horizontal separators between the three gray rows
            ('LINEBELOW',     (0, 0), (0, 0), 0.6, colors.whitesmoke),
            ('LINEBELOW',     (0, 1), (0, 1), 0.6, colors.whitesmoke),
            # no border; let the maroon band touch without a white seam
            ('BOX',           (0, 0), (-1, -1), 0, colors.transparent),
            ('INNERGRID',     (0, 0), (-1, -1), 0, colors.transparent),
        ]))

        red = colors.maroon
        band = Paragraph('Analytic Elements', self.styles['HdrBand'])

        hdr = Table(
            [[left_title, meta_tbl], [band, '']],
            colWidths=[left_w, right_w],
            hAlign='CENTER'
        )
        hdr.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (0, 0), colors.black),
            ('TEXTCOLOR',     (0, 0), (0, 0), colors.whitesmoke),
            ('ALIGN',         (0, 0), (0, 0), 'CENTER'),
            ('VALIGN',        (0, 0), (0, 0), 'MIDDLE'),  # center vertically; fixes “padding at top” feel
            # zero outer padding so widths line up with data table
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            # full-width maroon band
            ('SPAN',        (0, 1), (1, 1)),
            ('BACKGROUND',  (0, 1), (1, 1), red),
            ('TEXTCOLOR',   (0, 1), (1, 1), colors.whitesmoke),
            ('FONTNAME',    (0, 1), (1, 1), 'Helvetica-Bold'),
            ('ALIGN',       (0, 1), (1, 1), 'CENTER'),
            ('VALIGN',      (0, 1), (1, 1), 'MIDDLE'),
            # no borders
            ('BOX',         (0, 0), (-1, -1), 0, colors.transparent),
            ('INNERGRID',   (0, 0), (-1, -1), 0, colors.transparent),

            ('BOX',         (0, 0), (-1, -1), 0, colors.transparent),
            ('INNERGRID',   (0, 0), (-1, -1), 0, colors.transparent),
        ]))

        hdr.spaceBefore = 0
        hdr.spaceAfter = 0
        flows.append(hdr)
        return flows

    def _build_det_table(self, rows, span_cmds=None):
        '''
        Build the 8-column detections table with MITRE-style formatting.

        Enhancements over default ReportLab tables:
        --------------------------------------------------------------
        • Automatically collapses repeated values in the first three
          columns (AN, Platform, Detection Statement) by applying
          vertical row-spans. This matches historical ATT&CK PDF
          formatting and prevents excessive repetition.

        • Header rows (0-1) are preserved; row-spanning starts from
          the first data row (index 2).

        • `span_cmds` allows additional external SPAN rules, but the
          function now auto-generates the crucial row-spans needed
          for a clean table layout.

        Arguments:
        -----------
        rows : list[list]
            Full table row data including 2 header rows.
        span_cmds : list[tuple] | None
            Additional ReportLab TableStyle SPAN directives.

        Returns:
        --------
        Table
            Styled ReportLab Table instance ready to insert into PDF.
        '''
        span_cmds = span_cmds or []

        # ------------------------------------------------------------------
        # AUTO-GENERATE ROW SPANS FOR IDENTICAL CELL VALUES
        # ------------------------------------------------------------------
        start = 2                     # row 0–1 = header rows
        end = len(rows)
        valign_cmds = []              # stores ('VALIGN', (col,r1),(col,r2),'MIDDLE')

        def _add_spans_for_column(col_idx):
            '''
            Detect consecutive identical values in rows[col_idx],
            SPAN them, and emit a VALIGN rule to center vertically.
            '''
            r = start
            while r < end:
                r_start = r
                cell = rows[r][col_idx]

                # Find the consecutive matching block
                while r + 1 < end and rows[r + 1][col_idx] == cell:
                    r += 1

                if r > r_start:  # spanning required
                    span_cmds.append(('SPAN', (col_idx, r_start), (col_idx, r)))
                    valign_cmds.append(('VALIGN', (col_idx, r_start), (col_idx, r), 'MIDDLE'))
                r += 1

        # Spanning for AN / Platform / Statement
        _add_spans_for_column(0)
        _add_spans_for_column(1)
        _add_spans_for_column(2)

        # ------------------------------------------------------------------
        # BUILD TABLE
        # ------------------------------------------------------------------
        tbl = Table(
            rows,
            colWidths=self.DATA_COL_WIDTHS,
            repeatRows=2,
            hAlign='CENTER'
        )

        # Base styling (unchanged from your version)
        base_style = [
            # --- Row 0 main headers ---
            ('SPAN',       (3, 0), (5, 0)),
            ('SPAN',       (6, 0), (7, 0)),
            ('BACKGROUND', (0, 0), (7, 0), colors.maroon),
            ('FONTNAME',   (0, 0), (7, 0), 'Helvetica-Bold'),
            ('ALIGN',      (0, 0), (7, 0), 'CENTER'),
            ('VALIGN',     (0, 0), (7, 0), 'MIDDLE'),
            ('TEXTCOLOR',  (0, 0), (7, 0), colors.whitesmoke),

            # --- Row 1 secondary headers ---
            ('SPAN',       (0, 0), (0, 1)),
            ('SPAN',       (1, 0), (1, 1)),
            ('SPAN',       (2, 0), (2, 1)),
            ('BACKGROUND', (0, 0), (2, 1), colors.maroon),
            ('TEXTCOLOR',  (0, 0), (2, 1), colors.whitesmoke),
            ('FONTNAME',   (0, 0), (2, 1), 'Helvetica-Bold'),

            ('BACKGROUND', (3, 1), (5, 1), colors.maroon),
            ('BACKGROUND', (6, 1), (7, 1), colors.maroon),
            ('TEXTCOLOR',  (3, 1), (7, 1), colors.whitesmoke),
            ('FONTNAME',   (0, 1), (7, 1), 'Helvetica-Bold'),
            ('ALIGN',      (0, 1), (7, 1), 'CENTER'),
            ('VALIGN',     (0, 1), (7, 1), 'MIDDLE'),

            # Body cell defaults
            ('TOPPADDING', (0, 2), (7, 2), 0),
            ('VALIGN',     (0, 2), (7, -1), 'TOP'),
            ('TEXTCOLOR',  (0, 2), (7, -1), colors.black),

            ('BOX',        (0, 0), (7, -1), 0.75, colors.black),
            ('INNERGRID',  (0, 0), (7, -1), 0.25, colors.black),

            ('LEFTPADDING',   (0, 0), (7, -1), 4),
            ('RIGHTPADDING',  (0, 0), (7, -1), 4),
            ('BOTTOMPADDING', (0, 0), (7, -1), 2),
        ]

        # Insert generated spans + valign rules
        base_style.extend(span_cmds)
        base_style.extend(valign_cmds)

        tbl.setStyle(TableStyle(base_style))
        tbl.spaceBefore = 0
        tbl.spaceAfter = 0
        return tbl

    def _build_detection_refs(self, tid: str) -> list[dict]:
        '''
        Return a list of dicts for unique detection strategies relevant to `tid`.
        Each item in the returned list has:
        - 'strategy' : the source strategy dict (with s['det_id'] stamped)
        - 'det_id'   : canonical DET####
        - 'det_name' : strategy name or det_id
        - 'tid'      : the associated technique ID
        '''
        # Use the existing single source of truth for relevance
        strategies = self._a18.get_strategies(tid)
        out, seen = [], set()
        for s in strategies:
            det_id = s.get('det_id', '').strip()
            if not det_id or det_id in seen:
                continue

            seen.add(det_id)
            ret_strat = dict(s)
            ret_strat['det_id'] = det_id
            out.append({
                'strategy': ret_strat,
                'det_id': det_id,
                'det_name': ret_strat.get('name', det_id),
                'tid': tid
            })
        return out

    def _format_an_range(self, an_ids: list[str]) -> str:
        '''Format Analytic.'''
        nums = []
        for x in an_ids:
            m = re.match(r'AN(\d{4})$', str(x).strip(), flags=re.IGNORECASE)
            if m:
                nums.append(int(m.group(1)))
        if not nums:
            # fallback: show unique AN ids joined
            uniq = sorted(set(filter(None, an_ids)))
            return f'Analytic ( {', '.join(uniq) if uniq else '—'} )'
        return f'Analytic ( AN{min(nums):04d} to AN{max(nums):04d} )'
