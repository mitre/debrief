import re

from collections import OrderedDict, defaultdict
from reportlab.lib import colors

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, PageBreak, Table, TableStyle
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from plugins.debrief.app.utility.base_report_section import BaseReportSection
from plugins.debrief.attack_mapper import get_attack18


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'ttps-detections'
        self.display_name = 'TTPs & V18 Detections'
        self.section_title = 'TTPs and V18 Detections for <font name=Courier-Bold size=17>%s</font>'
        self.description = 'Ordered steps (TTPs) from the operation with their associated ATT&CK v18 Detections.'
        self._a18 = get_attack18()
        self._emitted_anchors = set() 
        if not hasattr(self, "styles") or self.styles is None:
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
            name="DetectionsCell",
            parent=None,
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            wordWrap="CJK",
            spaceBefore=0,
            spaceAfter=0,
        )
    
    def _section_band(self, title_text: str):
        red = colors.maroon
        band = Table([[Paragraph(title_text, self.styles['Heading2'])]],
                    colWidths=[self.DATA_FULL_WIDTH], hAlign='CENTER')
        band.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), red),
            ('TEXTCOLOR',  (0,0), (-1,-1), colors.whitesmoke),
            ('FONTNAME',   (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 14),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('LEFTPADDING',(0,0), (-1,-1), 0),
            ('RIGHTPADDING',(0,0),(-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ]))
        return band

    def _p(self, text: str):
        text = str(text or "")
        # Light escape to avoid accidental tag parsing
        text = (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
        return Paragraph(text, self.cell_style)

    def _ensure_styles(self):
        """(Re)ensure custom styles exist on the CURRENT stylesheet instance."""
        if not hasattr(self, "styles") or self.styles is None:
            self.styles = getSampleStyleSheet()

        # If the stylesheet object changed since last time, force a rebuild.
        if getattr(self, "_style_sheet_id", None) != id(self.styles):
            self._styles_init = False
            self._style_sheet_id = id(self.styles)

        if getattr(self, "_styles_init", False):
            # Even if marked init'd, verify the named styles exist on THIS stylesheet.
            # If any are missing (e.g., new stylesheet), clear the flag and rebuild.
            needed = {"HdrTitle", "HdrMeta", "HdrBand"}
            have = set(getattr(self.styles, "byName", {}) or {})
            if not needed.issubset(have):
                self._styles_init = False

        if self._styles_init:
            return

        base = self.styles["Normal"]

        # --- Body paragraph styles used in tables ---
        # Left-aligned body cell (used for AN labels, etc.)
        self.sty_cell = ParagraphStyle(
            "det-cell",
            parent=base,
            fontName="Helvetica",
            fontSize=8,
            leading=9.5,
            spaceBefore=0, spaceAfter=0,
            alignment=TA_LEFT,
        )
        # Centered body cell (platform, statement center variants, etc.)
        self.sty_cell_center = ParagraphStyle(
            "det-cell-center",
            parent=base,
            fontName="Helvetica",
            fontSize=8,
            leading=9.5,
            spaceBefore=0, spaceAfter=0,
            alignment=TA_CENTER,
        )

        # --- Header band styles used by _build_det_header_block ---
        if "HdrTitle" not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='HdrTitle', parent=base,
                fontName='Helvetica-Bold', fontSize=14, leading=13, alignment=1,
                textColor=colors.whitesmoke, spaceBefore=0, spaceAfter=0
            ))
        if "HdrMeta" not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='HdrMeta', parent=base,
                fontName='Helvetica', fontSize=8, leading=9,
                textColor=colors.whitesmoke, spaceBefore=0, spaceAfter=0
            ))
        if "HdrBand" not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='HdrBand', parent=base,
                fontName='Helvetica-Bold', fontSize=10, leading=11, alignment=1,
                textColor=colors.whitesmoke, spaceBefore=0, spaceAfter=0
            ))

        self._styles_init = True

    async def generate_section_elements(self, styles, **kwargs):
        """
        Build the Detections section pages. This method is required by the GUI to
        collect flowables for each report section.
        """
        self.styles = styles or getattr(self, "styles", None) or getSampleStyleSheet()
        self._ensure_styles()

        flows = []

        operations = kwargs.get('operations', []) or []
        if not operations:
            return flows
        
        if not getattr(self, "_section_band_added", False):
            op_name = (getattr(operations[0], 'name', None) or 'Operation').strip()
            flows.append(self._section_band(f"Detections for {op_name}"))

            # Add the one-time intro paragraph here (not per DET)
            flows.append(Paragraph(
                "This section lists mapping of Analytic Elements to Data Components and their tunable fields for the selected operation.",
                ParagraphStyle(
                    name="DetectionsIntro",
                    parent=self.styles["Normal"],
                    fontName="Helvetica",
                    fontSize=9,
                    leading=11,
                    alignment=TA_CENTER,
                    spaceBefore=6,
                    spaceAfter=10,
                )
            ))

            self._section_band_added = True

        agents = kwargs.get('agents', []) or []
        paw_to_platform = {getattr(a, 'paw', None): getattr(a, 'platform', None) for a in agents}
        run_platforms = sorted({
            str(getattr(a, 'platform', '') or '').strip().lower()
            for a in agents if getattr(a, 'platform', None)
        })
        print(f"[DET] agents={len(agents)} run_platforms={run_platforms}")
        for i, op in enumerate(operations):
            if i > 0:
                flows.append(PageBreak())
            flows.extend(self._generate_detection_appendix(op, self._a18, paw_to_platform, run_platforms=run_platforms))

        return flows

    def _generate_detection_appendix(self, operation, a18, paw_to_platform, run_platforms=None):
        styles = self.styles
        flows = []
        self._ensure_styles()
        run_platforms = (run_platforms or [])

        # 1) Collect platforms and TID → sub-technique TIDs used in operation
        tech_plats = defaultdict(lambda: OrderedDict())
        ptid_to_tids = defaultdict(set)

        for link in getattr(operation, 'chain', []) or []:
            if getattr(link, 'cleanup', False):
                continue

            tid = (getattr(getattr(link, 'ability', None), 'technique_id', '') or '').strip().upper()
            if not tid:
                continue

            ptid = tid.split('.')[0]       # parent TID
            plat = (paw_to_platform.get(getattr(link, 'paw', None)) or '').lower()

            tech_plats[ptid].setdefault((plat or None), None)
            ptid_to_tids[ptid].add(tid)

        print("[DET] op:", getattr(operation, "name", "?"), "ptids:", list(tech_plats.keys()))

        # ----------------------------------------------------------------------
        # For EACH parent technique, build DET appendix
        # ----------------------------------------------------------------------
        for ptid, _plats in tech_plats.items():
            exact_tids = sorted(ptid_to_tids.get(ptid, []))
            print(f"[DET] PTID={ptid} plats={list(_plats.keys())} exact_tids={exact_tids}", flush=True)

            # Determine platforms used in operation
            if run_platforms:
                observed_plats = run_platforms[:]  # platforms from agents
            else:
                # fallback: derive from analytics across all exact technique IDs
                cache_plats = set()
                for tid in exact_tids or [ptid]:
                    for r in (self._a18.get_analytics(tid, platform=None) or []):
                        cache_plats.update(p.lower() for p in (r.get('platforms') or []) if p)
                        sp = (r.get('platform') or '').strip().lower()
                        if sp:
                            cache_plats.add(sp)
                observed_plats = sorted(cache_plats)

                        # What we iterate to render rows (at least once)
            plats_iter = observed_plats or [None]
            plats_filter = observed_plats
            print(f"[DET] Using plats_iter={plats_iter} plats_filter={plats_filter}")

            # Try each exact sub-technique first; fall back to parent if none hit
            tids = list(ptid_to_tids.get(ptid, [])) or [ptid]
            chosen_tid = None
            refs = []

            for exact_tid in tids + [ptid]:
                refs = self._build_detection_refs(ptid, a18, plats_iter, tid=exact_tid)
                if refs:
                    chosen_tid = exact_tid
                    break

            if not refs:
                print(f"[DET] No detection refs for ptid={ptid} (tids={tids})")
                continue

            print(f"[DET] Built {len(refs)} unique detection refs for ptid={ptid} (chosen_tid={chosen_tid})")

            # ------------------------------------------------------------------
            # Build appendix table PER DET strategy
            # ------------------------------------------------------------------
            for ref in refs:
                s = ref["strategy"]
                det_id = ref["det_id"]
                det_name = ref["det_name"]

                print(f"[DET] {det_id} — {det_name} (ptid={ptid}, plats={list(plats_iter)})")

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
                analytics_by_plat = {}

                for plat in plats_iter:
                    merged = []
                    for t in exact_tids or [ptid]:
                        merged.extend(self._a18.get_analytics(t, platform=plat) or [])
                    analytics_by_plat[plat] = merged

                # --------------------------------------------------------------
                # Process analytic rows for this DET
                # --------------------------------------------------------------
                for plat, analytics in analytics_by_plat.items():
                    print(f"[DET] analytics for {ptid}/{exact_tids} plat={plat} → {len(analytics)} rows")

                    for arow in analytics:
                        print(f"  [DET] row det_id={arow.get('det_id')} an_id={arow.get('an_id')} tech={arow.get('technique_id')}")

                        row_det = (arow.get("det_id") or "").strip()
                        row_det_norm = self._normalize_det_id(row_det, fallback=row_det)
                        det_norm = self._normalize_det_id(det_id, fallback=det_id)
                        sid = (s.get("id") or "").strip()

                        # DET matching logic
                        if row_det:
                            if not (row_det_norm == det_norm or row_det == sid):
                                continue
                        else:
                            if sid:
                                continue

                        plat_disp = (plat or arow.get("platform", "") or "").capitalize()

                        stmt = Paragraph(
                            (str(arow.get("statement", "") or "")
                                .replace("&", "&amp;")
                                .replace("<", "&lt;")
                                .replace(">", "&gt;")),
                            self.sty_cell_center,
                        )

                        # ensure platform filled for AN mapping
                        if plat and not arow.get("platform"):
                            arow = dict(arow)
                            arow["platform"] = plat

                        cell_label, header_an = self._extract_an_labels(arow, a18=a18, strategy=s, ptid=ptid)

                        if header_an:
                            an_ids.add(header_an)
                        elif re.match(r"^AN-?\d{4}$", cell_label, flags=re.IGNORECASE):
                            an_ids.add(self._normalize_ext_id(cell_label))

                        # anchor = self._anchor_for_an(cell_label)
                        # if cell_label not in getattr(self, "_emitted_anchors", set()):
                        #     an_cell = Paragraph(f'<a name="{anchor}"></a>{cell_label}', self.sty_cell_center)
                        #     self._emitted_anchors.add(cell_label)
                        # else:
                        an_cell = Paragraph(cell_label, self.sty_cell_center)

                        plat_cell = Paragraph(plat_disp, self.sty_cell_center)

                        dcs = arow.get("dc_elements") or [{}]
                        tuns = arow.get("tunables") or []

                        for d in (dcs or [{}]):
                            dc_name = d.get("name", "")
                            dc_chan = d.get("channel", "")
                            dc_comp = d.get("data_component", "")

                            tuns_iter = tuns if tuns else [None]
                            for t in tuns_iter:
                                if t is None:
                                    field_val = ""
                                    desc_val = ""
                                else:
                                    field_val = (t.get("field") or "").strip()
                                    desc_val = (t.get("description") or "").strip()

                                key = (cell_label, plat_disp, dc_name, field_val, dc_chan)
                                if key in seen_rows:
                                    continue
                                seen_rows.add(key)

                                rows.append([
                                    an_cell, plat_cell, stmt,
                                    self._p(dc_name), self._p(dc_chan), self._p(dc_comp),
                                    self._p(field_val), self._p(desc_val)
                                ])

                print(f"[ANs] for {det_id}: {sorted(an_ids)}")

                det_anchor = self._anchor_for_det(det_id)
                flows.append(Paragraph(f'<a name="{det_anchor}"></a>', self.styles["Normal"]))

                hdr_block = self._build_det_header_block(det_id, det_name, sorted(an_ids))

                if len(rows) <= 2:
                    rows.append(["", "", self._p("No analytics for the selected OS scope."), "", "", "", "", ""])

                tbl = self._build_det_table(rows)
                tbl.spaceBefore = 0
                tbl.spaceAfter = 0

                flows.append(KeepTogether(hdr_block + [tbl]))

        return flows

    def _build_det_header_block(self, det_id: str, det_name: str, an_ids: list[str]):
        self._ensure_styles()
        flows = []

        full_w  = self.DATA_FULL_WIDTH
        left_w  = full_w * 0.5
        right_w = full_w * 0.5
        det_anchor = (det_id or '').replace(':', '-')
        flows.append(Paragraph(f'<a name="{det_anchor}"></a>', self.styles['Normal']))
        left_title = Paragraph('Detection Strategy Elements', self.styles['HdrTitle'])

        # Right gray meta table (with white horizontal rules)
        meta_rows = [
            [Paragraph(f'Detection Strategy ID ({det_id})', self.styles['HdrMeta'])],
            [Paragraph(f'Detection Strategy Name ({det_name})', self.styles['HdrMeta'])],
            [Paragraph(self._format_an_range(list(an_ids or [])), self.styles['HdrMeta'])],
        ]
        meta_tbl = Table(meta_rows, colWidths=[right_w], hAlign='CENTER')
        meta_gray = colors.Color(0.35, 0.35, 0.35)
        meta_tbl.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), meta_gray),
            ('TEXTCOLOR',    (0,0), (-1,-1), colors.whitesmoke),
            ('FONTNAME',     (0,0), (-1,-1), 'Helvetica'),
            ('LEFTPADDING',  (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING',   (0,0), (-1,-1), 2),
            ('BOTTOMPADDING',(0,0), (-1,-1), 2),
            ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            # white horizontal separators between the three gray rows
            ('LINEBELOW',    (0,0), (0,0), 0.6, colors.whitesmoke),
            ('LINEBELOW',    (0,1), (0,1), 0.6, colors.whitesmoke),
            # no border; let the maroon band touch without a white seam
            ('BOX',          (0,0), (-1,-1), 0, colors.transparent),
            ('INNERGRID',    (0,0), (-1,-1), 0, colors.transparent),
        ]))

        red = colors.maroon
        band = Paragraph('Analytic Elements', self.styles['HdrBand'])

        hdr = Table(
            [[left_title, meta_tbl], [band, '']],
            colWidths=[left_w, right_w],
            hAlign='CENTER'
        )
        hdr.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (0,0), colors.black),
            ('TEXTCOLOR',   (0,0), (0,0), colors.whitesmoke),
            ('ALIGN',       (0,0), (0,0), 'CENTER'),
            ('VALIGN',      (0,0), (0,0), 'MIDDLE'),  # center vertically; fixes “padding at top” feel
            # zero outer padding so widths line up with data table
            ('LEFTPADDING',  (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING',   (0,0), (-1,-1), 0),
            ('BOTTOMPADDING',(0,0), (-1,-1), 0),
            # full-width maroon band
            ('SPAN',        (0,1), (1,1)),
            ('BACKGROUND',  (0,1), (1,1), red),
            ('TEXTCOLOR',   (0,1), (1,1), colors.whitesmoke),
            ('FONTNAME',    (0,1), (1,1), 'Helvetica-Bold'),
            ('ALIGN',       (0,1), (1,1), 'CENTER'),
            ('VALIGN',      (0,1), (1,1), 'MIDDLE'),
            # no borders
            ('BOX',         (0,0), (-1,-1), 0, colors.transparent),
            ('INNERGRID',   (0,0), (-1,-1), 0, colors.transparent),
            
            ('BOX',         (0,0), (-1,-1), 0, colors.transparent),
            ('INNERGRID',   (0,0), (-1,-1), 0, colors.transparent),
        ]))

        hdr.spaceBefore = 0
        hdr.spaceAfter  = 0
        flows.append(hdr)
        return flows

    def _build_det_table(self, rows, span_cmds=None):
        """
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
        """
        span_cmds = span_cmds or []

        # ------------------------------------------------------------------
        # AUTO-GENERATE ROW SPANS FOR IDENTICAL CELL VALUES
        # ------------------------------------------------------------------
        start = 2                     # row 0–1 = header rows
        end = len(rows)
        valign_cmds = []              # stores ('VALIGN', (col,r1),(col,r2),'MIDDLE')

        def add_spans_for_column(col_idx):
            """
            Detect consecutive identical values in rows[col_idx],
            SPAN them, and emit a VALIGN rule to center vertically.
            """
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
        add_spans_for_column(0)
        add_spans_for_column(1)
        add_spans_for_column(2)

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
            ('SPAN',       (3,0), (5,0)),
            ('SPAN',       (6,0), (7,0)),
            ('BACKGROUND', (0,0), (7,0), colors.maroon),
            ('FONTNAME',   (0,0), (7,0), 'Helvetica-Bold'),
            ('ALIGN',      (0,0), (7,0), 'CENTER'),
            ('VALIGN',     (0,0), (7,0), 'MIDDLE'),
            ('TEXTCOLOR',  (0,0), (7,0), colors.whitesmoke),

            # --- Row 1 secondary headers ---
            ('SPAN',       (0,0), (0,1)),
            ('SPAN',       (1,0), (1,1)),
            ('SPAN',       (2,0), (2,1)),
            ('BACKGROUND', (0,0), (2,1), colors.maroon),
            ('TEXTCOLOR',  (0,0), (2,1), colors.whitesmoke),
            ('FONTNAME',   (0,0), (2,1), 'Helvetica-Bold'),

            ('BACKGROUND', (3,1), (5,1), colors.maroon),
            ('BACKGROUND', (6,1), (7,1), colors.maroon),
            ('TEXTCOLOR',  (3,1), (7,1), colors.whitesmoke),
            ('FONTNAME',   (0,1), (7,1), 'Helvetica-Bold'),
            ('ALIGN',      (0,1), (7,1), 'CENTER'),
            ('VALIGN',     (0,1), (7,1), 'MIDDLE'),

            # Body cell defaults
            ('TOPPADDING', (0,2), (7,2), 0),
            ('VALIGN',     (0,2), (7,-1), 'TOP'),
            ('TEXTCOLOR',  (0,2), (7,-1), colors.black),

            ('BOX',        (0,0), (7,-1), 0.75, colors.black),
            ('INNERGRID',  (0,0), (7,-1), 0.25, colors.black),

            ('LEFTPADDING', (0,0), (7,-1), 4),
            ('RIGHTPADDING',(0,0),(7,-1), 4),
            ('BOTTOMPADDING',(0,0),(7,-1), 2),
        ]

        # Insert generated spans + valign rules
        base_style.extend(span_cmds)
        base_style.extend(valign_cmds)

        tbl.setStyle(TableStyle(base_style))
        tbl.spaceBefore = 0
        tbl.spaceAfter = 0
        return tbl

    def _build_detection_refs(self, ptid: str, a18, platforms: list[str], tid: str | None = None) -> list[dict]:
        """
        Return a list of dicts for unique detection strategies relevant to `ptid`
        after platform filtering. Each item has:
        - 'strategy' : the source strategy dict (with s['det_id'] stamped)
        - 'det_id'   : canonical DET-#### (or object id fallback)
        - 'det_name' : strategy name or det_id
        - 'det_anchor': anchor-safe id used in-PDF (matches appendix anchors)
        """
        # Use the existing single source of truth for relevance
        strategies = self._a18.get_strategies(tid or ptid)
        out, seen = [], set()
        for s in strategies:
            det_id, det_name, det_anchor = self._resolve_det_meta(s, tid or ptid)
            if det_id in seen:
                continue
            seen.add(det_id)
            s = dict(s)
            s['det_id'] = det_id  # keep normalized id on the strategy (downstream checks rely on this)
            out.append({
                'strategy': s,
                'det_id': det_id,
                'det_name': det_name,
                'det_anchor': det_anchor,
            })
        return out

    def _format_an_range(self, an_ids: list[str]) -> str:
        """Format 'Analytic ."""
        nums = []
        for x in an_ids:
            m = re.match(r'AN(\d{4})$', str(x).strip(), flags=re.IGNORECASE)
            if m:
                nums.append(int(m.group(1)))
        if not nums:
            # fallback: show unique AN ids joined
            uniq = sorted(set(filter(None, an_ids)))
            return f"Analytic ( {', '.join(uniq) if uniq else '—'} )"
        return f"Analytic ( AN{min(nums):04d} to AN{max(nums):04d} )"

    def _normalize_ext_id(self, s: str) -> str:
        s = (s or '').strip().upper()
        s = s.replace("AN-", "AN")
        return s

    def _normalize_det_id(self, det_id: str, fallback=None):
        if not det_id:
            return fallback

        s = det_id.upper().replace("DET", "")
        digits = "".join(ch for ch in s if ch.isdigit())

        if digits:
            return f"DET{digits}"     # <-- NO DASH VERSION
        return fallback

    def _resolve_det_meta(self, s: dict, ptid: str) -> tuple[str, str, str]:
        """
        Return (det_id, det_name, det_anchor) for a strategy dict `s`.
        - det_id: canonical DET#### when possible (no dash)
        - det_name: strategy name or det_id
        - det_anchor: anchor-safe version of det_id (also DET####)
        """
        # 1) Try stamped det_id from relevant_strategies
        raw = s.get("det_id") or ""

        # 2) Else fallback to external_id inside external_references
        ext = next(
            (
                er.get("external_id", "")
                for er in (s.get("external_references") or [])
                if isinstance(er.get("external_id", ""), str)
            ),
            ""
        )

        # 3) Determine best raw ID
        best = raw or ext or s.get("id", "") or ""

        # 4) Normalize → DET#### (no dash)
        det_id = self._normalize_det_id(best, fallback=best)

        # 5) Strategy name or fallback to det_id
        det_name = s.get("name") or det_id

        # 6) Anchor is exactly the normalized det_id, sanitized
        det_anchor = self._normalize_det_id(det_id)

        print(f"[DET/_resolve] det_id={det_id} det_anchor={det_anchor} name={det_name}")
        return det_id, det_name, det_anchor


    # @staticmethod
    # def _anchor_for_an(an_id: str) -> str:
    #     return (an_id or '').upper().replace('AN-', 'AN')
    
    def _anchor_for_det(self, det_id: str) -> str:
        """
        Convert a DET id (DET####) into a stable PDF anchor.

        - Normalizes dash/no-dash variants
        - Ensures uppercase
        - Produces something safe for <a name="..."> tags
        """
        det = (det_id or "").strip().upper()
        det = det.replace("DET-", "DET")  # normalize DET-#### → DET####
        return det

    # def _relevant_strategies_for_ptid(self, a18, ptid: str, plats: list[str], tid: str | None = None):
    #     """
    #     Return detection strategies for `ptid`/`tid`, deduped by DET id.

    #     v18 already links techniques to detection strategies via STIX relationships,
    #     so we do NOT try to re-derive that linkage from analytics here. We simply:

    #     - ask attack18 for strategies for the technique (or sub-technique),
    #     - pull the DET#### code from the strategy's external_references,
    #     - normalize it, and
    #     - deduplicate by that DET id.
    #     """
    #     # NOTE: `plats` is currently unused here; platform filtering happens
    #     # at the analytics row level when building the table.
    #     cand = self._a18.get_strategies(tid or ptid) or []
    #     rel, seen = [], set()

    #     for s in cand:
    #         # Best-effort DET label from external_references
    #         det_label = next(
    #             (
    #                 er.get("external_id", "")
    #                 for er in (s.get("external_references") or [])
    #                 if isinstance(er.get("external_id", ""), str)
    #                 and er.get("external_id", "").strip().upper().startswith("DET")
    #             ),
    #             ""
    #         )

    #         det_id = self._normalize_det_id(
    #             det_label or s.get("det_id") or s.get("id", ""),
    #             fallback=None,
    #         )
    #         if not det_id or det_id in seen:
    #             continue

    #         seen.add(det_id)
    #         s = dict(s)
    #         s["det_id"] = det_id
    #         rel.append(s)

    #     return rel

    def _extract_an_labels(self, arow, a18=None, strategy=None, ptid=None):
        """
        Return (cell_label, header_an) for an analytic row.
        - cell_label: what we display in the AN column (and anchor on).
        - header_an : canonical 'AN-####' that contributes to the header range.
        """
        # 1) explicit row-level AN id
        an = (arow.get('an_id') or '').strip()
        if re.match(r'^AN-?\d{4}$', an, flags=re.IGNORECASE):
            return an.upper(), an.upper()
        # 2a) map by STIX analytic id -> AN
        aid = (arow.get('id') or '').strip().lower()
        if aid and getattr(self, '_an_external_by_stix', None):
            mapped = self._an_external_by_stix.get(aid)
            if mapped:
                canon = self._normalize_ext_id(mapped)
                return canon, canon

        # 2b) map by (DET, platform) -> AN
        det = self._normalize_det_id(arow.get('det_id') or '')
        plat_l = (arow.get('platform') or '').strip().lower()
        if det and getattr(self, '_an_by_det_and_platform', None):
            mapped = (self._an_by_det_and_platform.get((det, plat_l)) or
                    self._an_by_det_and_platform.get((det, None)))
            if mapped:
                canon = self._normalize_ext_id(mapped)
                return canon, canon

        # 3) (slower) resolve via full analytic object in bundle
        analytic_obj = None
        if a18 and aid:
            # Try common places to find the full STIX objects list
            candidate_lists = []
            for attr in ('objects', '_objects'):
                v = getattr(a18, attr, None)
                if isinstance(v, list):
                    candidate_lists.append(v)
            for attr in ('bundle', '_bundle'):
                v = getattr(a18, attr, None)
                if isinstance(v, dict) and isinstance(v.get('objects'), list):
                    candidate_lists.append(v['objects'])

            for objs in candidate_lists:
                for o in objs:
                    if o.get('type') == 'x-mitre-analytic' and (o.get('id','').strip().lower() == aid):
                        analytic_obj = o
                        break
                if analytic_obj:
                    break

        if analytic_obj:
            for er in (analytic_obj.get('external_references') or []):
                eid = (er.get('external_id') or '').strip()
                if re.match(r'^AN-?\d{4}$', eid, flags=re.IGNORECASE):
                    canon = self._normalize_ext_id(eid)
                    return canon, canon

        # 4) final fallback: stable short label (does NOT contribute to header range)
        fallback = (arow.get('id', '')[-8:] or '').upper() or 'AN'
        return fallback, None
