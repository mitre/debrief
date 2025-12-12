import json, os, re

from collections import OrderedDict, defaultdict
from reportlab.lib import colors

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, PageBreak, Table, TableStyle
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from plugins.debrief.app.utility.base_report_section import BaseReportSection
from plugins.debrief.attack_mapper import Attack18Map, index_bundle, CACHE_PATH

class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'ttps-detections'
        self.display_name = 'TTPs & V18 Detections'
        self.section_title = 'TTPs and V18 Detections for <font name=Courier-Bold size=17>%s</font>'
        self.description = 'Ordered steps (TTPs) from the operation with their associated ATT&CK v18 Detections.'
        self._a18 = None
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
            1.40*inch,  # Field
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

    def _load_attack18(self):
        """Load ATT&CK v18 index, preferring the local cache so report gen works offline."""
        if self._a18 is None:
            cache_path = CACHE_PATH
            if not os.path.exists(cache_path):
                cache_path = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'attack18_cache.json')
                cache_path = os.path.abspath(cache_path)
            with open(cache_path, 'r', encoding='utf-8') as f:
                bundle = json.load(f)
                # (1) STIX-analytic-id  -> AN-#### (normalize to AN-0000)
                self._an_external_by_stix = {}
                # (2) (DET-####, platform_lower) -> AN-####  (parsed from the analytic's URL)
                self._an_by_det_and_platform = {}

                for obj in (bundle.get('objects') or []):
                    if obj.get('type') != 'x-mitre-analytic':
                        continue

                    stix_id = (obj.get('id', '') or '').strip().lower()
                    plats = [str(p).strip().lower() for p in (obj.get('x_mitre_platforms') or []) if p]

                    an_ext = None
                    det_ext = None

                    for er in (obj.get('external_references') or []):
                        eid = (er.get('external_id') or '').strip()
                        url = (er.get('url') or '').strip()

                        # AN external id
                        if re.match(r'^AN-?\d{4}$', eid, flags=re.IGNORECASE):
                            an_ext = f"AN-{int(re.sub(r'[^0-9]', '', eid)):04d}"

                        # Pull DET and AN from URL like .../detectionstrategies/DET0014#AN0041
                        m = re.search(r'/detectionstrategies/(DET-?\d{4})(?:#(AN-?\d{4}))?', url, flags=re.IGNORECASE)
                        if m:
                            det_ext = f"DET-{int(re.sub(r'[^0-9]', '', m.group(1))):04d}"
                            if not an_ext and m.group(2):
                                an_ext = f"AN-{int(re.sub(r'[^0-9]', '', m.group(2))):04d}"

                    # Fill maps
                    if stix_id and an_ext:
                        self._an_external_by_stix[stix_id] = an_ext

                    if det_ext and an_ext:
                        if not plats:
                            plats = [None]  # allow platform-agnostic mapping as a fallback
                        for p in plats:
                            self._an_by_det_and_platform[(det_ext, p)] = an_ext
            self._a18 = Attack18Map(index_bundle(bundle))
        return self._a18

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


        a18 = self._load_attack18()
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
            flows.extend(self._generate_detection_appendix(op, a18, paw_to_platform, run_platforms=run_platforms))

        return flows

    def _generate_detection_appendix(self, operation, a18: Attack18Map, paw_to_platform, run_platforms=None):
        styles = self.styles
        flows = []
        self._ensure_styles()
        run_platforms = (run_platforms or [])

        # 1) Collect platforms actually seen for each parent technique in this op
        tech_plats = defaultdict(lambda: OrderedDict())
        ptid_to_tids = defaultdict(set)
        for link in getattr(operation, 'chain', []) or []:
            if getattr(link, 'cleanup', False):
                continue
            tid  = (getattr(getattr(link, 'ability', None), 'technique_id', '') or '').strip().upper()
            if not tid:
                continue
            ptid = tid.split('.')[0]
            plat = (paw_to_platform.get(getattr(link, 'paw', None)) or '').lower()
            if ptid:
                # record even if platform unknown; let the table use [None]
                tech_plats[ptid].setdefault((plat or None), None)
            ptid_to_tids[ptid].add(tid)
        print("[DET] op:", getattr(operation, "name", "?"),
            "ptids:", list(tech_plats.keys())) 

        # ---- One appendix block per TECHNIQUE, and per DET strategy under that technique ----
        for ptid, _plats in tech_plats.items():
            print(f"[DET] PTID={ptid} plats={list(_plats.keys())} exact_tids={sorted(ptid_to_tids.get(ptid, []))}", flush=True)
            if run_platforms:
                observed_plats = run_platforms[:]          # e.g., ['linux']
            else:
                # No agents info? fall back to analytics-derived platforms
                cache_plats = set()
                for r in (a18.get_analytics(ptid, platform=None) or []):
                    cache_plats.update(
                        str(p).strip().lower()
                        for p in (r.get('platforms') or [])
                        if p
                    )
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
            strategies = []
            s = a18.get_strategies(ptid) or []
            print(f"[DET] get_strategies({ptid}) -> {len(s)}")
            chosen_tid = None
            for exact_tid in tids + [ptid]:
                strategies = self._relevant_strategies_for_ptid(a18, ptid, plats_filter, tid=exact_tid)
                if strategies:
                    chosen_tid = exact_tid
                    break
            if not strategies:
                continue

            # Dedup strategies by DET id
            # Build unique, platform-relevant refs once (dedup + canonical ids)
            refs = self._build_detection_refs(ptid, a18, list(plats_iter), tid=chosen_tid)
            if not refs:
                continue

            for ref in refs:
                s         = ref['strategy']
                det_id    = ref['det_id']
                det_name  = ref['det_name']
                # det_anchor is not directly needed here (header builder emits the anchor)
                print(f"[DET] {det_id} — {det_name} (ptid={ptid}, plats={list(plats_iter)})")

                # ---------- SINGLE TABLE (8 cols) ----------
                rows = []
                rows.append([
                    'AN', 'Platform', 'Detection Statement',
                    'Data Component Elements (DC)', '', '',
                    'Mutable Elements', ''
                ])
                rows.append(['', '', '', 'Name', 'Channel', 'Data Component', 'Field', 'Description'])

                an_ids       = set()
                seen_rows    = set()
                anchored_ans = set()
                analytics_by_plat = {
                    plat: (a18.get_analytics(ptid, platform=plat) or [])
                    for plat in plats_iter
                }
                for plat, analytics in analytics_by_plat.items():
                    print(f"[DET] get_analytics(ptid={ptid}, plat={plat}) -> rows={len(analytics)}; "
                        f"sample ANs={[ (r.get('an_id'), r.get('technique_id')) for r in analytics[:3] ]}")

                    for arow in analytics:
                        print(f"  [DET] row det_id={arow.get('det_id')} an_id={arow.get('an_id')} tech={arow.get('technique_id')}", flush=True)
                        row_det      = (arow.get('det_id') or '').strip()
                        row_det_norm = self._normalize_det_id(row_det, fallback=row_det)
                        det_norm     = self._normalize_det_id(det_id, fallback=det_id)
                        sid          = (s.get('id') or '').strip()

                        if row_det:
                            if not (row_det_norm == det_norm or row_det == sid):
                                continue
                        else:
                            if sid:
                                continue

                        plat_disp = (plat or arow.get('platform', '') or '').capitalize()
                        stmt      = self._p(arow.get('statement', '') or '')
                        # Ensure lookup sees the platform we’re iterating
                        if plat and not arow.get('platform'):
                            arow = dict(arow)
                            arow['platform'] = plat
                        cell_label, header_an = self._extract_an_labels(arow, a18=a18, strategy=s, ptid=ptid)
                        # If we got a canonical AN from the row/strategy hint, keep it for the header range
                        if header_an:
                            an_ids.add(header_an)
                        # Also: if the cell label itself is canonical, count it too (cheap win)
                        elif re.match(r'^AN-?\d{4}$', cell_label, flags=re.IGNORECASE):
                            an_ids.add(self._normalize_ext_id(cell_label))

                        plat_disp = (plat or arow.get('platform', '') or '').capitalize()
                        stmt = Paragraph(  # centered, with light escaping like _p()
                            (str(arow.get('statement','') or '')
                                .replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")),
                            self.sty_cell_center
                        )

                        # Anchor on the exact cell label so the per-AN links remain stable
                        anchor = self._anchor_for_an(cell_label)
                        if cell_label not in getattr(self, "_emitted_anchors", set()):
                            an_cell = Paragraph(f'<a name="{anchor}"></a>{cell_label}', self.sty_cell_center)
                            self._emitted_anchors.add(cell_label)
                        else:
                            an_cell = Paragraph(cell_label, self.sty_cell_center)
                        plat_cell = Paragraph(plat_disp, self.sty_cell_center)
                        dcs  = arow.get('dc_elements') or [{}]
                        tuns = arow.get('tunables') or []

                        for d in (dcs or [{}]):
                            dc_name = d.get('name', '')
                            dc_chan = d.get('channel', '')
                            dc_comp = d.get('data_component', '')

                            tuns_iter = tuns if tuns else [None]
                            for t in tuns_iter:
                                if t is None:
                                    field_val = ''
                                    desc_val  = ''
                                elif isinstance(t, dict):
                                    field_val = (t.get('field') or '').strip()
                                    desc_val  = (t.get('description') or '').strip()
                                else:
                                    field_val = str(t or '')
                                    desc_val  = ''

                                key = (cell_label, plat_disp, dc_name, field_val, dc_chan)
                                if key in seen_rows:
                                    continue
                                seen_rows.add(key)

                                rows.append([
                                    an_cell, plat_cell, stmt,
                                    self._p(dc_name), self._p(dc_chan), self._p(dc_comp),
                                    self._p(field_val), self._p(desc_val)
                                ])

                print(f"  [ANs] for {det_id}: {sorted(an_ids)}")

                # ---- Build header block ----
                hdr_block = self._build_det_header_block(det_id, det_name, sorted(an_ids))
                if len(rows) <= 2:
                    rows.append(['', '', self._p('No analytics for the selected OS scope.'), '', '', '', '', ''])

                span_cmds = []
                if len(rows) > 2:
                    def _plain(c):
                        return getattr(c, 'text', str(c))
                    block_start = 2
                    prev_key = (_plain(rows[2][0]), _plain(rows[2][1]), _plain(rows[2][2]))
                    for r in range(3, len(rows)):
                        key = (_plain(rows[r][0]), _plain(rows[r][1]), _plain(rows[r][2]))
                        if key != prev_key:
                            if r - 1 > block_start:
                                span_cmds += [
                                    ('SPAN', (0, block_start), (0, r-1)),
                                    ('SPAN', (1, block_start), (1, r-1)),
                                    ('SPAN', (2, block_start), (2, r-1)),
                                    ('VALIGN', (0, block_start), (2, r-1), 'MIDDLE'),
                                ]
                            block_start = r
                            prev_key = key
                    if len(rows) - 1 > block_start:
                        span_cmds += [
                            ('SPAN', (0, block_start), (0, len(rows)-1)),
                            ('SPAN', (1, block_start), (1, len(rows)-1)),
                            ('SPAN', (2, block_start), (2, len(rows)-1)),
                            ('VALIGN', (0, block_start), (2, len(rows)-1), 'MIDDLE'),
                        ]

                tbl = self._build_det_table(rows, span_cmds)
                tbl.spaceBefore = 0
                tbl.spaceAfter  = 0
                flows.append(KeepTogether(hdr_block + [tbl]))

        return flows

    def _build_det_table(self, rows, span_cmds=None):
        """
        Build the 8-column detections table with our standard styling.
        Pass optional span_cmds (list of TableStyle commands) to add row spans.
        """
        tbl = Table(
            rows,
            colWidths=self.DATA_COL_WIDTHS,
            repeatRows=2,
            hAlign='CENTER'
        )

        base_style = [
            # --- Top header row (main labels) ---
            ('SPAN',       (3,0), (5,0)),
            ('SPAN',       (6,0), (7,0)),
            ('BACKGROUND', (0,0), (7,0), colors.maroon),
            ('FONTNAME',   (0,0), (7,0), 'Helvetica-Bold'),
            ('ALIGN',      (0,0), (7,0), 'CENTER'),
            ('VALIGN',     (0,0), (7,0), 'MIDDLE'),
            ('TEXTCOLOR',  (0,0), (7,0), colors.whitesmoke),

            # --- Second header row (sub-labels) ---
            ('SPAN',       (0,0), (0,1)),
            ('SPAN',       (1,0), (1,1)),
            ('SPAN',       (2,0), (2,1)),
            # Paint the entire two-row left header block (AN / Platform / Detection Statement)
            ('BACKGROUND', (0,0), (2,1), colors.maroon),
            ('TEXTCOLOR',  (0,0), (2,1), colors.whitesmoke),
            ('FONTNAME',   (0,0), (2,1), 'Helvetica-Bold'),

            # Paint the other header groups
            ('BACKGROUND', (3,1), (5,1), colors.maroon),
            ('BACKGROUND', (6,1), (7,1), colors.maroon),
            ('TEXTCOLOR',  (3,1), (7,1), colors.whitesmoke),
            ('FONTNAME',   (0,1), (7,1), 'Helvetica-Bold'),
            ('ALIGN',      (0,1), (7,1), 'CENTER'),
            ('VALIGN',     (0,1), (7,1), 'MIDDLE'),

            # --- Cosmetic / borders ---
            ('LINEBELOW',  (0,0), (7,1), 0, colors.transparent),
            ('TOPPADDING', (0,2), (7,2), 0),
            ('VALIGN',     (0,2), (7,-1), 'TOP'),
            ('TEXTCOLOR',  (0,2), (7,-1), colors.black),

            ('BOX',        (0,0), (7,-1), 0.75, colors.black),
            ('INNERGRID',  (0,0), (7,-1), 0.25, colors.black),

            ('LEFTPADDING',(0,0), (7,-1), 4),
            ('RIGHTPADDING',(0,0),(7,-1), 4),
            ('BOTTOMPADDING',(0,0),(7,-1), 2),
        ]

        if span_cmds:
            base_style += span_cmds

        tbl.setStyle(TableStyle(base_style))
        tbl.spaceBefore = 0
        tbl.spaceAfter  = 0
        return tbl

    def _build_detection_refs(self, ptid: str, a18: Attack18Map, platforms: list[str], tid: str | None = None) -> list[dict]:
        """
        Return a list of dicts for unique detection strategies relevant to `ptid`
        after platform filtering. Each item has:
        - 'strategy' : the source strategy dict (with s['det_id'] stamped)
        - 'det_id'   : canonical DET-#### (or object id fallback)
        - 'det_name' : strategy name or det_id
        - 'det_anchor': anchor-safe id used in-PDF (matches appendix anchors)
        """
        # Use the existing single source of truth for relevance
        strategies = self._relevant_strategies_for_ptid(a18, ptid, platforms, tid=tid) or []
        out, seen = [], set()
        for s in strategies:
            det_id, det_name, det_anchor = self._resolve_det_meta(s, ptid)
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

    def _normalize_ext_id(self, s: str) -> str:
        s = (s or '').strip().upper()
        if s.startswith('AN') and not s.startswith('AN-'):
            return f'AN-{s[2:]}'
        return s

    def _normalize_det_id(self, det_external_or_id: str, fallback: str = "") -> str:
        """
        Return canonical DET-#### when possible; otherwise fallback (usually the object id).
        """
        s = (det_external_or_id or "").strip()
        m = re.match(r'^DET-?(\d{4})$', s, flags=re.IGNORECASE)
        if m:
            return f"DET-{int(m.group(1)):04d}"
        return fallback or s

    def _resolve_det_meta(self, s: dict, ptid: str) -> tuple[str, str, str]:
        """
        Return (det_id, det_name, det_anchor) for a strategy dict `s`.
        - det_id: canonical DET-#### when possible (falls back to object id)
        - det_name: s['name'] or det_id
        - det_anchor: anchor-safe id used in-PDF
        """
        # 1) prefer stamped det_id (from _relevant_strategies_for_ptid), else external DET-####, else object id
        ext = next((er.get('external_id', '') for er in (s.get('external_references') or [])
                if isinstance(er.get('external_id',''), str)), '')
        det_id = self._normalize_det_id(s.get('det_id') or ext, fallback=(s.get('id', '') or ''))

        # 2) If still not canonical DET-####, consult analytics to lift to canonical DET
        if not re.match(r'^DET-\d{4}$', str(det_id), flags=re.IGNORECASE):
            a18 = self._load_attack18()
            for r in (a18.get_analytics(ptid, platform=None) or []):
                rd = (r.get('det_id') or '').strip()
                if rd.upper().startswith('DET-'):
                    det_id = self._normalize_det_id(rd, fallback=det_id)
                    print(f"[DET/_resolve] Upgraded det_id via analytics: {rd} -> {det_id} (ptid={ptid})")
                    break

        det_name = s.get('name', '') or det_id
        det_anchor = (det_id or (s.get('id','')[-8:]) or f"DET-{ptid}").replace(':','-')
        print(f"[DET/_resolve] det_id={det_id} det_anchor={det_anchor} name={det_name}")
        return det_id, det_name, det_anchor

    @staticmethod
    def _anchor_for_an(an_id: str) -> str:
        return (an_id or '').upper().replace(':', '-')
    
    def _relevant_strategies_for_ptid(self, a18, ptid: str, plats: list[str], tid: str | None = None):
        plats_l = { str(p).strip().lower() for p in (plats or []) if p }
        rel = []
        cand = a18.get_strategies(tid or ptid) or []
        # Gather analytics for parent PTID so we can match rows back to strategies
        analytics = a18.get_analytics(ptid, platform=None) or []
        for s in cand:
            sid = (s.get('id') or '').strip()
            has_hit = False
            for r in analytics:
                # platform gate
                row_plats = { (r.get('platform') or '').strip().lower() }
                row_plats |= { str(p).strip().lower() for p in (r.get('platforms') or []) if p }
                if plats_l and row_plats and not (row_plats & plats_l):
                    continue

                rdet = (r.get('det_id') or '').strip()
                # rows may carry raw strategy id or DET-####
                if rdet == sid or rdet.upper().startswith('DET-'):
                    has_hit = True
                    break
            if has_hit:
                # stamp a best-effort det_id label we can anchor to
                det_label = next((er.get('external_id','') for er in (s.get('external_references') or [])
                  if isinstance(er.get('external_id',''), str) and er.get('external_id','').startswith('DET-')),
                 None)
                s = dict(s)
                s['det_id'] = (det_label or sid)
                rel.append(s)
        # de-dup by det_id label
        out, seen = [], set()
        for s in rel:
            if s['det_id'] not in seen:
                seen.add(s['det_id'])
                out.append(s)
        return out

    def _extract_an_labels(self, arow, a18=None, strategy=None, ptid=None):
        """
        Return (cell_label, header_an) for an analytic row.
        - cell_label: what we display in the AN column (and anchor on).
        - header_an : canonical 'AN-####' that contributes to the header range.
        """
        # 1) explicit row-level AN id
        an = (arow.get('an_id') or '').strip()
        if re.match(r'^AN-?\d{4}$', an, flags=re.IGNORECASE):
            canon = self._normalize_ext_id(an)
            return canon, canon

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
