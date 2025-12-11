import json
import os
import re

from typing import Dict, List, Any, Optional, Tuple

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
DEFAULT_URL = os.getenv(
    "ATTACK_V18_URL",
    "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
)
CACHE_PATH = os.getenv(
    "ATTACK_V18_CACHE",
    os.path.join(os.path.dirname(__file__), "uploads", "attack18_cache.json"),
)

_TID_RX = re.compile(r'(T\d{4}(?:\.\d{3})?)', re.IGNORECASE)


def _extract_tids_from_analytic(a):
    """
    Return a set of ATT&CK technique IDs (T#### or T####.###) discoverable from an analytic.
    Searches in: external_references.external_id, id, name, and (as a last resort) description.
    """
    out = set()

    # 1) external refs, if any
    for er in (a.get("external_references") or []):
        eid = str(er.get("external_id", "") or "")
        if eid.startswith("T"):
            out.add(eid.upper())

    # 2) embedded in id / name / description (e.g., an-T1074_001-…)
    for field in ("id", "name", "description"):
        s = str(a.get(field, "") or "")
        for m in _TID_RX.findall(s):
            out.add(m.upper())

    return out


# ----------------------------------------------------------------------------
# Public Map API (back-compat name kept as Attack18Map)
# ----------------------------------------------------------------------------
class Attack18Map:
    """Unified view over ATT&CK bundles (v17.1 today; v18-ready).

    Exposes stable helpers used by the report section:
      - get_strategies(tid)
      - get_analytics(tid, platform=None)
      - get_log_sources(ids)

    On v18 bundles, these map to Detection Strategies / Analytics / DC log-sources.
    On v17.1, we synthesize minimal analytics from Data Components and detection text
    so downstream code still renders useful telemetry.
    """

    def __init__(self, idx: Dict[str, Any]):
        self._idx = idx or {}
        self._is_v18 = bool(self._idx.get("has_v18"))

    # ------------------------------ Public ----------------------------------
    def get_strategies(self, tid: str) -> List[Dict[str, Any]]:
        key = (tid or "").strip().upper()
        return (
            self._idx.get("strategies_by_tid", {}).get(key, [])
            or self._idx.get("strategies_by_tid", {}).get(_parent_tid(key), [])
        )

    def get_analytics(self, tid: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        # DO NOT force-parent here; we index under both exact+parent.
        key = (tid or "").strip().upper()
        all_an = (
            self._idx.get("analytics_by_tid", {}).get(key, [])
            or self._idx.get("analytics_by_tid", {}).get(_parent_tid(key), [])
        )
        if platform:
            p = platform.lower()

            def _match(row):
                plats = (row.get("platforms") or [])
                prim = (row.get("platform") or "")
                return (p in plats) or (prim in ("", None, p))
            return [a for a in all_an if _match(a)]
        return all_an

    def get_log_sources(self, ids: List[str]) -> List[Dict[str, Any]]:
        d = self._idx.get("log_sources_by_id", {})
        return [d[i] for i in ids if i in d]

    # Optional helpers (useful for fallbacks / debugging)
    def get_detection_text(self, tid: str) -> Optional[str]:
        tid = _parent_tid(tid)
        t = self._idx.get("techniques_by_id", {}).get(tid)
        return t.get("x_mitre_detection") if t else None

    def is_v18(self) -> bool:
        return self._is_v18


# ----------------------------------------------------------------------------
# Fetch & Cache
# ----------------------------------------------------------------------------
async def fetch_and_cache(session_get) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    if not os.path.exists(CACHE_PATH):
        status, text = await session_get(DEFAULT_URL)
        if status == 200 and text:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                f.write(text)
            return json.loads(text)
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError("ATT&CK JSON unavailable and no cache present")


# ----------------------------------------------------------------------------
# Indexing
# ----------------------------------------------------------------------------

def index_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    objs: List[Dict[str, Any]] = [o for bundle_obj in bundle.get("objects", []) if not o.get("revoked", False)]

    # Base indices
    techniques_by_id: Dict[str, Dict[str, Any]] = {}
    relationships_by_src: Dict[str, List[Dict[str, Any]]] = {}
    relationships_by_dst: Dict[str, List[Dict[str, Any]]] = {}

    # v18-ish indices (preferred)
    strategies_by_tid: Dict[str, List[Dict[str, Any]]] = {}
    analytics_by_id: Dict[str, Dict[str, Any]] = {}
    analytics_by_tid: Dict[str, List[Dict[str, Any]]] = {}
    data_components_by_id: Dict[str, Dict[str, Any]] = {}
    log_sources_by_id: Dict[str, Dict[str, Any]] = {}

    # Pass 1: collect objects & relationships
    for o in objs:
        typ = (o.get("type") or "").lower()
        if typ == "attack-pattern":
            tid = _extract_tid(o)
            if not tid:
                continue
            parent = _parent_tid(tid)
            techniques_by_id[parent] = {
                "technique_id": parent,
                "name": o.get("name", ""),
                "x_mitre_detection": o.get("x_mitre_detection"),
                "id": o.get("id"),
            }
        elif typ == "relationship":
            src = o.get("source_ref")
            dst = o.get("target_ref")
            if src and dst:
                relationships_by_src.setdefault(src, []).append(o)
                relationships_by_dst.setdefault(dst, []).append(o)
        elif typ in ("x-mitre-data-component", "x_mitre_data_component"):
            data_components_by_id[o.get("id")] = o
        elif "analytic" in typ:  # x-mitre-analytic
            analytics_by_id[o.get("id")] = o

    # Detect v18 presence: any detection-strategy SDOs or x-mitre-analytic
    has_v18_strategy = any((o.get("type") or "").lower() in ("x-mitre-detection-strategy", "x_mitre_detection_strategy") for o in objs)
    has_v18_analytic = bool(analytics_by_id)
    has_v18 = has_v18_strategy or has_v18_analytic

    # Build v18 indices if present
    if has_v18:
        # a) First, collect strategies w/ friendly DET id
        strategies_by_id: Dict[str, Dict[str, Any]] = {}
        for o in objs:
            typ = (o.get("type") or "").lower()
            if typ in ("x-mitre-detection-strategy", "x_mitre_detection_strategy"):
                det_id = None
                for er in (o.get("external_references") or []):
                    ext = er.get("external_id", "") or ""
                    m = re.match(r'^DET-?(\d{4})$', str(ext).strip(), flags=re.IGNORECASE)
                    if m:
                        det_id = f"DET{m.group(1)}"  # normalize to DET0001
                        break

                strategies_by_id[o.get("id")] = {
                    "obj": o,
                    "det_id": det_id,
                }

        # b) Map strategies to techniques via explicit detects relationships (if present)
        for s_id, pack in strategies_by_id.items():
            s_obj = pack["obj"]
            det_id = pack["det_id"]
            s_row = {
                "id": s_id,
                "name": s_obj.get("name", ""),
                "summary": s_obj.get("description", ""),
                "external_references": s_obj.get("external_references", []),
                "det_id": det_id,
            }
            for rel in relationships_by_src.get(s_id, []):
                if (rel.get("relationship_type") or "").lower() != "detects":
                    continue
                tgt = rel.get("target_ref")
                t_tid = _tid_from_attack_pattern_id(tgt, techniques_by_id)
                if not t_tid:
                    continue
                p_tid = _parent_tid(t_tid)
                strategies_by_tid.setdefault(t_tid, []).append(s_row)
                if t_tid != p_tid:
                    strategies_by_tid.setdefault(p_tid, []).append(s_row)

        # c) Regardless of relationships, also bind strategies/analytics to techniques by
        #    extracting TIDs from each referenced analytic's id/name/refs.
        for s_id, pack in strategies_by_id.items():
            s_obj = pack["obj"]
            det_id = pack["det_id"]
            s_row = {
                "id": s_id,
                "name": s_obj.get("name", ""),
                "summary": s_obj.get("description", ""),
                "external_references": s_obj.get("external_references", []),
                "det_id": det_id,
            }

            analytic_refs = (
                s_obj.get("x_mitre_analytic_refs")
                or s_obj.get("x_mitre_analytics")
                or []
            )
            for a_ref in analytic_refs:
                a_obj = analytics_by_id.get(a_ref)
                if not a_obj:
                    continue

                # Normalize analytic (adds an_id, platforms, dc_elements, etc.)
                a_row, ls_ids, dc_elems = _normalize_analytic(a_obj, data_components_by_id)
                a_row["log_source_ids"] = ls_ids
                a_row["dc_elements"] = dc_elems
                a_row["det_id"] = det_id  # stamp parent DET on each analytic row

                tids = _extract_tids_from_analytic(a_obj)
                if not tids:
                    continue
                for tid in tids:
                    parent = _parent_tid(tid)
                    # index under both exact and parent to help callers
                    for key in (tid, parent):
                        analytics_by_tid.setdefault(key, []).append(a_row)
                        strategies_by_tid.setdefault(key, []).append(s_row)

        # d) Also include any analytics that declare technique refs directly (outside strategies)
        for a_obj in analytics_by_id.values():
            tids = _rel_tids(a_obj)
            if not tids:
                continue
            a_row, ls_ids, dc_elems = _normalize_analytic(a_obj, data_components_by_id)
            a_row["log_source_ids"] = ls_ids
            a_row["dc_elements"] = dc_elems
            for tid in tids:
                for key in (tid, _parent_tid(tid)):
                    analytics_by_tid.setdefault(key, []).append(a_row)

        # e) Flatten log sources from data components
        for dc_id, dc in data_components_by_id.items():
            for i, ls in enumerate(dc.get("x_mitre_log_sources", []) or []):
                sid = f"{dc_id}#ls{i}"
                log_sources_by_id[sid] = {
                    "id": sid,
                    "name": ls.get("name") or ls.get("channel") or "log-source",
                    "channel": ls.get("channel"),
                    "notes": ls.get("description") or "",
                }

    # v17.1 fallback: synthesize analytics from data components + detection text
    else:
        # Heuristics: older bundles sometimes use relationships from data-component -> attack-pattern ("detects")
        for dc_id, dc in data_components_by_id.items():
            # which techniques does this DC detect?
            rels = relationships_by_src.get(dc_id, [])
            for rel in rels:
                if (rel.get("relationship_type") or "").lower() != "detects":
                    continue
                t_tid = _tid_from_attack_pattern_id(rel.get("target_ref"), techniques_by_id)
                if not t_tid:
                    continue
                parent = _parent_tid(t_tid)
                # create synthetic analytic row from DC name, attach DC's log_sources if present
                a_row = {
                    "id": f"synthetic-analytic::{dc_id}",
                    "name": dc.get("name", "Data Component"),
                    "platform": "",
                    "statement": (dc.get("description") or ""),
                    "tunables": [],
                }
                # turn DC's log sources into flattened ids
                ls_ids: List[str] = []
                for i, ls in enumerate(dc.get("x_mitre_log_sources", []) or []):
                    sid = f"{dc_id}#ls{i}"
                    log_sources_by_id.setdefault(sid, {
                        "id": sid,
                        "name": ls.get("name") or ls.get("channel") or "log-source",
                        "channel": ls.get("channel"),
                        "notes": ls.get("description") or "",
                    })
                    ls_ids.append(sid)
                a_row["log_source_ids"] = ls_ids
                a_row["dc_elements"] = []
                analytics_by_tid.setdefault(parent, []).append(a_row)

        # Also index technique detection text so callers can show it if desired
        # (already stored in techniques_by_id)

    # De-dup analytics per technique while preserving order (by id)
    for tid, items in list(analytics_by_tid.items()):
        seen: set = set()
        dedup: List[Dict[str, Any]] = []
        for a in items:
            aid = a.get("id")
            if aid in seen:
                continue
            seen.add(aid)
            dedup.append(a)
        analytics_by_tid[tid] = dedup

    # === DEDUPE Again: strategies_by_tid (by id + det_id) ===
    for tid, items in list(strategies_by_tid.items()):
        seen = set()
        out = []
        for s in items:
            key = (s.get("id"), s.get("det_id"))
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
        strategies_by_tid[tid] = out

    return {
        "has_v18": has_v18,
        "techniques_by_id": techniques_by_id,
        "strategies_by_tid": strategies_by_tid,
        "analytics_by_tid": analytics_by_tid,
        "log_sources_by_id": log_sources_by_id,
    }


# ----------------------------------------------------------------------------
# Loader
# ----------------------------------------------------------------------------

def load_attack18_cache(path: str):
    """Load ATT&CK v18 cache and normalize shape if needed."""
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    if isinstance(raw, list):
        raw = {"type": "bundle", "objects": raw}
    elif not isinstance(raw, dict):
        raise TypeError(f"Unexpected ATT&CK cache type: {type(raw).__name__}")
    return raw


async def load_attack18_map(session_get) -> Attack18Map:
    bundle = await fetch_and_cache(session_get)
    return Attack18Map(index_bundle(bundle))


# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------

def _parent_tid(tid: str) -> str:
    return (tid or "").split(".")[0].upper() if tid else ""


def _extract_tid(o: Dict[str, Any]) -> Optional[str]:
    for ref in o.get("external_references", []) or []:
        if ref.get("source_name") == "mitre-attack" and str(ref.get("external_id", "")).startswith("T"):
            return ref.get("external_id")
    return None


def _tid_from_attack_pattern_id(ap_id: Optional[str], techniques_by_id: Dict[str, Dict[str, Any]]) -> Optional[str]:
    if not ap_id:
        return None
    # reverse lookup by internal id
    for tid, t in techniques_by_id.items():
        if t.get("id") == ap_id:
            return tid
    return None


def _rel_tids(x: Dict[str, Any]) -> List[str]:
    out = set()
    # 1) explicit technique refs in external_refs
    for ref in x.get("external_references", []) or []:
        eid = str(ref.get("external_id", "") or "")
        if ref.get("source_name") == "mitre-attack" and eid.startswith("T"):
            out.add(eid.upper())
    # 2) explicit technique refs in fields
    for k in ("technique_refs", "x_mitre_technique_refs", "attack_pattern_refs"):
        for tid in x.get(k, []) or []:
            if isinstance(tid, str) and tid.startswith("T"):
                out.add(tid.upper())
    # 3) heuristic from id/name
    sid = str(x.get("id", "") or "")
    sname = str(x.get("name", "") or "")
    for m in re.findall(r'(T\d{4}(?:\.\d{3})?)', sid + " " + sname, flags=re.IGNORECASE):
        out.add(m.upper())
    return list(out)


def _normalize_analytic(
    a: Dict[str, Any],
    data_components_by_id: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[str], List[Dict[str, Any]]]:
    # keep both primary and full list for better per-OS filtering downstream
    plats = a.get("x_mitre_platforms") or a.get("platform") or []
    if isinstance(plats, str):
        plats = [plats]
    plats_norm = [str(p).lower() for p in plats if p]
    plat_primary = (plats_norm[0] if plats_norm else "")

    row = {
        "id": a.get("id"),
        "name": a.get("name", ""),
        "platform": plat_primary,          # for existing callers
        "platforms": plats_norm,           # for improved filtering
        "statement": a.get("description", ""),
        "tunables": a.get("x_mitre_mutable_elements") or a.get("x_mitre_tunable_parameters") or a.get("tunables") or [],
    }

    # derive a clean AN#### for display if present in external refs or name
    an_id = None
    for er in (a.get("external_references") or []):
        ext = er.get("external_id", "")
        m = re.match(r'^AN-?(\d{4})$', str(ext).strip(), flags=re.IGNORECASE)
        if m:
            an_id = f'AN{m.group(1)}'  # normalize to AN0001
            break
        an_id = ext
        break
    if not an_id:
        m = re.search(r'Analytic (\d{4})', a.get("name", "") or "")
        if m:
            an_id = f'AN{m.group(1)}'  # normalize to AN0001
    row["an_id"] = an_id

    # extract linked data components & their log source ids
    ls_ids: List[str] = []
    dc_elements: List[Dict[str, Any]] = []
    for ref in (a.get("x_mitre_log_source_references") or []):
        dc_ref = ref.get("x_mitre_data_component_ref")
        dc_refs = [dc_ref] if dc_ref else (ref.get("x_mitre_data_component_refs") or [])
        for dc_id in dc_refs:
            dc = data_components_by_id.get(dc_id)
            if not dc:
                continue
            dc_elements.append({
                "name": ref.get("name", ""),                          # e.g., "wineventlog:security" comes from ref['name'] if you use it elsewhere
                "channel": (ref.get("channel") or ""),               # channel only exists on the ref
                "data_component": dc.get("name", ""),                # <-- FIX: DC display (e.g., "Process Creation")
            })
            # keep any existing log-source indexing you rely on
            for i, _ in enumerate(dc.get("x_mitre_log_sources", []) or []):
                ls_ids.append(f"{dc_id}#ls{i}")

    return row, ls_ids, dc_elements

