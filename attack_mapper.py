import os, json, asyncio
from typing import Dict, List, Any, Optional

DEFAULT_URL = os.getenv(
    "ATTACK_V18_URL",
    "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
)
CACHE_PATH = os.getenv(
    "ATTACK_V18_CACHE",
    os.path.join(os.path.dirname(__file__), "..", "uploads", "attack18_cache.json")
)

class Attack18Map:
    def __init__(self, idx: Dict[str, Any]): self._idx = idx or {}
    def get_strategies(self, tid: str) -> List[Dict[str, Any]]:
        return self._idx.get("strategies_by_tid", {}).get(tid.split('.')[0], [])
    def get_analytics(self, tid: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        tid = tid.split('.')[0]; all_an = self._idx.get("analytics_by_tid", {}).get(tid, [])
        return [a for a in all_an if not platform or a.get("platform","").lower()==platform.lower()]
    def get_log_sources(self, ids: List[str]) -> List[Dict[str, Any]]:
        d = self._idx.get("log_sources_by_id", {}); return [d[i] for i in ids if i in d]

async def fetch_and_cache(session_get) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    # Try live
    try:
        status, text = await session_get(DEFAULT_URL)
        if status == 200 and text:
            with open(CACHE_PATH, "w", encoding="utf-8") as f: f.write(text)
            return json.loads(text)
    except Exception:
        pass
    # Fallback cache
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f: return json.load(f)
    raise RuntimeError("ATT&CK JSON unavailable and no cache present")

def index_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    objs = bundle.get("objects") or []
    techniques_by_id, strategies_by_tid, analytics_by_tid, log_sources_by_id = {}, {}, {}, {}

    # Techniques
    for o in objs:
        if o.get("type") != "attack-pattern": continue
        tid = None
        for ref in o.get("external_references", []) or []:
            if ref.get("source_name")=="mitre-attack": tid = ref.get("external_id")
        if not tid: continue
        parent = tid.split(".")[0]
        techniques_by_id.setdefault(parent, {"technique_id": parent, "name": o.get("name","")})

    # Log sources
    for o in objs:
        t = (o.get("type","") or "").lower()
        if "log" in t and "source" in t:
            log_sources_by_id[o.get("id")] = {"id": o.get("id"), "name": o.get("name",""), "notes": o.get("description","")}

    # Strategies and analytics (tolerant of naming)
    def rel_tids(x: Dict[str, Any]) -> List[str]:
        out=set()
        for ref in x.get("external_references",[]) or []:
            if ref.get("source_name")=="mitre-attack" and str(ref.get("external_id","")).startswith("T"):
                out.add(ref["external_id"])
        for k in ("technique_refs","x_mitre_technique_refs","attack_pattern_refs"):
            for tid in x.get(k,[]) or []:
                if isinstance(tid,str) and tid.startswith("T"): out.add(tid)
        return [t.split('.')[0] for t in out]

    for o in objs:
        t = (o.get("type","") or "").lower()
        # detection strategies
        if ("strategy" in t and "detect" in t) or t == "x-mitre-detection-strategy":
            row = {"id": o.get("id"), "name": o.get("name",""), "summary": o.get("description","")}
            for tid in rel_tids(o): strategies_by_tid.setdefault(tid, []).append(row)
        # analytics
        if "analytic" in t:
            plat = o.get("x_mitre_platforms") or o.get("platform") or ""
            plat = plat[0] if isinstance(plat, list) and plat else plat
            row = {
                "id": o.get("id"), "name": o.get("name",""),
                "platform": str(plat).lower(),
                "statement": o.get("description",""),
                "tunables": o.get("x_mitre_tunable_parameters") or o.get("tunables") or [],
                "log_source_ids": o.get("x_mitre_log_source_refs") or o.get("log_source_refs") or [],
            }
            for tid in rel_tids(o): analytics_by_tid.setdefault(tid, []).append(row)

    return {
        "techniques_by_id": techniques_by_id,
        "strategies_by_tid": strategies_by_tid,
        "analytics_by_tid": analytics_by_tid,
        "log_sources_by_id": log_sources_by_id,
    }

async def load_attack18_map(session_get) -> Attack18Map:
    bundle = await fetch_and_cache(session_get)
    return Attack18Map(index_bundle(bundle))
