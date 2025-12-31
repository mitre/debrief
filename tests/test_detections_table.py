import pytest
import importlib

from base64 import b64encode
from datetime import datetime

from reportlab.platypus import Paragraph

from app.objects.c_ability import Ability
from app.objects.c_adversary import Adversary
from app.objects.c_agent import Agent
from app.objects.c_operation import Operation
from app.objects.secondclass.c_executor import Executor
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
    link_abil = Ability(ability_id='1083-1', tactic='discovery', technique_id='T1083',
                        technique_name='File and Directory Discovery',
                        name='T1083 Ability Windows', description='T1083 Ability Windows Desc',
                        executors=[link_exec])
    return op_link(ability=link_abil, paw=win_agent.paw, executor=link_exec,
                   command=encode_command(command), plaintext_command=encode_command(command), status=0, host=win_agent.host, pid=789,
                   decide=parse_datestring(LINK_DECIDE_TIME),
                   collect=parse_datestring(LINK_COLLECT_TIME),
                   finish=LINK_FINISH_TIME)


@pytest.fixture
def link_T1083_linux(op_link, linux_agent, encode_command, parse_datestring):
    command = 'ls'
    link_exec = Executor(name='sh', platform='linux', command=command)
    link_abil = Ability(ability_id='1083-2', tactic='discovery', technique_id='T1083',
                        technique_name='File and Directory Discovery',
                        name='T1083 Ability Linux', description='T1083 Ability Linux Desc',
                        executors=[link_exec])
    return op_link(ability=link_abil, paw=linux_agent.paw, executor=link_exec,
                   command=encode_command(command), plaintext_command=encode_command(command),
                   status=0, host=linux_agent.host, pid=789,
                   decide=parse_datestring(LINK_DECIDE_TIME),
                   collect=parse_datestring(LINK_COLLECT_TIME),
                   finish=LINK_FINISH_TIME)


@pytest.fixture
def link_T1547_001_windows(op_link, win_agent, encode_command, parse_datestring):
    command = 'reg'
    link_exec = Executor(name='psh', platform='windows', command=command)
    link_abil = Ability(ability_id='1547-001-1', tactic='persistence',
                        technique_id='T1547.001', name='T1547.001 Ability',
                        technique_name='Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder',
                        description='T1547.001 Ability Desc', executors=[link_exec])
    return op_link(ability=link_abil, paw=win_agent.paw, executor=link_exec,
                   command=encode_command(command), plaintext_command=encode_command(command),
                   status=0, host=win_agent.host, pid=789,
                   decide=parse_datestring(LINK_DECIDE_TIME),
                   collect=parse_datestring(LINK_COLLECT_TIME),
                   finish=LINK_FINISH_TIME)


@pytest.fixture
def link_T1560_001_windows(op_link, win_agent, encode_command, parse_datestring):
    command = 'zip'
    link_exec = Executor(name='psh', platform='windows', command=command)
    link_abil = Ability(ability_id='1560-001-1', tactic='collection', technique_id='T1560.001',
                        technique_name='Archive Collected Data: Archive via Utility',
                        name='T1560.001 Ability Windows', description='T1560.001 Ability Windows Desc',
                        executors=[link_exec])
    return op_link(ability=link_abil, paw=win_agent.paw, executor=link_exec,
                   command=encode_command(command), plaintext_command=encode_command(command),
                   status=0, host=win_agent.host, pid=789,
                   decide=parse_datestring(LINK_DECIDE_TIME),
                   collect=parse_datestring(LINK_COLLECT_TIME),
                   finish=LINK_FINISH_TIME)


@pytest.fixture
def link_T1560_001_linux(op_link, linux_agent, encode_command, parse_datestring):
    command = 'zip'
    link_exec = Executor(name='sh', platform='linux', command=command)
    link_abil = Ability(ability_id='1560-001-2', tactic='collection', technique_id='T1560.001',
                        technique_name='Archive Collected Data: Archive via Utility',
                        name='T1560.001 Ability Linux', description='T1560.001 Ability Linux Desc',
                        executors=[link_exec])
    return op_link(ability=link_abil, paw=linux_agent.paw, executor=link_exec,
                   command=encode_command(command), plaintext_command=encode_command(command),
                   status=0, host=linux_agent.host, pid=789,
                   decide=parse_datestring(LINK_DECIDE_TIME),
                   collect=parse_datestring(LINK_COLLECT_TIME),
                   finish=LINK_FINISH_TIME)


