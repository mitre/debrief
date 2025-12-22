import aiohttp
import json
import os
import re

from typing import Dict, List, Any, Optional, Tuple

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
DEFAULT_URL = os.getenv(
    'ATTACK_V18_URL',
    'https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json',
)
CACHE_PATH = os.getenv(
    'ATTACK_V18_CACHE',
    os.path.join(os.path.dirname(__file__), 'uploads', 'attack18_cache.json'),
)

_TID_RX = re.compile(r'(T\d{4}(?:\.\d{3})?)', re.IGNORECASE)


# ----------------------------------------------------------------------------
# Public Map API
# ----------------------------------------------------------------------------
class Attack18Map:
    '''Unified view over ATT&CK v18 bundles.

    Exposes stable helpers used by the report section:
      - get_strategies(tid)
      - get_parent_strategies(tid)
      - get_analytics(tid, platform=None)
      - get_parent_analytics(tid, platform=None)

    On v18 bundles, these map to Detection Strategies / Analytics / DC log-sources.
    '''

    def __init__(self, idx: Dict[str, Any]):
        self._idx = idx or {}
        self.techniques_by_id = self._idx.get('techniques_by_id', {})
        self.strategies_by_tid = self._idx.get('strategies_by_tid', {})
        self.analytics_by_tid = self._idx.get('analytics_by_tid', {})

    # ------------------------------ Public ----------------------------------
    def get_strategies(self, tid):
        return self.strategies_by_tid.get(tid, [])

    def get_parent_strategies(self, tid: str) -> List[Dict[str, Any]]:
        parent_tid = _parent_tid((tid or '').strip().upper())
        return self.get_strategies(parent_tid)

    def get_analytics(self, tid: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        key = (tid or '').strip().upper()
        all_an = self._idx.get('analytics_by_tid', {}).get(key, [])
        if platform:
            p = platform.lower()

            def _match(row):
                plats = (row.get('platforms') or [])
                prim = (row.get('platform') or '')
                return (p in plats) or (prim in ('', None, p))
            return [a for a in all_an if _match(a)]
        return all_an

    def get_parent_analytics(self, tid: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        parent_tid = _parent_tid((tid or '').strip().upper())
        return self.get_analytics(parent_tid, platform=platform)


class NormalizeAnalyticException(Exception):
    pass


# ----------------------------------------------------------------------------
# Fetch & Cache
# ----------------------------------------------------------------------------
async def fetch_and_cache(session_get, url=DEFAULT_URL, path=CACHE_PATH, timeout=aiohttp.ClientTimeout(total=30)) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        async with session_get(url, timeout=timeout) as resp:
            status = resp.status
            text = await resp.text()
        if status == 200:
            if text:
                with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                    f.write(text)
                return
            else:
                raise RuntimeError('Empty response - no JSON text found.')
        else:
            raise RuntimeError(f'Non-200 HTTP status code returned when fetching JSON blob from {url}: {status}.')
    raise RuntimeError('ATT&CK JSON unavailable and no cache present')


# ----------------------------------------------------------------------------
# Indexing
# ----------------------------------------------------------------------------
def index_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Index a MITRE ATT&CK v18+ STIX bundle into lookup tables used by the
    reporting and detection modules.

    This builds:
        techniques_by_id     : { 'T1041': {...}, 'T1074.001': {...}, ... }
        strategies_by_tid    : { 'T1041': [DET strategies], ... }
        analytics_by_tid     : { 'T1041': [analytic rows], ... }

    Expected ATT&CK v18 content:
        - x-mitre-detection-strategy SDOs
        - x-mitre-analytic SDOs
        - Optional: STIX 'relationship' objects of type 'detects'
        - analytics referenced via 'x_mitre_analytic_refs'
        - strategies/techniques referenced via external_references (DET###, T####)

    This implementation:
        1. Collects all objects
        2. Extracts techniques, data components, detection strategies, analytics
        3. Collects relationships (needed for debug and future expansion)
        4. Verifies that v18 content exists
        5. For each detection strategy:
            - normalize DET ID
            - collect analytics via x_mitre_analytic_refs
            - map strategy → techniques based on external_references containing T#### IDs
        6. Deduplicates all lists
    '''
    # Skip revoked objects
    objs = [o for o in bundle.get('objects', []) if not o.get('revoked', False)]

    # ----------------------------------------------------------------------
    # INITIAL INDEX DICTS
    # ----------------------------------------------------------------------
    techniques_by_id: Dict[str, Dict[str, Any]] = {}
    attack_pattern_id_to_tid: Dict[str, str] = {}
    data_components_by_id: Dict[str, Dict[str, Any]] = {}

    strategies_by_id: Dict[str, Dict[str, Any]] = {}
    strategies_by_tid: Dict[str, List[Dict[str, Any]]] = {}

    analytics_by_id: Dict[str, Dict[str, Any]] = {}
    analytics_by_tid: Dict[str, List[Dict[str, Any]]] = {}

    # Relationship indices (STIX relationship SROs)
    relationships_by_src: Dict[str, List[Dict[str, Any]]] = {}
    relationships_by_dst: Dict[str, List[Dict[str, Any]]] = {}

    # ----------------------------------------------------------------------
    # PASS 1 — Collect Techniques, Data Components, Strategies, Analytics, Relationships
    # ----------------------------------------------------------------------
    for o in objs:
        typ = o.get('type', '').lower()

        # Techniques (attack-pattern)
        if typ == 'attack-pattern':
            tid = _extract_tid(o)
            if tid:
                techniques_by_id[tid] = {
                    'technique_id': tid,
                    'name': o.get('name', ''),
                    'ap_id': o.get('id'),
                }
                attack_pattern_id_to_tid[o.get('id')] = tid

        # Relationships (may include 'detects' but some ATT&CK bundles omit these)
        elif typ == 'relationship':
            src = o.get('source_ref')
            dst = o.get('target_ref')
            if src and dst:
                relationships_by_src.setdefault(src, []).append(o)
                relationships_by_dst.setdefault(dst, []).append(o)

        # Data Components
        elif typ == 'x-mitre-data-component':
            data_components_by_id[o.get('id')] = o

        # Detection Strategy SDO
        elif typ == 'x-mitre-detection-strategy':
            det_id = None
            for er in o.get('external_references', []):
                ext_id = er.get('external_id', '')
                m = re.match(r'^DET-?(\d{4})$', str(ext_id).strip(), flags=re.IGNORECASE)
                if m:
                    det_id = f'DET{m.group(1)}'   # Normalize DET-0012 → DET0012 (no dash)
                    break

            if det_id:
                strategies_by_id[o.get('id')] = {
                    'obj': o,
                    'det_id': det_id,
                }

        # Analytics SDO
        elif typ == 'x-mitre-analytic':
            analytics_by_id[o.get('id')] = o

    # ----------------------------------------------------------------------
    # VALIDATE — If NO detection strategies AND NO analytics exist, bundle is not v18+
    # ----------------------------------------------------------------------
    if not (strategies_by_id or analytics_by_id):
        raise Exception(
            'ATT&CK bundle JSON missing v18+ elements (x-mitre-detection-strategy or x-mitre-analytic). '
            'Please supply ATT&CK v18 or newer.'
        )

    # ----------------------------------------------------------------------
    # PASS 2 — Map detection strategies → techniques → analytics
    # ----------------------------------------------------------------------
    for s_id, pack in strategies_by_id.items():
        s_obj = pack['obj']
        det_id = pack['det_id']

        # Strategy row stored per technique
        s_row = {
            'id': s_id,
            'name': s_obj.get('name', ''),
            'external_references': s_obj.get('external_references', []),
            'det_id': det_id,
        }

        # Collect analytics referenced by this strategy
        strat_analytic_rows = []
        for a_ref in s_obj.get('x_mitre_analytic_refs', []):
            a_obj = analytics_by_id.get(a_ref)
            if not a_obj:
                continue

            try:
                a_row, dc_elems = _normalize_analytic(a_obj, data_components_by_id)
            except NormalizeAnalyticException:
                continue

            a_row['dc_elements'] = dc_elems
            a_row['det_id'] = det_id
            strat_analytic_rows.append(a_row)

        # Technique mapping via external_references (preferred for ATT&CK v18)
        for rel in relationships_by_src.get(s_id, []):
            if rel.get('relationship_type', '').lower() != 'detects':
                continue

            target_ap = rel.get('target_ref')
            tid = attack_pattern_id_to_tid.get(target_ap)
            if not tid:
                continue

            # Map the strategy
            strategies_by_tid.setdefault(tid, []).append(s_row)

            # Map its analytics
            analytics_by_tid.setdefault(tid, []).extend(strat_analytic_rows)

    # ----------------------------------------------------------------------
    # PASS 3 — Deduplicate analytics & strategies
    # ----------------------------------------------------------------------
    for tid, items in analytics_by_tid.items():
        seen, out = set(), []
        for a in items:
            sig = a.get('id')
            if sig not in seen:
                seen.add(sig)
                out.append(a)
        analytics_by_tid[tid] = out

    for tid, items in strategies_by_tid.items():
        seen, out = set(), []
        for s in items:
            key = (s.get('id'), s.get('det_id'))
            if key not in seen:
                seen.add(key)
                out.append(s)
        strategies_by_tid[tid] = out

    # ----------------------------------------------------------------------
    # RETURN INDEX STRUCTURE
    # ----------------------------------------------------------------------
    return {
        'techniques_by_id': techniques_by_id,
        'strategies_by_tid': strategies_by_tid,
        'analytics_by_tid': analytics_by_tid,
    }


# ----------------------------------------------------------------------------
# Loader
# ----------------------------------------------------------------------------
def load_attack18_cache(path: str):
    '''Load ATT&CK v18 cache and normalize shape if needed.'''
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    if isinstance(raw, list):
        raw = {'type': 'bundle', 'objects': raw}
    elif not isinstance(raw, dict):
        raise TypeError(f'Unexpected ATT&CK cache type: {type(raw).__name__}')
    return raw


# ----------------------------------------------------------------------------
# Global single-source loader for ATT&CK v18
# ----------------------------------------------------------------------------

_attack18_global: Optional[Attack18Map] = None


def get_attack18() -> Attack18Map:
    '''
    Return a shared Attack18Map instance.
    Ensures the ATT&CK v18 bundle is loaded and indexed once per process.
    Consumers (TTT, Detections, Debrief GUI) should use only this.
    '''
    global _attack18_global
    if _attack18_global is not None:
        return _attack18_global

    # 1: Load bundle from cache (no network, fully offline)
    if not os.path.exists(CACHE_PATH):
        raise FileNotFoundError(f'ATT&CK v18 cache missing: {CACHE_PATH}')

    raw = load_attack18_cache(CACHE_PATH)

    # 3: Build the indexed map (canonical unified structure)
    _attack18_global = Attack18Map(index_bundle(raw))
    return _attack18_global


# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------

def _parent_tid(tid: str) -> str:
    return (tid or '').split('.')[0].upper() if tid else ''


def _extract_tid(o: Dict[str, Any]) -> Optional[str]:
    for ref in o.get('external_references', []) or []:
        if ref.get('source_name') == 'mitre-attack' and str(ref.get('external_id', '')).startswith('T'):
            return ref.get('external_id')
    return None


def _normalize_analytic(
    a: Dict[str, Any],
    data_components_by_id: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    # keep both primary and full list for better per-OS filtering downstream
    plats = a.get('x_mitre_platforms') or a.get('platform') or []
    if isinstance(plats, str):
        plats = [plats]
    plats_norm = [str(p).lower() for p in plats if p]
    plat_primary = (plats_norm[0] if plats_norm else '')

    row = {
        'id': a.get('id'),
        'name': a.get('name', ''),
        'platform': plat_primary,          # for existing callers
        'platforms': plats_norm,           # for improved filtering
        'statement': a.get('description', ''),
        'tunables': a.get('x_mitre_mutable_elements', []),
    }

    # derive a clean AN#### for display if present in external refs or name
    an_id = None
    for ext_ref in a.get('external_references', []):
        ext_id = ext_ref.get('external_id', '')
        m = re.match(r'^AN-?(\d{4})$', str(ext_id).strip(), flags=re.IGNORECASE)
        if m:
            an_id = f'AN{m.group(1)}'  # normalize to AN0001
            break
    if not an_id:
        m = re.search(r'Analytic (\d{4})', a.get('name', '') or '')
        if m:
            an_id = f'AN{m.group(1)}'  # normalize to AN0001

    if not an_id:
        raise NormalizeAnalyticException('Failed to parse analytic ID from analytic object.')

    row['an_id'] = an_id

    # extract linked log sources with data components info
    dc_elements: List[Dict[str, Any]] = []
    for log_ref in a.get('x_mitre_log_source_references', []):
        dc_ref = log_ref.get('x_mitre_data_component_ref')
        dc_refs = [dc_ref] if dc_ref else log_ref.get('x_mitre_data_component_refs', [])
        for dc_id in dc_refs:
            dc = data_components_by_id.get(dc_id)
            if not dc:
                continue
            dc_elements.append({
                'name': log_ref.get('name', ''),  # e.g. 'wineventlog:security'
                'channel': log_ref.get('channel', ''),  # channel only exists in the log ref
                'data_component': dc.get('name', ''),  # DC display (e.g., 'Process Creation')
            })

    return row, dc_elements
