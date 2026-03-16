"""Tests for hook.py — plugin registration and ATT&CK cache init."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import plugins.debrief.hook as hook


class TestHookMetadata:
    def test_name(self):
        assert hook.name == 'Debrief'

    def test_description(self):
        assert hook.description == 'Operation debrief functionality'

    def test_address(self):
        assert hook.address == '/plugin/debrief/gui'

    def test_access(self):
        # Access should be RED
        assert hook.access is not None


class TestInitAttack18Cache:
    @pytest.mark.asyncio
    async def test_successful_cache_init(self):
        with patch('plugins.debrief.hook.fetch_and_cache', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            # Should not raise
            await hook._init_attack18_cache()
            mock_fetch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cache_init_failure_logged(self):
        with patch('plugins.debrief.hook.fetch_and_cache', new_callable=AsyncMock,
                   side_effect=Exception('network error')):
            with patch.object(hook.log, 'warning') as mock_warn:
                await hook._init_attack18_cache()
                mock_warn.assert_called_once()


class TestEnable:
    @pytest.mark.asyncio
    async def test_enable_registers_routes(self):
        mock_app = MagicMock()
        mock_router = MagicMock()
        mock_app.router = mock_router

        app_svc = MagicMock()
        app_svc.application = mock_app

        services = {
            'app_svc': app_svc,
            'auth_svc': MagicMock(),
            'data_svc': MagicMock(),
            'file_svc': MagicMock(),
            'knowledge_svc': MagicMock(),
        }

        with patch('plugins.debrief.hook.BaseWorld') as mock_bw, \
             patch('plugins.debrief.hook.DebriefGui') as mock_gui_cls, \
             patch('plugins.debrief.hook.asyncio.create_task') as mock_task:
            mock_bw.strip_yml.return_value = [{}]
            mock_gui_instance = MagicMock()
            mock_gui_cls.return_value = mock_gui_instance

            await hook.enable(services)

            # Check routes registered
            assert mock_router.add_route.call_count >= 7
            assert mock_router.add_static.call_count >= 2

            # Check cache warmup task created
            mock_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_applies_config(self):
        mock_app = MagicMock()
        mock_app.router = MagicMock()
        app_svc = MagicMock()
        app_svc.application = mock_app

        services = {
            'app_svc': app_svc,
            'auth_svc': MagicMock(),
            'data_svc': MagicMock(),
            'file_svc': MagicMock(),
            'knowledge_svc': MagicMock(),
        }

        with patch('plugins.debrief.hook.BaseWorld') as mock_bw, \
             patch('plugins.debrief.hook.DebriefGui'), \
             patch('plugins.debrief.hook.asyncio.create_task'):
            mock_bw.strip_yml.return_value = [{}]
            await hook.enable(services)
            mock_bw.apply_config.assert_called_once_with(
                'debrief', mock_bw.strip_yml.return_value[0])
