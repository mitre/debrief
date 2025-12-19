import aiohttp
import asyncio
import logging

from app.utility.base_world import BaseWorld
from plugins.debrief.app.debrief_gui import DebriefGui
from plugins.debrief.attack_mapper import fetch_and_cache, CACHE_PATH

name = 'Debrief'
description = 'Operation debrief functionality'
address = '/plugin/debrief/gui'
access = BaseWorld.Access.RED
log = logging.getLogger('debrief_hook')


async def _init_attack18_cache():
    # Background init so UI isn't blocked
    async with aiohttp.ClientSession() as session:
        try:
            await fetch_and_cache(session.get, path=CACHE_PATH)   # fetch + write cache
            log.info(f'ATT&CK v18 cache initialized at {CACHE_PATH}')
        except Exception as ex:
            log.warning(f'ATT&CK v18 cache not initialized: {ex}')


async def enable(services):
    BaseWorld.apply_config('debrief', BaseWorld.strip_yml('plugins/debrief/conf/default.yml')[0])
    app = services.get('app_svc').application
    debrief_gui = DebriefGui(services)

    # Static routes
    app.router.add_static('/debrief', 'plugins/debrief/static/', append_version=True)
    app.router.add_static('/logodebrief', 'plugins/debrief/uploads/', append_version=True)
    app.router.add_route('GET', '/plugin/debrief/gui', debrief_gui.splash)
    app.router.add_route('POST', '/plugin/debrief/report', debrief_gui.report)
    app.router.add_route('*', '/plugin/debrief/graph', debrief_gui.graph)
    app.router.add_route('POST', '/plugin/debrief/pdf', debrief_gui.download_pdf)
    app.router.add_route('POST', '/plugin/debrief/json', debrief_gui.download_json)
    app.router.add_route('GET', '/plugin/debrief/logos', debrief_gui.all_logos)
    app.router.add_route('GET', '/plugin/debrief/sections', debrief_gui.report_sections)
    app.router.add_route('POST', '/plugin/debrief/logo', debrief_gui.upload_logo)

    # Kick off the ATT&CK v18 cache warmup
    asyncio.create_task(_init_attack18_cache())
