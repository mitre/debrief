import os, json, logging, re
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, TableStyle, Table
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from html import escape

from plugins.debrief.app.utility.base_report_section import BaseReportSection
from plugins.debrief.app.debrief_svc import DebriefService

from plugins.debrief.attack_mapper import get_attack18

class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'tactic-technique-table'
        self.display_name = 'Tactic and Technique Table'
        self.section_title = 'TACTICS AND TECHNIQUES'
        self.description = ''
        self.log = logging.getLogger('debrief_gui')
        self._a18 = get_attack18()  # lazy-loaded ATT&CK v18 index
        self._emitted_anchors = set() # track emitted anchors to avoid duplicates
        


    # ---------- Report generation ----------
    async def generate_section_elements(self, styles, **kwargs):
        self.tt_body = ParagraphStyle(
            name="tt-body",
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
            print("Generating Tactic and Technique Table section")
            print(f"  - Operations count: {len(kwargs.get('operations', []))}")

            operations = kwargs.get('operations', [])
            ttps = DebriefService.generate_ttps(operations) or {}

            if not any((t or {}).get('techniques') for t in ttps.values()):
                self.log.warning("generate_ttps() returned empty techniques; using _get_operation_ttps fallback")
                ttps = self._get_operation_ttps(operations)

            # ----------------------------------------------------------
            # PREDECLARE DET ANCHORS — must go INSIDE the KeepTogether block
            # ----------------------------------------------------------
            anchors = []
            predeclared = set()

            for tactic in ttps.values():
                tech_map = tactic.get("techniques") or {}

                for tid, tname in tech_map.items():
                    ptid = (tid or "").split(".")[0].strip().upper()
                    strategies = self._a18.get_strategies(ptid) or []

                    for s in strategies:
                        det = self._normalize_det_id(s.get("det_id") or "")
                        if not det or det in predeclared:
                            continue

                        anchor = self._anchor_for_det(det)
                        anchors.append(Paragraph(f'<a name="{anchor}"/>', styles["Normal"]))
                        predeclared.add(det)
                        print(f"[TT-PREDECL] emitted anchor for {det} -> {anchor}")

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

    def _generate_ttps_table(self, ttps, operations):
        """
        One row per TACTIC.
        - Techniques: stacked "Txxxx: Name"
        - Detections: stacked DET IDs (as links) aligned 1:1 with Techniques
        - Abilities: stacked ability names (operation name stripped)
        """

        ttp_data = [['Tactics', 'Techniques', 'Abilities', 'Detections']]
        tech_plats = self._op_platforms_by_ptid(operations)

        for _tac_key, tactic in ttps.items():

            technique_lines = []
            detect_lines    = []

            tech_map = (tactic.get('techniques') or {})

            # If keys look like names (not TIDs), invert to {tid -> name}
            def _is_tid(s: str) -> bool:
                return bool(re.match(r'^T\d{4}(?:\.\d{3})?$', str(s or '').strip()))

            if tech_map and not all(_is_tid(k) for k in tech_map.keys()):
                tech_map = {v: k for (k, v) in tech_map.items() if v}

            for tid, tname in tech_map.items():

                print(f"  - Processing technique: TID={tid}, Name={tname}")
                ptid = (tid or '').split('.')[0].strip().upper()
                print(f"[TTP-05] Technique loop: tid={tid}, tname={tname}")

                # ------------------------------------------------------------------
                # TECHNIQUE LABEL
                # ------------------------------------------------------------------
                try:
                    label = f"{tid}: {tname}" if (tid and tname) else (tid or tname or '—')
                    technique_lines.append(label)
                    print("[TTP-06] label OK")
                except Exception:
                    self.log.exception("[ERR-TTP-06] Failed building technique label")
                    raise

                # ------------------------------------------------------------------
                # DETECTION SELECTION
                #   Use child technique strategies first; fallback to parent strategies.
                #   Only DETs present in ATT&CK strategies are allowed.
                #   Analytics guide choosing between multiple strategy DETs,
                #   but analytics do NOT create new DETs.
                # ------------------------------------------------------------------

                try:
                    # --- Child technique strategies ---
                    child_strats = self._a18.get_strategies(tid) or []
                    parent_strats = self._a18.get_strategies(ptid) or []

                    if child_strats:
                        strategies = child_strats
                        print(f"[TTP-07] Using CHILD strategies for {tid}: {len(strategies)} found")
                    else:
                        strategies = parent_strats
                        print(f"[TTP-07] Using PARENT strategies for {tid}: {len(strategies)} found")

                    # Collect allowed DETs from strategies (appendix will render only these)
                    valid_strategy_dets = []
                    for s in strategies:
                        det_id = self._normalize_det_id(s.get("det_id") or "")
                        if det_id:
                            valid_strategy_dets.append(det_id)

                    print(f"[TTP-07] Strategy DETs: {valid_strategy_dets}")

                    if not valid_strategy_dets:
                        print(f"[TTP-08] No valid strategy DETs for {tid} — using placeholder")
                        detect_lines.append("—")
                        continue

                    # Analytics: used only for ranking selection
                    analytics = self._a18.get_analytics(ptid, platform=None) or []
                    print(f"[TTP-07] Analytics loaded for {ptid}: {len(analytics)} items")

                    # Prefer DETs whose analytics match the exact sub-technique
                    exact_tid = tid.strip().upper()
                    child_hits = []

                    for det in valid_strategy_dets:
                        for row in analytics:
                            row_det = self._normalize_det_id(row.get("det_id") or "")
                            if row_det != det:
                                continue
                            if (row.get("technique_id") or "").strip().upper() == exact_tid:
                                child_hits.append(det)

                    if child_hits:
                        det_label = child_hits[0]
                        print(f"[TTP-08] Choosing child-hit DET for {tid}: {det_label}")
                    else:
                        det_label = valid_strategy_dets[0]
                        print(f"[TTP-08] No child-hit analytics; defaulting DET for {tid}: {det_label}")

                    # Build the PDF link (safe: appendix WILL contain this anchor)
                    try:
                        det_anchor = self._anchor_for_det(det_label)
                        link = f'<link href="#{escape(det_anchor)}" color="blue">{escape(det_label)}</link>'
                        detect_lines.append(link)
                        print(f"[TTP-09] DET link built: {link}")
                    except Exception:
                        self.log.exception("[ERR-TTP-09] DET link building failed")
                        raise

                except Exception:
                    self.log.exception("[ERR-TTP-08] DET selection failed")
                    raise

            # ----------------------------------------------------------------------
            # ABILITIES
            # ----------------------------------------------------------------------
            raw_steps = []
            for _opname, steps in (tactic.get('steps') or {}).items():
                raw_steps.extend(steps or [])
                print(f"    - Found steps for op {_opname}: {steps}")

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
            d_style = ParagraphStyle("tt-body-center", parent=self.tt_body, alignment=1)
            d_para = Paragraph(self._stacked(detect_lines, html=True), d_style)

            ttp_data.append([
                (tactic.get('name') or '').capitalize(),
                t_para, a_para, d_para
            ])

        print("[TT] BEFORE build types:",
            type(ttp_data[1][1]).__name__ if len(ttp_data) > 1 else None,
            type(ttp_data[1][2]).__name__ if len(ttp_data) > 1 else None,
            type(ttp_data[1][3]).__name__ if len(ttp_data) > 1 else None)

        # --------------------------------------------------------------------------
        # TABLE LAYOUT
        # --------------------------------------------------------------------------
        tbl = Table(
            ttp_data,
            colWidths=[
                0.75*inch, #Tactics
                2.85*inch, #Techniques
                1.75*inch, #Abilities
                0.90*inch  #Detections
            ],
            hAlign='LEFT'
        )

        header_bg = colors.maroon
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), header_bg),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN',      (0,0), (-1,0), 'CENTER'),

            ('VALIGN',     (0,1), (-1,-1), 'TOP'),
            ('TEXTCOLOR',  (0,1), (-1,-1), colors.black),

            ('ALIGN',      (0,1), (0,-1), 'CENTER'),
            ('ALIGN',      (1,1), (2,-1), 'LEFT'),
            ('ALIGN',      (3,1), (3,-1), 'CENTER'),

            ('BOX',        (0,0), (-1,-1), 0.75, colors.black),
            ('INNERGRID',  (0,0), (-1,-1), 0.25, colors.black),

            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING',(0,0), (-1,-1), 4),
            ('TOPPADDING',  (0,0), (-1,-1), 0),
            ('BOTTOMPADDING',(0,0), (-1,-1), 2),
        ]))

        print(f"Generated TTP table with {len(ttp_data)-1} tactics")
        print("[TT] sample technique_lines:", ttp_data[1][1] if len(ttp_data) > 1 else None)
        print("[TT] sample detections cell:", ttp_data[1][3] if len(ttp_data) > 1 else None)

        return tbl

    @staticmethod
    def _get_operation_ttps(operations):
        """
        (Unchanged) Aggregates 'steps' by tactic (dict of op_name -> [step names]).
        We flatten & clean in _generate_ttps_table to avoid showing operation names.
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
        print(f"Aggregated TTPs for {len(ttps)} tactics from operations")  
        print(f"  - Tactics: {list(ttps.keys())}")
        print(f"  - Sample tactic data: {list(ttps.values())[:1]}")
        print(f"  - Operations processed: {[op.name for op in operations]}")
        print(f"  - Total steps collected: {sum(len(tactic['steps']) for tactic in ttps.values())}")
        print(f"  - Total techniques collected: {sum(len(tactic['techniques']) for tactic in ttps.values())}")
        print(f"  - Example techniques for first tactic: {list(ttps.values())[0]['techniques']}")
        self.log
        return dict(sorted(ttps.items()))
    
    def _iter_techniques(self, tactic):
        """
        Yield (name, tid) pairs from multiple shapes:
        - dict: {"Technique Name": "T1059"} OR {"T1059": "Technique Name"}
        - list[dict]: [{"name": "...", "id": "T1059"}] or common variants
        - list[str] / set[str]: ["T1059", "T1041"]  (IDs only)
        """
        techs = tactic.get('techniques') or {}

        # dict form
        if isinstance(techs, dict):
            for k, v in techs.items():
                k_str = (k or "")
                v_str = (v or "")
                if k_str.upper().startswith("T") and not v_str.upper().startswith("T"):
                    # {"T1059": "Command and Scripting Interpreter"}
                    name, tid = v_str, k_str
                else:
                    # {"Command and Scripting Interpreter": "T1059"}  (original shape)
                    name, tid = k_str, v_str
                yield (name or ""), (tid or "")

        # list/tuple/set forms
        elif isinstance(techs, (list, tuple, set)):
            for t in techs:
                if isinstance(t, str):
                    # plain TID
                    yield "", t
                elif isinstance(t, dict):
                    name = t.get('name') or t.get('technique_name') or t.get('display') or ""
                    tid  = t.get('id')   or t.get('technique_id')   or t.get('tid')     or ""
                    yield (name or ""), (tid or "")

    # ---------- small helpers ----------
    @staticmethod
    def _stacked(lines, *, html=False):
        """
        Join a list of strings into a single Paragraph body with <br/>.
        If html=True, assume strings already contain reportlab para XML (e.g., <link>).
        """
        if html:
            # DO NOT escape – preserve tags like <link href="#AN-0006">AN-0006</link>
            clean = [str(s or '') for s in (lines or [])]
        else:
            # Safe text mode
            clean = [escape(str(s or '')) for s in (lines or [])]
        return '<br/>'.join(clean) or '—'

    @staticmethod
    def _anchor_for_det(det_id):
        return (det_id or "").upper().replace("DET-", "DET")
    def _normalize_det_id(self, det_id: str, fallback=None):
        if not det_id:
            return fallback

        s = det_id.upper().replace("DET", "")
        digits = "".join(ch for ch in s if ch.isdigit())

        if digits:
            return f"DET{digits}"     # <-- NO DASH
        return fallback

    @staticmethod
    def _anchor_for_an(an_id: str) -> str:
        """
        Return anchor-safe analytic ID in dashless form: AN0001
        """
        s = (an_id or "").strip().upper()

        # Accept AN0001 or AN-0001 or AN-1 etc.
        m = re.match(r'^AN-?(\d+)$', s)
        if m:
            return f"AN{int(m.group(1)):04d}"

        # Last-resort fallback — strip non-allowed characters
        safe = re.sub(r'[^A-Z0-9]', '', s)
        return safe or "AN0000"

    def _normalize_ext_id(self, s: str) -> str:
        """
        Normalize analytic external IDs into canonical dashless AN0001 format.
        """
        s = (s or "").strip().upper()

        # Handle AN0001, AN-0001, AN-1, AN1, AN001, etc.
        m = re.match(r'^AN-?(\d+)$', s)
        if m:
            return f"AN{int(m.group(1)):04d}"

        return s

    def _analytic_ids_for_tid(self, ptid: str, tid: str = None):
        """
        Return unique AN IDs for a technique using analytics rows,
        preferring exact sub-technique (tid) when provided.
        """
        an_ids_exact = set()
        an_ids_parent = set()
        print(f"[TT/_an] ptid={ptid} tid={tid}", flush=True)
        rows = self._a18.get_analytics(ptid, platform=None) or []
        print(f"[TT/_an] rows={len(rows)}", flush=True)
        tid_u = (tid or '').strip().upper()

        for r in rows:
            an = r.get('an_id') or (r.get('id', '')[-8:] or None)
            if not an:
                continue
            an = self._normalize_ext_id(an)
            r_tid = (r.get('technique_id') or '').strip().upper()

            if tid_u and r_tid == tid_u:
                an_ids_exact.add(an)
            else:
                an_ids_parent.add(an)
        print(f"[TT/_an] ptid={ptid} tid={tid} rows={len(rows)} "
        f"sample={[ (r.get('an_id'), r.get('technique_id')) for r in rows[:3] ]}")

        if an_ids_exact:
            return sorted(an_ids_exact)
        return sorted(an_ids_parent)

    def _select_single_an(self, ptid, tid, platforms: set[str]):
        # 1) collect candidates from strategy refs
        cand = self._analytic_ids_for_tid(ptid, tid) or []
        if not cand:
            return None

        # 2) prefer sub-technique-scoped analytics (Txxxx.yyy) over parent
        def is_sub(an_tid):
            return bool(re.search(r'T\d{4}\.\d{3}', an_tid or ''))
        sub_first = [c for c in cand if is_sub(tid)] or cand

        # 3) prefer platform overlap (using ATT&CK v18 x_mitre_platforms)
        plat_set = { (p or '').strip().lower() for p in (platforms or set()) if p }
        if plat_set:
            # derive per-AN platforms from analytics rows for this PTID
            rows = self._a18.get_analytics(ptid, platform=None) or []
            an_to_plats = {}
            for r in rows:
                an = r.get('an_id') or (r.get('id','')[-8:] or '')
                if not an:
                    continue
                an = self._normalize_ext_id(an)
                pls = set()
                sp = (r.get('platform') or '').strip().lower()
                if sp:
                    pls.add(sp)
                for p in (r.get('platforms') or []):
                    if p:
                        pls.add(str(p).strip().lower())
                an_to_plats.setdefault(an, set()).update(pls)
            with_plat = [a for a in sub_first if (an_to_plats.get(a, set()) & plat_set)]
            sub_first = with_plat or sub_first


        # 4) numeric tie-breaker on AN-####
        sub_first.sort(key=lambda a: int(re.search(r'AN-(\d+)', a).group(1)) if re.search(r'AN-(\d+)', a) else 10**9)
        choice = sub_first[0]
        print(f"[TT] Multiple ANs for {(tid or ptid)}: {cand} -> chose {choice}")
        return choice


    def _op_platforms_by_ptid(self, operations):
        # ptid -> set(lowercased platforms)
        ptid_plats = {}
        for op in operations or []:
            paw_to_plat = {}
            for a in getattr(op, 'agents', []):
                paw_to_plat[getattr(a, 'paw', None)] = (getattr(a, 'platform', '') or '').strip().lower()

            for l in getattr(op, 'chain', []):
                if getattr(l, 'cleanup', False):
                    continue
                tid = getattr(getattr(l, 'ability', None), 'technique_id', None)
                ptid = (tid or '').split('.')[0].upper()
                if not ptid:
                    continue
                plat = paw_to_plat.get(getattr(l, 'paw', None))
                if plat:
                    ptid_plats.setdefault(ptid, set()).add(plat)
        return ptid_plats

    