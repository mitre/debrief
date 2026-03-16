"""Shared fixtures for debrief plugin test suite."""
import pytest
import asyncio
import importlib
import json
import os
import sys

from base64 import b64encode
from datetime import datetime
from enum import Enum
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from plugins.debrief.attack_mapper import Attack18Map


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
LINK_DECIDE_TIME = '2021-01-01T08:00:00Z'
LINK_COLLECT_TIME = '2021-01-01T08:01:00Z'
LINK_FINISH_TIME = '2021-01-01T08:02:00Z'


class _OriginType(Enum):
    IMPORTED = 'IMPORTED'
    LEARNED = 'LEARNED'
    SEEDED = 'SEEDED'


def _encode(s):
    return b64encode(s.encode('utf-8')).decode()


def _make_ability(ability_id='ab-1', tactic='discovery', technique_id='T1082',
                  technique_name='System Information Discovery', name='Test ability',
                  cleanup=False):
    ab = SimpleNamespace(
        ability_id=ability_id,
        tactic=tactic,
        technique_id=technique_id,
        technique_name=technique_name,
        name=name,
    )
    return ab


def _make_link(paw='paw1', ability=None, status=0, cleanup=0, unique='link1',
               command=None, facts=None, created='2021-01-01 08:00:00', finish=LINK_FINISH_TIME,
               link_id=None):
    if ability is None:
        ability = _make_ability()
    if command is None:
        command = _encode('whoami')
    lnk = SimpleNamespace(
        paw=paw,
        ability=ability,
        status=status,
        cleanup=cleanup,
        unique=unique,
        command=command,
        facts=facts or [],
        created=created,
        finish=finish,
        id=link_id or unique,
    )
    lnk.decode_bytes = staticmethod(lambda c: c)
    return lnk


def _make_agent(paw='paw1', platform='windows', host='WORKSTATION', group='red',
                display_name='Agent1', unique='agent1', username='user1',
                privilege='User', exe_name='agent.exe',
                created=None, origin_link_id=None):
    if created is None:
        created = datetime(2021, 1, 1, 8, 0, 0)
    return SimpleNamespace(
        paw=paw,
        platform=platform,
        host=host,
        group=group,
        display_name=display_name,
        unique=unique,
        username=username,
        privilege=privilege,
        exe_name=exe_name,
        created=created,
        origin_link_id=origin_link_id,
    )


def _make_source(source_id='src-1', facts=None):
    return SimpleNamespace(id=source_id, facts=facts or [])


def _make_fact(trait='host.user.name', value='admin', score=1, unique='fact1',
               origin_type=None, source='src-1', links=None, collected_by=None,
               created=None):
    if origin_type is None:
        origin_type = _OriginType.LEARNED
    if created is None:
        created = datetime(2021, 1, 1, 8, 1, 0)
    return SimpleNamespace(
        trait=trait,
        value=value,
        score=score,
        unique=unique,
        origin_type=origin_type,
        source=source,
        links=links or [],
        collected_by=collected_by or [],
        created=created,
    )


def _make_planner(name='atomic'):
    return SimpleNamespace(name=name)


def _make_objective(name='default'):
    return SimpleNamespace(name=name)


def _make_operation(name='TestOp', agents=None, chain=None, source=None,
                    state='finished', finish='2021-01-01 09:00:00',
                    created='2021-01-01 08:00:00', op_id='op-1',
                    planner=None, objective=None, facts=None, relationships=None):
    if agents is None:
        agents = [_make_agent()]
    if chain is None:
        chain = [_make_link()]
    if source is None:
        source = _make_source()
    if planner is None:
        planner = _make_planner()
    if objective is None:
        objective = _make_objective()

    async def all_facts():
        return facts or []

    async def all_relationships():
        return relationships or []

    op = SimpleNamespace(
        id=op_id,
        name=name,
        agents=agents,
        chain=chain,
        source=source,
        state=state,
        finish=finish,
        created=created,
        planner=planner,
        objective=objective,
        display={'name': name, 'id': op_id},
        all_facts=all_facts,
        all_relationships=all_relationships,
    )
    return op


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def make_ability():
    return _make_ability


@pytest.fixture
def make_link():
    return _make_link


