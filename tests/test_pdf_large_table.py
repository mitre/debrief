"""Test that detection tables with many rows do not cause LayoutError.

The bug: KeepTogether forced header+table onto a single page. When the table
exceeded the landscape frame height (~576pts), ReportLab raised LayoutError.
The fix uses KeepTogetherSplitAtTop which allows the table to split across
pages while keeping the header attached to the top of the first fragment.
"""
import io
import importlib
import pytest

from base64 import b64encode
from datetime import datetime

from reportlab.lib.pagesizes import letter, landscape as to_landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate

from app.objects.c_ability import Ability
from app.objects.c_adversary import Adversary
from app.objects.c_agent import Agent
from app.objects.c_operation import Operation
from app.objects.secondclass.c_executor import Executor
from app.objects.secondclass.c_link import Link
from app.utility.base_object import BaseObject

TTP_DET_MODULE = importlib.import_module('plugins.debrief.app.debrief-sections.ttps_detections')


def _make_link(tid, technique_name, paw, platform):
    """Create a minimal Link with the given technique ID."""
    command = 'whoami'
    executor = Executor(name='psh' if platform == 'windows' else 'sh',
                        platform=platform, command=command)
    ability = Ability(
        ability_id=f'test-{tid}',
        tactic='lateral-movement',
        technique_id=tid,
        technique_name=technique_name,
        name=f'{tid} ability',
        description=f'{tid} test ability',
        executors=[executor],
    )
    encoded = b64encode(command.encode()).decode()
    link = Link(command=encoded, plaintext_command=encoded, paw=paw,
                ability=ability, executor=executor)
    link.pid = 999
    link.decide = datetime.strptime('2021-01-01T08:00:00Z', BaseObject.TIME_FORMAT)
    link.collect = datetime.strptime('2021-01-01T08:01:00Z', BaseObject.TIME_FORMAT)
    link.finish = '2021-01-01T08:02:00Z'
    return link


@pytest.fixture
def large_operation():
    """Create an operation with many distinct technique IDs to produce a large table."""
    agent = Agent(
        sleep_min=30, sleep_max=60, watchdog=0, platform='windows',
        host='WORKSTATION', username='user', architecture='amd64', group='red',
        location=r'C:\test.exe', pid=100, ppid=1, executors=['psh'],
        privilege='User', exe_name='test.exe', contact='unknown', paw='largepaw',
    )
    adversary = Adversary(adversary_id='large-test', name='Large Test Adversary',
                          description='test', atomic_ordering=dict())
    op = Operation(name='Large Test Op', agents=[agent], adversary=adversary)
    op.set_start_details()

    # Use technique IDs that exist in the ATT&CK v18 mapping so detection rows are generated.
    # Even if some TIDs have no detections, the ones that do will produce many rows.
    technique_ids = [
        'T1083', 'T1547.001', 'T1560.001', 'T1548.001',
        'T1059.001', 'T1053.005', 'T1021.002', 'T1021.001',
        'T1055.001', 'T1003.001', 'T1070.004', 'T1071.001',
        'T1036.005', 'T1105',
    ]
    links = []
    for tid in technique_ids:
        links.append(_make_link(tid, f'Technique {tid}', agent.paw, agent.platform))
    op.chain = links
    return op, agent


class TestLargeTablePdfGeneration:
    """Verify that a detection table with many rows builds a PDF without LayoutError."""

    @pytest.mark.asyncio
    async def test_large_operation_does_not_crash(self, large_operation):
        """Build a landscape PDF with a large detection table and verify no exception."""
        op, agent = large_operation
        section = TTP_DET_MODULE.DebriefReportSection()
        styles = getSampleStyleSheet()

        flowables = await section.generate_section_elements(
            styles,
            operations=[op],
            agents=[agent],
        )

        # There should be flowables generated
        assert len(flowables) > 0

        # Verify detection data tables exist (not just the section-band header).
        # Detection tables have 8 columns (AN, Platform, Statement, Name,
        # Channel, Data Component, Field, Description).
        from reportlab.platypus import Table
        det_tables = [f for f in flowables
                      if isinstance(f, Table) and len(f._argW) == 8]
        assert len(det_tables) > 0, "Expected at least one 8-column detection Table"

        # Build an actual PDF in a landscape frame matching debrief_gui.py
        buf = io.BytesIO()
        lw, lh = to_landscape(letter)
        margin = 18
        avail_width = lw - 2 * margin
        avail_height = lh - 2 * margin

        # Precondition: at least one detection table must exceed the available
        # frame height so that we actually exercise the page-split code path.
        max_table_h = max(
            t.wrap(avail_width, avail_height)[1] for t in det_tables
        )
        assert max_table_h > avail_height, (
            f"Test precondition failed: tallest detection table ({max_table_h:.0f}pt) "
            f"does not exceed frame height ({avail_height:.0f}pt), so the "
            f"LayoutError regression would not be exercised"
        )

        doc = SimpleDocTemplate(buf, pagesize=(lw, lh),
                                leftMargin=margin, rightMargin=margin,
                                topMargin=margin, bottomMargin=margin)

        # This is the line that used to raise LayoutError with KeepTogether
        doc.build(flowables)

        pdf_bytes = buf.getvalue()
        assert len(pdf_bytes) > 0
        # Verify it's a valid PDF
        assert pdf_bytes[:5] == b'%PDF-'

    @pytest.mark.asyncio
    async def test_section_uses_keep_together_split_at_top(self, large_operation):
        """Confirm the import was changed from KeepTogether to KeepTogetherSplitAtTop."""
        from reportlab.platypus.flowables import KeepTogetherSplitAtTop
        op, agent = large_operation
        section = TTP_DET_MODULE.DebriefReportSection()
        styles = getSampleStyleSheet()

        flowables = await section.generate_section_elements(
            styles,
            operations=[op],
            agents=[agent],
        )

        # At least one flowable should be a KeepTogetherSplitAtTop instance
        ktat_found = any(isinstance(f, KeepTogetherSplitAtTop) for f in flowables)
        assert ktat_found, (
            "Expected at least one KeepTogetherSplitAtTop flowable in the output; "
            "found types: " + str(set(type(f).__name__ for f in flowables))
        )