@pytest.fixture
def link_library(link_T1083_windows, link_T1083_linux, link_T1547_001_windows,
                 link_T1560_001_windows, link_T1560_001_linux):
    return {
        'win_T1083': link_T1083_windows,
        'lin_T1083': link_T1083_linux,
        'win_T1547.001': link_T1547_001_windows,
        'win_T1560.001': link_T1560_001_windows,
        'lin_T1560.001': link_T1560_001_linux,
    }


@pytest.fixture
def create_test_op(op_adversary):
    def _create_test_op(name, agents, links=[]):
        op = Operation(name=name, agents=agents, adversary=op_adversary)
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
    section = TTP_DET_MODULE.DebriefReportSection()
    section._ensure_styles()
    return section


def compare_paragraphs(a, b):
    return a.text == b.text and a.style == b.style


def compare_rows(a, b):
    if len(a) != len(b):
        return False
    for i, elem in enumerate(a):
        if type(elem) is not type(b[i]):
            return False
        elif type(elem) is Paragraph:
            if not compare_paragraphs(elem, b[i]):
                print(f'Unequal paragraphs: {str(elem)}, {str(b[i])}')
                return False
        else:
            if elem != b[i]:
                print(f'Unequal: {str(elem)}, {str(b[i])}')
                return False
    return True