@pytest.fixture
def make_agent():
    return _make_agent


@pytest.fixture
def make_operation():
    return _make_operation


@pytest.fixture
def make_fact():
    return _make_fact


@pytest.fixture
def make_source():
    return _make_source


@pytest.fixture
def encode_command():
    return _encode


@pytest.fixture
def sample_agent():
    return _make_agent()


@pytest.fixture
def sample_agent_linux():
    return _make_agent(paw='paw2', platform='linux', host='SERVER', unique='agent2',
                       display_name='Agent2', username='linuser', exe_name='agent')


@pytest.fixture
def sample_ability():
    return _make_ability()


@pytest.fixture
def sample_link():
    return _make_link()


@pytest.fixture
def sample_operation():
    return _make_operation()


@pytest.fixture
def two_op_chain():
    """Two links in chain with different tactics/techniques."""
    ab1 = _make_ability(ability_id='ab-1', tactic='discovery', technique_id='T1082',
                        technique_name='System Information Discovery', name='Sys Info')
    ab2 = _make_ability(ability_id='ab-2', tactic='collection', technique_id='T1005',
                        technique_name='Data from Local System', name='Collect Data')
    link1 = _make_link(paw='paw1', ability=ab1, unique='lnk1', created='2021-01-01 08:00:00')
    link2 = _make_link(paw='paw1', ability=ab2, unique='lnk2', created='2021-01-01 08:01:00')
    return [link1, link2]


@pytest.fixture
def multi_op_operations(sample_agent, two_op_chain):
    op1 = _make_operation(name='Op1', op_id='op-1', agents=[sample_agent], chain=two_op_chain)
    op2 = _make_operation(name='Op2', op_id='op-2', agents=[sample_agent],
                          chain=[_make_link(paw='paw1', ability=_make_ability(
                              ability_id='ab-3', tactic='discovery', technique_id='T1082',
                              technique_name='System Information Discovery', name='Sys Info 2'),
                              unique='lnk3')])
    return [op1, op2]


@pytest.fixture
def mock_services():
    """Minimal mock services dict for DebriefService / DebriefGui."""
    data_svc = AsyncMock()
    data_svc.locate = AsyncMock(return_value=[])

    app_svc = AsyncMock()
    app_svc.find_op_with_link = AsyncMock(return_value=None)
    app_svc.application = MagicMock()
    app_svc.application.router = MagicMock()

    auth_svc = AsyncMock()
    auth_svc.get_permissions = AsyncMock(return_value=[])

    file_svc = AsyncMock()
    knowledge_svc = AsyncMock()

    return {
        'data_svc': data_svc,
        'app_svc': app_svc,
        'auth_svc': auth_svc,
        'file_svc': file_svc,
        'knowledge_svc': knowledge_svc,
    }


@pytest.fixture
def mock_attack18_map():
    """Return an Attack18Map with empty indexes for isolated unit testing."""
    return Attack18Map({
        'techniques_by_id': {},
        'strategies_by_tid': {},
        'analytics_by_tid': {},
    })


@pytest.fixture
def populated_attack18_map():
    """Return an Attack18Map with some sample data."""
    return Attack18Map({
        'techniques_by_id': {
            'T1082': {'technique_id': 'T1082', 'name': 'System Information Discovery'},
            'T1005': {'technique_id': 'T1005', 'name': 'Data from Local System'},
            'T1547.001': {'technique_id': 'T1547.001', 'name': 'Registry Run Keys'},
        },
        'strategies_by_tid': {
            'T1082': [{'id': 's1', 'name': 'Detect SysInfo', 'det_id': 'DET0001',
                        'external_references': []}],
            'T1547': [{'id': 's2', 'name': 'Detect Persistence', 'det_id': 'DET0002',
                        'external_references': []}],
        },
        'analytics_by_tid': {
            'T1082': [
                {'id': 'a1', 'an_id': 'AN0001', 'name': 'Analytic 0001',
                 'platform': 'windows', 'platforms': ['windows'],
                 'statement': 'Monitor sysinfo', 'tunables': [],
                 'dc_elements': [{'name': 'WinEventLog:Security', 'channel': '4688',
                                  'data_component': 'Process Creation'}],
                 'det_id': 'DET0001'},
            ],
        },
    })
