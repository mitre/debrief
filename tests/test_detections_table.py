import pytest
import importlib

from base64 import b64encode
from datetime import datetime

from app.objects.c_ability import Ability
from app.objects.c_adversary import Adversary
from app.objects.c_agent import Agent
from app.objects.c_operation import Operation
from app.objects.secondclass.c_executor import Executor
from app.objects.secondclass.c_fact import Fact
from app.objects.secondclass.c_link import Link
from app.utility.base_object import BaseObject

from plugins.debrief.attack_mapper import Attack18Map

LINK_DECIDE_TIME = '2021-01-01T08:00:00Z'
LINK_COLLECT_TIME = '2021-01-01T08:01:00Z'
LINK_FINISH_TIME = '2021-01-01T08:02:00Z'

TTP_DET_MODULE = importlib.import_module('plugins.debrief.app.debrief-sections.ttps_detections')


@pytest.fixture
def win_agent():
    return Agent(sleep_min=30, sleep_max=60, watchdog=0, platform='windows', host='WORKSTATION',
                 username='windowsgent', architecture='amd64', group='red', location=r'C:\Users\Public\test.exe',
                 pid=1234, ppid=123, executors=['psh'], privilege='User', exe_name='test.exe', contact='unknown',
                 paw='testpawwin')


@pytest.fixture
def linux_agent():
    return Agent(sleep_min=30, sleep_max=60, watchdog=0, platform='linux', host='SERVER',
                 username='linuxagent', architecture='amd64', group='red', location=r'/home/linuxagent/test',
                 pid=1234, ppid=123, executors=['sh'], privilege='User', exe_name='test', contact='unknown',
                 paw='testpawlin')


@pytest.fixture
def op_adversary():
    return Adversary(adversary_id='123', name='test adversary', description='test adversary desc', atomic_ordering=dict())


@pytest.fixture
def op_link():
    def _generate_link(command, plaintext_command, paw, ability, executor, pid=0, decide=None, collect=None, finish=None, **kwargs):
        generated_link = Link(command, plaintext_command, paw, ability, executor, **kwargs)
        generated_link.pid = pid
        if decide:
            generated_link.decide = decide
        if collect:
            generated_link.collect = collect
        if finish:
            generated_link.finish = finish
        return generated_link
    return _generate_link


@pytest.fixture
def encode_command():
    def _encode_command(command_str):
        return b64encode(command_str.encode('utf-8')).decode()
    return _encode_command


@pytest.fixture
def parse_datestring():
    def _parse_datestring(datestring):
        return datetime.strptime(datestring, BaseObject.TIME_FORMAT)
    return _parse_datestring


@pytest.fixture
def link_T1083_windows(op_link, win_agent, encode_command, parse_datestring):
    command = 'ls'
    link_exec = Executor(name='psh', platform='windows', command=command)
    link_abil = Ability(ability_id='123', tactic='discovery', technique_id='T1083', technique_name='File and Directory Discovery',
                        name='T1083 Ability', description='T1083 Ability Desc', executors=[link_exec])
    return op_link(ability=link_abil, paw=win_agent.paw, executor=link_exec,
                   command=encode_command(command), plaintext_command=encode_command(command), status=0, host=win_agent.host, pid=789,
                   decide=parse_datestring(LINK_DECIDE_TIME),
                   collect=parse_datestring(LINK_COLLECT_TIME),
                   finish=LINK_FINISH_TIME)


@pytest.fixture
def link_T1083_linux(op_link, linux_agent, encode_command, parse_datestring):
    command = 'ls'
    link_exec = Executor(name='sh', platform='linux', command=command)
    link_abil = Ability(ability_id='123', tactic='discovery', technique_id='T1083', technique_name='File and Directory Discovery',
                        name='T1083 Ability', description='T1083 Ability Desc', executors=[link_exec])
    return op_link(ability=link_abil, paw=linux_agent.paw, executor=link_exec,
                   command=encode_command(command), plaintext_command=encode_command(command), status=0, host=linux_agent.host, pid=789,
                   decide=parse_datestring(LINK_DECIDE_TIME),
                   collect=parse_datestring(LINK_COLLECT_TIME),
                   finish=LINK_FINISH_TIME)


@pytest.fixture
def create_test_op():
    def _create_test_op(name, agents, adversary, links=[]):
        op = Operation(name=name, agents=agents, adversary=adversary)
        op.set_start_details()
        op.chain = links
        return op
    return _create_test_op


@pytest.fixture
def paw_to_platform(win_agent, linux_agent):
    return {
        win_agent.paw: win_agent.platform,
        linux_agent.paw: linux_agent.platform
    }


@pytest.fixture
def det_report_section():
    return TTP_DET_MODULE.DebriefReportSection()


class TestDetectionsTable:
    def test_report_section_fields(self, det_report_section):
        assert det_report_section.id == 'ttps-detections'
        assert det_report_section.display_name == 'TTPs & V18 Detections'
        assert det_report_section.description == 'Ordered steps (TTPs) from the operation with their associated ATT&CK v18 Detections.'
        assert type(det_report_section._a18) is Attack18Map

    def test_format_an_range(self, det_report_section):
        an_list1 = ['AN0002', 'AN0001', 'AN0003']
        an_list2 = ['AN0001']
        an_list3 = ['AN1204', 'AN1202', 'AN1205']
        assert det_report_section._format_an_range(an_list1) == 'Analytic ( AN0001 to AN0003 )'
        assert det_report_section._format_an_range(an_list2) == 'Analytic ( AN0001 to AN0001 )'
        assert det_report_section._format_an_range(an_list3) == 'Analytic ( AN1202 to AN1205 )'

    def test_single_link(self, create_test_op):
        pass

    def test_single_tid_multi_platform(self, create_test_op):
        pass

    def test_single_tid_repeated_platform(self, create_test_op):
        pass

    def test_multi_tid(self, create_test_op):
        pass
