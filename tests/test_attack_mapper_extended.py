"""Extended tests for attack_mapper.py — covers Attack18Map, index_bundle, utilities, fetch_and_cache."""
import pytest
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from plugins.debrief.attack_mapper import (
    Attack18Map,
    NormalizeAnalyticException,
    index_bundle,
    fetch_and_cache,
    load_attack18_cache,
    get_attack18,
    _parent_tid,
    _extract_tid,
    _normalize_analytic,
    CACHE_PATH,
)


# ===========================================================================
# Attack18Map
# ===========================================================================
class TestAttack18Map:
    def test_empty_init(self):
        m = Attack18Map({})
        assert m.techniques_by_id == {}
        assert m.strategies_by_tid == {}
        assert m.analytics_by_tid == {}

    def test_none_init(self):
        m = Attack18Map(None)
        assert m.techniques_by_id == {}

    def test_get_strategies_present(self, populated_attack18_map):
        result = populated_attack18_map.get_strategies('T1082')
        assert len(result) == 1
        assert result[0]['det_id'] == 'DET0001'

    def test_get_strategies_missing(self, populated_attack18_map):
        result = populated_attack18_map.get_strategies('T9999')
        assert result == []

    def test_get_parent_strategies(self, populated_attack18_map):
        result = populated_attack18_map.get_parent_strategies('T1547.001')
        assert len(result) == 1
        assert result[0]['det_id'] == 'DET0002'

    def test_get_parent_strategies_no_sub(self, populated_attack18_map):
        result = populated_attack18_map.get_parent_strategies('T1082')
        assert len(result) == 1  # parent of T1082 is T1082

    def test_get_analytics(self, populated_attack18_map):
        result = populated_attack18_map.get_analytics('T1082')
        assert len(result) == 1

    def test_get_analytics_with_platform_filter(self, populated_attack18_map):
        result = populated_attack18_map.get_analytics('T1082', platform='windows')
        assert len(result) == 1

    def test_get_analytics_wrong_platform(self, populated_attack18_map):
        result = populated_attack18_map.get_analytics('T1082', platform='macos')
        assert len(result) == 0

    def test_get_analytics_missing_tid(self, populated_attack18_map):
        result = populated_attack18_map.get_analytics('T9999')
        assert result == []

    def test_get_parent_analytics(self, populated_attack18_map):
        result = populated_attack18_map.get_parent_analytics('T1082.001', platform='windows')
        # Parent is T1082
        assert len(result) == 1

    def test_get_analytics_empty_platform(self, populated_attack18_map):
        result = populated_attack18_map.get_analytics('T1082', platform='')
        assert len(result) == 1  # Empty platform returns all


# ===========================================================================
# _parent_tid
# ===========================================================================
class TestParentTid:
    def test_main_technique(self):
        assert _parent_tid('T1082') == 'T1082'

    def test_subtechnique(self):
        assert _parent_tid('T1547.001') == 'T1547'

    def test_empty(self):
        assert _parent_tid('') == ''

    def test_none(self):
        assert _parent_tid(None) == ''

    def test_lowercase(self):
        assert _parent_tid('t1082') == 'T1082'


# ===========================================================================
# _extract_tid
# ===========================================================================
class TestExtractTid:
    def test_valid_technique(self):
        obj = {'external_references': [
            {'source_name': 'mitre-attack', 'external_id': 'T1082'}
        ]}
        assert _extract_tid(obj) == 'T1082'

    def test_no_mitre_source(self):
        obj = {'external_references': [
            {'source_name': 'other', 'external_id': 'T1082'}
        ]}
        assert _extract_tid(obj) is None

    def test_no_external_refs(self):
        assert _extract_tid({}) is None
        assert _extract_tid({'external_references': None}) is None

    def test_non_technique_id(self):
        obj = {'external_references': [
            {'source_name': 'mitre-attack', 'external_id': 'S0001'}
        ]}
        assert _extract_tid(obj) is None

    def test_subtechnique(self):
        obj = {'external_references': [
            {'source_name': 'mitre-attack', 'external_id': 'T1547.001'}
        ]}
        assert _extract_tid(obj) == 'T1547.001'


