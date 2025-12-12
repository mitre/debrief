import os, json, logging, re
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, TableStyle, Table
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from html import escape

from plugins.debrief.app.utility.base_report_section import BaseReportSection
from plugins.debrief.app.debrief_svc import DebriefService

from plugins.debrief.attack_mapper import Attack18Map, index_bundle, CACHE_PATH, load_attack18_cache


class DebriefReportSection(BaseReportSection):
    def __init__(self):
        super().__init__()
        self.id = 'tactic-technique-table'
        self.display_name = 'Tactic and Technique Table'
        self.section_title = 'TACTICS AND TECHNIQUES'
        self.description = ''
        self.log = logging.getLogger('debrief_gui')
        self._a18 = None  # lazy-loaded ATT&CK v18 index
        self._emitted_anchors = set() # track emitted anchors to avoid duplicates

    # ---------- ATT&CK v18 Load ----------
    def _load_attack18(self):
        """Load ATT&CK v18 index (cached file, works offline)."""
        if self._a18 is None:
            cache_path = CACHE_PATH
            if not os.path.exists(cache_path):
                cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'attack18_cache.json'))
            bundle = load_attack18_cache(cache_path)
            self._a18 = Attack18Map(index_bundle(bundle))
            print(f"Loaded ATT&CK v18 cache from {cache_path}")
        return self._a18

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
            # Fallback if all tactics have empty/absent 'techniques'
            if not any((t or {}).get('techniques') for t in ttps.values()):
                self.log.warning("generate_ttps() returned empty techniques; using _get_operation_ttps fallback")
                ttps = self._get_operation_ttps(operations)
            flowable_list.append(self.group_elements([
                Paragraph(self.section_title, styles['Heading2']),
                self._generate_ttps_table(ttps, kwargs.get('operations', []))
            ]))
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

            # If keys look like names (not TIDs), invert to {tid: name}
            def _is_tid(s: str) -> bool:
                return bool(re.match(r'^T\d{4}(?:\.\d{3})?$', str(s or '').strip()))

            if tech_map and not all(_is_tid(k) for k in tech_map.keys()):
                tech_map = {v: k for (k, v) in tech_map.items() if v}  # -> {tid: name}

            for tid, tname in tech_map.items():
                print(f"  - Processing technique: TID={tid}, Name={tname}")
                ptid = (tid or '').split('.')[0].strip().upper()

                # Technique label
                label = f"{tid}: {tname}" if (tid and tname) else (tid or tname or '—')
                technique_lines.append(label)

                # ---- ONE Analytic per technique (prefer the sub-technique) ----
                chosen_platforms = tech_plats.get(ptid, set())
                det_anchor = None
                det_label = None

                for r in self._load_attack18().get_analytics(ptid, platform=None) or []:
                    r_tid = (r.get('technique_id') or '').strip().upper()
                    da = self._normalize_det_id(r.get('det_id') or '')
                    if not da:
                        continue
                    # prefer exact technique match
                    if r_tid == tid.strip().upper():
                        det_label = da
                        break
                    # fallback to any DET under parent technique
                    if not det_label:
                        det_label = da

                if det_label:
                    det_anchor = self._anchor_for_det(det_label)
                    link_line = f'<link href="#{escape(det_anchor)}" color="blue">{escape(det_label)}</link>'
                else:
                    link_line = '—'

                detect_lines.append(link_line)

            
            # Abilities (flatten & clean)   
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

            # IMPORTANT: render as Paragraphs so <link> tags work
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
            ('BACKGROUND', (0,0), (-1,0), header_bg),   # red/orange header
            ('TEXTCOLOR',  (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN',      (0,0), (-1,0), 'CENTER'),

            ('VALIGN',     (0,1), (-1,-1), 'TOP'),
            ('TEXTCOLOR',  (0,1), (-1,-1), colors.black),
            
            ('ALIGN',      (0,1), (0,-1), 'CENTER'),   # Tactics column
            ('ALIGN',      (1,1), (2,-1), 'LEFT'),     # Techniques & Abilities columns
            ('ALIGN',      (3,1), (3,-1), 'CENTER'),   # Detections column


            ('BOX',        (0,0), (-1,-1), 0.75, colors.black),
            ('INNERGRID',  (0,0), (-1,-1), 0.25, colors.black),

            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING',(0,0), (-1,-1), 4),
            ('TOPPADDING',  (0,0), (-1,-1), 0),
            ('BOTTOMPADDING',(0,0), (-1,-1), 2),
        ]))

        print(f"Generated TTP table with {len(ttp_data)-1} tactics")
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
                tech_name   = getattr(link.ability, 'technique_name', None)
                tech_id     = getattr(link.ability, 'technique_id', None)
                step_name   = getattr(link.ability, 'name', None)

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
    def _anchor_for_det(det_id: str) -> str:
        """Anchor-safe DET id used by the detections section."""
        return (det_id or '').replace(':', '-')
    def _normalize_det_id(self, s: str) -> str:
        s = (s or "").strip()
        m = re.match(r'^DET-?(\d{4})$', s, flags=re.IGNORECASE)
        return f"DET-{int(m.group(1)):04d}" if m else ""

    @staticmethod
    def _anchor_for_an(an_id: str) -> str:
        """Anchor-safe AN id used by the tactic-technique table."""
        s = (an_id or '').strip().upper()
        m = re.match(r'^AN-?(\d{4})$', s)
        if m:
            return f"AN-{int(m.group(1)):04d}"
        return s.replace(':', '-')
    
    def _a18_index(self):
        a18 = self._load_attack18()
        # Attack18Map likely keeps a dict of all objects by id; fall back to bundle index if needed
        return getattr(a18, 'index', None) or getattr(a18, '_index', None) or {}

    def _normalize_ext_id(self, s: str) -> str:
        s = (s or '').strip().upper()
        if s.startswith('AN') and not s.startswith('AN-'):
            return f'AN-{s[2:]}'
        return s

    def _analytic_ids_for_tid(self, ptid: str, tid: str = None):
        """
        Return unique AN IDs for a technique using analytics rows,
        preferring exact sub-technique (tid) when provided.
        """
        a18 = self._load_attack18()
        an_ids_exact = set()
        an_ids_parent = set()
        print(f"[TT/_an] ptid={ptid} tid={tid}", flush=True)
        rows = a18.get_analytics(ptid, platform=None) or []
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
            rows = self._load_attack18().get_analytics(ptid, platform=None) or []
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

    