from app.utility.base_world import BaseWorld
from plugins.debrief.app.debrief_gui import DebriefGui

name = 'Debrief'
description = 'some good bones'
address = '/plugin/debrief/gui'
access = BaseWorld.Access.RED


async def enable(services):
    app = services.get('app_svc').application
    debrief_gui = DebriefGui(services)
    app.router.add_static('/debrief', 'plugins/debrief/static/', append_version=True)
    app.router.add_route('GET', '/plugin/debrief/gui', debrief_gui.splash)
    app.router.add_route('POST', '/plugin/debrief/report', debrief_gui.report)
    app.router.add_route('*', '/plugin/debrief/graph', debrief_gui.graph)
    app.router.add_route('POST', '/plugin/debrief/pdf', debrief_gui.download_pdf)
    app.router.add_route('POST', '/plugin/debrief/json', debrief_gui.download_json)