# ===========================================================================
# _normalize_analytic
# ===========================================================================
class TestNormalizeAnalytic:
    def test_basic_analytic(self):
        a = {
            'id': 'analytic--1',
            'name': 'Analytic 0001',
            'description': 'Test statement',
            'x_mitre_platforms': ['windows'],
            'x_mitre_mutable_elements': [],
            'external_references': [{'external_id': 'AN0001'}],
            'x_mitre_log_source_references': [],
        }
        row, dcs = _normalize_analytic(a, {})
        assert row['an_id'] == 'AN0001'
        assert row['platform'] == 'windows'
        assert row['platforms'] == ['windows']
        assert row['statement'] == 'Test statement'
        assert dcs == []

    def test_analytic_with_dash_in_id(self):
        a = {
            'id': 'analytic--1',
            'name': 'Analytic 0001',
            'external_references': [{'external_id': 'AN-0001'}],
            'x_mitre_log_source_references': [],
        }
        row, _ = _normalize_analytic(a, {})
        assert row['an_id'] == 'AN0001'

    def test_analytic_id_from_name_fallback(self):
        a = {
            'id': 'analytic--1',
            'name': 'Analytic 0042',
            'external_references': [],
            'x_mitre_log_source_references': [],
        }
        row, _ = _normalize_analytic(a, {})
        assert row['an_id'] == 'AN0042'

    def test_raises_if_no_id(self):
        a = {
            'id': 'analytic--1',
            'name': 'NoIdHere',
            'external_references': [],
            'x_mitre_log_source_references': [],
        }
        with pytest.raises(NormalizeAnalyticException):
            _normalize_analytic(a, {})

    def test_with_data_components(self):
        dc_id = 'dc-1'
        dc = {'name': 'Process Creation'}
        a = {
            'id': 'analytic--1',
            'name': 'Analytic 0001',
            'external_references': [{'external_id': 'AN0001'}],
            'x_mitre_log_source_references': [
                {
                    'name': 'WinEventLog:Security',
                    'channel': '4688',
                    'x_mitre_data_component_ref': dc_id,
                }
            ],
        }
        row, dcs = _normalize_analytic(a, {dc_id: dc})
        assert len(dcs) == 1
        assert dcs[0]['data_component'] == 'Process Creation'

    def test_multi_platform(self):
        a = {
            'id': 'analytic--1',
            'name': 'Analytic 0001',
            'x_mitre_platforms': ['windows', 'linux'],
            'external_references': [{'external_id': 'AN0001'}],
            'x_mitre_log_source_references': [],
        }
        row, _ = _normalize_analytic(a, {})
        assert row['platforms'] == ['windows', 'linux']
        assert row['platform'] == 'windows'

    def test_string_platform(self):
        a = {
            'id': 'analytic--1',
            'name': 'Analytic 0001',
            'platform': 'Linux',
            'external_references': [{'external_id': 'AN0001'}],
            'x_mitre_log_source_references': [],
        }
        row, _ = _normalize_analytic(a, {})
        assert row['platform'] == 'linux'


