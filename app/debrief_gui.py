import json
import logging

from aiohttp import web
from aiohttp_jinja2 import template
from reportlab.pdfgen import canvas

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

        # suppress Python Image Library debug logs
        pil = logging.getLogger('PIL')
        pil.setLevel(logging.INFO)

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
            operations = request.rel_url.query['operations'].split(',')
            graph = await self.debrief_svc.build_operation_d3(operations)
            return web.json_response(graph)
        except Exception as e:
            self.log.error(repr(e), exc_info=True)

    async def download_pdf(self, request):
        data = dict(await request.json())
        op_id = data['operation_id'].pop()
        operation = (await self.data_svc.locate('operations', match=dict(id=int(op_id))))[0]
        filename = operation.name + '_' + operation.start.strftime('%Y-%m-%d_%H-%M-%S')
        pdf_bytes = self._build_pdf(filename, operation)
        return web.json_response(dict(filename=filename, pdf_bytes=pdf_bytes))

    def _build_pdf(self, filename, operation):
        c = canvas.Canvas(filename + '.pdf', bottomup=0)
        c.setTitle(filename)
        self._draw_logo(c)
        c.setFont('Helvetica-Bold', 20)
        c.drawString(100, 100, operation.name)
        c.setFont('Helvetica', 15)
        c.drawString(100, 140, 'Steps')
        self._draw_steps(c, operation.chain)
        c.showPage()
        return c.getpdfdata().decode('utf-8', errors='ignore')

    @staticmethod
    def _draw_logo(self, cnvs):
        cnvs.saveState()
        cnvs.translate(15, 15)
        cnvs.scale(1, -1)
        cnvs.drawImage('./static/img/back-red.png', 80, 0, -80, -60)
        cnvs.restoreState()

    @staticmethod
    def _draw_steps(self, cnvs, chain):
        cnvs.setFont('Helvetica', 12)
        y = 140
        for link in chain:
            y += 20
            cnvs.drawString(100, y, link.collect.strftime('%Y-%m-%d %H:%M:%S') + ' ' + link.ability.name)
