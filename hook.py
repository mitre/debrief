from app.utility.base_world import BaseWorld
from plugins.debrief.app.debrief_gui import DebriefGui

# NEW:
import aiohttp, asyncio, logging
from plugins.debrief.attack_mapper import load_attack18_map, CACHE_PATH

name = 'Debrief'
description = 'some good bones'
address = '/plugin/debrief/gui'
access = BaseWorld.Access.RED
log = logging.getLogger('debrief')


async def _init_attack18_cache():
    # Background init so UI isn't blocked
    async with aiohttp.ClientSession() as session:
        async def _get(url: str):
            async with session.get(url, timeout=30) as resp:
                return resp.status, await resp.text()
        try:
            _ = await load_attack18_map(_get)   # fetch + write cache
            log.info(f'ATT&CK v18 cache initialized at {CACHE_PATH}')
        except Exception as ex:
            log.warning(f'ATT&CK v18 cache not initialized: {ex}')

async def enable(services):
    BaseWorld.apply_config('debrief', BaseWorld.strip_yml('plugins/debrief/conf/default.yml')[0])
    app = services.get('app_svc').application
    debrief_gui = DebriefGui(services)
    
    #Static routes
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