class TestDetectionsTable:
    def test_report_section_fields(self, det_report_section):
        assert det_report_section.id == 'ttps-detections'
        assert det_report_section.display_name == 'Detection Strategies'
        assert det_report_section.description == 'Ordered steps (TTPs) from the operation with their associated ATT&CK v18 Detections.'
        assert type(det_report_section._a18) is Attack18Map

    def test_format_an_range(self, det_report_section):
        an_list1 = ['AN0002', 'AN0001', 'AN0003']
        an_list2 = ['AN0001']
        an_list3 = ['AN1204', 'AN1202', 'AN1205']
        assert det_report_section._format_an_range(an_list1) == 'Analytic ( AN0001 to AN0003 )'
        assert det_report_section._format_an_range(an_list2) == 'Analytic ( AN0001 to AN0001 )'
        assert det_report_section._format_an_range(an_list3) == 'Analytic ( AN1202 to AN1205 )'

    def test_get_op_platforms_and_tids(self, det_report_section, paw_to_platform, create_test_op,
                                       win_agent, linux_agent, link_library):
        # One agent, one platform
        single_agent_links = [
            link_library.get('win_T1083'),
            link_library.get('win_T1083'),
            link_library.get('win_T1547.001'),
            link_library.get('win_T1560.001'),
        ]
        single_agent_op = create_test_op('single agent op', [win_agent], single_agent_links)
        tid_to_platforms, tids = det_report_section._get_op_platforms_and_tids(single_agent_op, paw_to_platform)
        assert tid_to_platforms == {
            'T1083': {'windows'},
            'T1547.001': {'windows'},
            'T1560.001': {'windows'},
        }
        assert tids == {'T1083', 'T1547.001', 'T1560.001'}

        # Two agents, two platforms
        two_agent_links = [
            link_library.get('win_T1083'),
            link_library.get('win_T1083'),
            link_library.get('win_T1547.001'),
            link_library.get('win_T1560.001'),
            link_library.get('lin_T1083'),
            link_library.get('lin_T1083'),
            link_library.get('lin_T1560.001'),
        ]
        two_agent_op = create_test_op('two agent op', [win_agent, linux_agent], two_agent_links)
        tid_to_platforms2, tids2 = det_report_section._get_op_platforms_and_tids(two_agent_op, paw_to_platform)
        assert tid_to_platforms2 == {
            'T1083': {'windows', 'linux'},
            'T1547.001': {'windows'},
            'T1560.001': {'windows', 'linux'},
        }
        assert tids2 == {'T1083', 'T1547.001', 'T1560.001'}

    def test_get_technique_detection_refs(self, det_report_section):
        # Non-subtechnique
        main_tid_ret = det_report_section._get_technique_detection_refs('T1083')
        assert len(main_tid_ret) == 1
        main_tid_det = main_tid_ret[0]
        assert main_tid_det['strategy']['name'] == 'Recursive Enumeration of Files and Directories Across Privilege Contexts'
        assert main_tid_det['strategy']['det_id'] == 'DET0370'
        assert main_tid_det['det_id'] == 'DET0370'
        assert main_tid_det['strategy']['name'] == main_tid_det['det_name']
        assert main_tid_det['tid'] == 'T1083'

        # Subtechnique
        sub_tid_ret = det_report_section._get_technique_detection_refs('T1548.001')
        assert len(sub_tid_ret) == 1
        sub_tid_det = sub_tid_ret[0]
        assert sub_tid_det['strategy']['name'] == 'Setuid/Setgid Privilege Abuse Detection (Linux/macOS)'
        assert sub_tid_det['strategy']['det_id'] == 'DET0110'
        assert sub_tid_det['det_id'] == 'DET0110'
        assert sub_tid_det['strategy']['name'] == sub_tid_det['det_name']
        assert sub_tid_det['tid'] == 'T1548.001'

        # Force fallback with non-existent subtechnique
        fallback_ret = det_report_section._get_technique_detection_refs('T1083.DNE')
        assert fallback_ret == main_tid_ret

    def test_det_rows_single_platform(self, det_report_section):
        refs = det_report_section._get_technique_detection_refs('T1083')
        assert len(refs) == 1
        rows, an_ids = det_report_section._build_det_appendix_rows(refs[0], ['windows'])
        want_rows = [
            [
                'AN', 'Platform', 'Detection Statement',
                'Data Component Elements (DC)', '', '',
                'Mutable Elements', ''
            ],
            ['', '', '', 'Name', 'Channel', 'Data Component', 'Field', 'Description'],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Security', det_report_section.cell_style),
                Paragraph('EventCode=4688', det_report_section.cell_style),
                Paragraph('Process Creation', det_report_section.cell_style),
                Paragraph('CommandLineRegex', det_report_section.cell_style),
                Paragraph('Allows tuning based on tools/scripts used for enumeration (e.g., tree, dir /s /b)', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Security', det_report_section.cell_style),
                Paragraph('EventCode=4688', det_report_section.cell_style),
                Paragraph('Process Creation', det_report_section.cell_style),
                Paragraph('UserContext', det_report_section.cell_style),
                Paragraph('Scoping for standard vs elevated or service accounts', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Security', det_report_section.cell_style),
                Paragraph('EventCode=4688', det_report_section.cell_style),
                Paragraph('Process Creation', det_report_section.cell_style),
                Paragraph('TimeWindow', det_report_section.cell_style),
                Paragraph('Defines burst activity over short periods (e.g., &gt;50 directory queries in 30s)', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Sysmon', det_report_section.cell_style),
                Paragraph('EventCode=11', det_report_section.cell_style),
                Paragraph('File Creation', det_report_section.cell_style),
                Paragraph('CommandLineRegex', det_report_section.cell_style),
                Paragraph('Allows tuning based on tools/scripts used for enumeration (e.g., tree, dir /s /b)', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Sysmon', det_report_section.cell_style),
                Paragraph('EventCode=11', det_report_section.cell_style),
                Paragraph('File Creation', det_report_section.cell_style),
                Paragraph('UserContext', det_report_section.cell_style),
                Paragraph('Scoping for standard vs elevated or service accounts', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Sysmon', det_report_section.cell_style),
                Paragraph('EventCode=11', det_report_section.cell_style),
                Paragraph('File Creation', det_report_section.cell_style),
                Paragraph('TimeWindow', det_report_section.cell_style),
                Paragraph('Defines burst activity over short periods (e.g., &gt;50 directory queries in 30s)', det_report_section.cell_style),
            ]
        ]
        assert len(rows) == len(want_rows)
        for i, want_row in enumerate(want_rows):
            assert compare_rows(want_row, rows[i])
        assert an_ids == {'AN1040'}

    def test_det_rows_multi_platform(self, det_report_section):
        refs = det_report_section._get_technique_detection_refs('T1083')
        assert len(refs) == 1
        rows, an_ids = det_report_section._build_det_appendix_rows(refs[0], ['linux', 'windows'])
        want_rows = [
            [
                'AN', 'Platform', 'Detection Statement',
                'Data Component Elements (DC)', '', '',
                'Mutable Elements', ''
            ],
            ['', '', '', 'Name', 'Channel', 'Data Component', 'Field', 'Description'],
            [
                Paragraph('AN1041', det_report_section.sty_cell_center),
                Paragraph('Linux', det_report_section.sty_cell_center),
                Paragraph("Use of file enumeration commands (e.g., 'ls', 'find', 'locate') executed by suspicious users or scripts accessing broad file hierarchies or restricted directories.", det_report_section.sty_cell_center),
                Paragraph('auditd:SYSCALL', det_report_section.cell_style),
                Paragraph('execve', det_report_section.cell_style),
                Paragraph('Process Creation', det_report_section.cell_style),
                Paragraph('FilePathDepth', det_report_section.cell_style),
                Paragraph('Max depth of recursive access to tune noise vs anomaly', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1041', det_report_section.sty_cell_center),
                Paragraph('Linux', det_report_section.sty_cell_center),
                Paragraph("Use of file enumeration commands (e.g., 'ls', 'find', 'locate') executed by suspicious users or scripts accessing broad file hierarchies or restricted directories.", det_report_section.sty_cell_center),
                Paragraph('auditd:SYSCALL', det_report_section.cell_style),
                Paragraph('execve', det_report_section.cell_style),
                Paragraph('Process Creation', det_report_section.cell_style),
                Paragraph('UserContext', det_report_section.cell_style),
                Paragraph('Helpful to exclude known scripts or automation accounts', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1041', det_report_section.sty_cell_center),
                Paragraph('Linux', det_report_section.sty_cell_center),
                Paragraph("Use of file enumeration commands (e.g., 'ls', 'find', 'locate') executed by suspicious users or scripts accessing broad file hierarchies or restricted directories.", det_report_section.sty_cell_center),
                Paragraph('auditd:PATH', det_report_section.cell_style),
                Paragraph('PATH', det_report_section.cell_style),
                Paragraph('File Access', det_report_section.cell_style),
                Paragraph('FilePathDepth', det_report_section.cell_style),
                Paragraph('Max depth of recursive access to tune noise vs anomaly', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1041', det_report_section.sty_cell_center),
                Paragraph('Linux', det_report_section.sty_cell_center),
                Paragraph("Use of file enumeration commands (e.g., 'ls', 'find', 'locate') executed by suspicious users or scripts accessing broad file hierarchies or restricted directories.", det_report_section.sty_cell_center),
                Paragraph('auditd:PATH', det_report_section.cell_style),
                Paragraph('PATH', det_report_section.cell_style),
                Paragraph('File Access', det_report_section.cell_style),
                Paragraph('UserContext', det_report_section.cell_style),
                Paragraph('Helpful to exclude known scripts or automation accounts', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Security', det_report_section.cell_style),
                Paragraph('EventCode=4688', det_report_section.cell_style),
                Paragraph('Process Creation', det_report_section.cell_style),
                Paragraph('CommandLineRegex', det_report_section.cell_style),
                Paragraph('Allows tuning based on tools/scripts used for enumeration (e.g., tree, dir /s /b)', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Security', det_report_section.cell_style),
                Paragraph('EventCode=4688', det_report_section.cell_style),
                Paragraph('Process Creation', det_report_section.cell_style),
                Paragraph('UserContext', det_report_section.cell_style),
                Paragraph('Scoping for standard vs elevated or service accounts', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Security', det_report_section.cell_style),
                Paragraph('EventCode=4688', det_report_section.cell_style),
                Paragraph('Process Creation', det_report_section.cell_style),
                Paragraph('TimeWindow', det_report_section.cell_style),
                Paragraph('Defines burst activity over short periods (e.g., &gt;50 directory queries in 30s)', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Sysmon', det_report_section.cell_style),
                Paragraph('EventCode=11', det_report_section.cell_style),
                Paragraph('File Creation', det_report_section.cell_style),
                Paragraph('CommandLineRegex', det_report_section.cell_style),
                Paragraph('Allows tuning based on tools/scripts used for enumeration (e.g., tree, dir /s /b)', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Sysmon', det_report_section.cell_style),
                Paragraph('EventCode=11', det_report_section.cell_style),
                Paragraph('File Creation', det_report_section.cell_style),
                Paragraph('UserContext', det_report_section.cell_style),
                Paragraph('Scoping for standard vs elevated or service accounts', det_report_section.cell_style),
            ],
            [
                Paragraph('AN1040', det_report_section.sty_cell_center),
                Paragraph('Windows', det_report_section.sty_cell_center),
                Paragraph("Execution of file enumeration commands (e.g., 'dir', 'tree') from non-standard processes or unusual user contexts, followed by recursive directory traversal or access to sensitive locations.", det_report_section.sty_cell_center),
                Paragraph('WinEventLog:Sysmon', det_report_section.cell_style),
                Paragraph('EventCode=11', det_report_section.cell_style),
                Paragraph('File Creation', det_report_section.cell_style),
                Paragraph('TimeWindow', det_report_section.cell_style),
                Paragraph('Defines burst activity over short periods (e.g., &gt;50 directory queries in 30s)', det_report_section.cell_style),
            ]
        ]
        assert len(rows) == len(want_rows)
        for i, want_row in enumerate(want_rows):
            assert compare_rows(want_row, rows[i])
        assert an_ids == {'AN1040', 'AN1041'}
