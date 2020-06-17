import json
import logging
from aiohttp import web
from aiohttp_jinja2 import template

from app.service.auth_svc import for_all_public_methods, check_authorization
from app.utility.base_world import BaseWorld
from plugins.debrief.app.debrief_svc import DebriefService


@for_all_public_methods(check_authorization)
class DebriefGui(BaseWorld):

    def __init__(self, services):
        self.services = services
        self.debrief_svc = DebriefService(services)
        self.auth_svc = services.get('auth_svc')
        self.data_svc = services.get('data_svc')
        self.file_svc = services.get('file_svc')
        self.log = logging.getLogger('debrief_gui')

    async def _get_access(self, request):
        return dict(access=tuple(await self.auth_svc.get_permissions(request)))

    @template('debrief.html')
    async def splash(self, request):
        operations = [o.display for o in await self.data_svc.locate('operations', match=await self._get_access(request))]
        return dict(operations=operations)

    async def report(self, request):
        data = dict(await request.json())
        operations = [o.display for o in await self.data_svc.locate('operations', match=await self._get_access(request))
                      if str(o.id) in data.get('operations')]
        return web.json_response(dict(operations=operations))

    async def graph(self, request):
        try:
            graph = await self.debrief_svc.build_agent_d3()
            return web.json_response(graph)
        except Exception as e:
            self.log.error(repr(e), exc_info=True)