# ===========================================================================
# index_bundle
# ===========================================================================
class TestIndexBundle:
    def _make_bundle(self, objects):
        return {'type': 'bundle', 'objects': objects}

    def test_empty_bundle_raises(self):
        with pytest.raises(Exception, match='v18'):
            index_bundle(self._make_bundle([]))

    def test_no_strategies_or_analytics_raises(self):
        bundle = self._make_bundle([
            {'type': 'attack-pattern', 'id': 'ap-1',
             'external_references': [{'source_name': 'mitre-attack', 'external_id': 'T1082'}]},
        ])
        with pytest.raises(Exception, match='v18'):
            index_bundle(bundle)

    def test_revoked_objects_skipped(self):
        bundle = self._make_bundle([
            {'type': 'x-mitre-detection-strategy', 'id': 'ds-1', 'revoked': True,
             'external_references': [{'external_id': 'DET0001'}]},
            {'type': 'x-mitre-analytic', 'id': 'an-1', 'revoked': False,
             'name': 'Analytic 0001', 'external_references': [{'external_id': 'AN0001'}]},
        ])
        # Only analytic remains, which is enough to not raise
        idx = index_bundle(bundle)
        assert 'analytics_by_tid' in idx

    def test_indexes_techniques(self):
        bundle = self._make_bundle([
            {'type': 'attack-pattern', 'id': 'ap-1',
             'name': 'SysInfo',
             'external_references': [{'source_name': 'mitre-attack', 'external_id': 'T1082'}]},
            {'type': 'x-mitre-analytic', 'id': 'an-1',
             'name': 'Analytic 0001',
             'external_references': [{'external_id': 'AN0001'}]},
        ])
        idx = index_bundle(bundle)
        assert 'T1082' in idx['techniques_by_id']

    def test_strategy_det_id_normalization(self):
        bundle = self._make_bundle([
            {'type': 'x-mitre-detection-strategy', 'id': 'ds-1',
             'name': 'Test Strat',
             'external_references': [{'external_id': 'DET-0012'}],
             'x_mitre_analytic_refs': []},
            {'type': 'x-mitre-analytic', 'id': 'an-1',
             'name': 'Analytic 0001',
             'external_references': [{'external_id': 'AN0001'}]},
        ])
        idx = index_bundle(bundle)
        # DET-0012 should be normalized to DET0012
        assert idx is not None
        all_det_ids = [
            s.get('det_id', '') for strats in idx.get('strategies_by_tid', {}).values() for s in strats
        ]
        assert any('DET0012' in d for d in all_det_ids), (
            f"Expected normalized DET0012 in strategies, got: {all_det_ids}"
        )

    def test_full_strategy_to_technique_mapping(self):
        bundle = self._make_bundle([
            {'type': 'attack-pattern', 'id': 'ap-1', 'name': 'T',
             'external_references': [{'source_name': 'mitre-attack', 'external_id': 'T1082'}]},
            {'type': 'x-mitre-detection-strategy', 'id': 'ds-1', 'name': 'S',
             'external_references': [{'external_id': 'DET0001'}],
             'x_mitre_analytic_refs': ['an-1']},
            {'type': 'x-mitre-analytic', 'id': 'an-1', 'name': 'Analytic 0001',
             'external_references': [{'external_id': 'AN0001'}],
             'x_mitre_platforms': ['windows'],
             'x_mitre_log_source_references': []},
            {'type': 'relationship', 'id': 'rel-1',
             'source_ref': 'ds-1', 'target_ref': 'ap-1',
             'relationship_type': 'detects'},
        ])
        idx = index_bundle(bundle)
        assert 'T1082' in idx['strategies_by_tid']
        assert 'T1082' in idx['analytics_by_tid']
        assert len(idx['analytics_by_tid']['T1082']) == 1

    def test_deduplication(self):
        bundle = self._make_bundle([
            {'type': 'attack-pattern', 'id': 'ap-1', 'name': 'T',
             'external_references': [{'source_name': 'mitre-attack', 'external_id': 'T1082'}]},
            {'type': 'x-mitre-detection-strategy', 'id': 'ds-1', 'name': 'S',
             'external_references': [{'external_id': 'DET0001'}],
             'x_mitre_analytic_refs': ['an-1']},
            {'type': 'x-mitre-analytic', 'id': 'an-1', 'name': 'Analytic 0001',
             'external_references': [{'external_id': 'AN0001'}],
             'x_mitre_platforms': ['windows'],
             'x_mitre_log_source_references': []},
            # Two relationships to same technique
            {'type': 'relationship', 'source_ref': 'ds-1', 'target_ref': 'ap-1',
             'relationship_type': 'detects'},
            {'type': 'relationship', 'source_ref': 'ds-1', 'target_ref': 'ap-1',
             'relationship_type': 'detects'},
        ])
        idx = index_bundle(bundle)
        # Deduplication should keep only one
        assert len(idx['analytics_by_tid']['T1082']) == 1
        assert len(idx['strategies_by_tid']['T1082']) == 1


# ===========================================================================
# load_attack18_cache
# ===========================================================================
class TestLoadAttack18Cache:
    def test_load_dict(self, tmp_path):
        p = tmp_path / 'cache.json'
        p.write_text(json.dumps({'type': 'bundle', 'objects': []}))
        result = load_attack18_cache(str(p))
        assert result['type'] == 'bundle'

    def test_load_list_becomes_bundle(self, tmp_path):
        p = tmp_path / 'cache.json'
        p.write_text(json.dumps([{'type': 'attack-pattern'}]))
        result = load_attack18_cache(str(p))
        assert result['type'] == 'bundle'
        assert len(result['objects']) == 1

    def test_load_unexpected_type_raises(self, tmp_path):
        p = tmp_path / 'cache.json'
        p.write_text('"just a string"')
        with pytest.raises(TypeError, match='Unexpected'):
            load_attack18_cache(str(p))


# ===========================================================================
# fetch_and_cache
# ===========================================================================
class TestFetchAndCache:
    @pytest.mark.asyncio
    async def test_fetch_success(self, tmp_path):
        cache_path = str(tmp_path / 'cache.json')
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text = AsyncMock(return_value='{"type": "bundle"}')

        mock_session_get = MagicMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_session_get.return_value = mock_cm

        with patch('plugins.debrief.attack_mapper.CACHE_PATH', cache_path):
            await fetch_and_cache(mock_session_get, path=cache_path)
        assert os.path.exists(cache_path)

    @pytest.mark.asyncio
    async def test_fetch_already_cached(self, tmp_path):
        cache_path = str(tmp_path / 'cache.json')
        with open(cache_path, 'w') as f:
            f.write('{}')
        mock_session_get = MagicMock()
        await fetch_and_cache(mock_session_get, path=cache_path)
        mock_session_get.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_non_200(self, tmp_path):
        cache_path = str(tmp_path / 'no_cache.json')
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.text = AsyncMock(return_value='error')

        mock_session_get = MagicMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_session_get.return_value = mock_cm

        with pytest.raises(RuntimeError, match='Non-200'):
            await fetch_and_cache(mock_session_get, path=cache_path)

    @pytest.mark.asyncio
    async def test_fetch_empty_response(self, tmp_path):
        cache_path = str(tmp_path / 'no_cache.json')
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text = AsyncMock(return_value='')

        mock_session_get = MagicMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_session_get.return_value = mock_cm

        with pytest.raises(RuntimeError, match='Empty'):
            await fetch_and_cache(mock_session_get, path=cache_path)


# ===========================================================================
# get_attack18
# ===========================================================================
class TestGetAttack18:
    def test_cache_missing_raises(self, tmp_path):
        with patch('plugins.debrief.attack_mapper.CACHE_PATH', str(tmp_path / 'missing.json')), \
             patch('plugins.debrief.attack_mapper._attack18_global', None):
            with pytest.raises(FileNotFoundError):
                get_attack18()

    def test_returns_cached_instance(self):
        sentinel = Attack18Map({})
        with patch('plugins.debrief.attack_mapper._attack18_global', sentinel):
            assert get_attack18() is sentinel


# ===========================================================================
# NormalizeAnalyticException
# ===========================================================================
class TestNormalizeAnalyticException:
    def test_is_exception(self):
        ex = NormalizeAnalyticException('test')
        assert isinstance(ex, Exception)
        assert str(ex) == 'test'
