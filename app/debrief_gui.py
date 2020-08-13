import base64
import json
import logging
from io import BytesIO

from aiohttp import web
from aiohttp_jinja2 import template
from reportlab.graphics import renderPM
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Flowable
from svglib.svglib import svg2rlg

from app.service.auth_svc import for_all_public_methods, check_authorization
from app.utility.base_world import BaseWorld
from plugins.debrief.app.debrief_svc import DebriefService
from plugins.debrief.app.crop import Crop


class DrawLine(Flowable):
    def __init__(self):
        Flowable.__init__(self)

    def draw(self):
        maroon = colors.maroon
        self.canv.setStrokeColor(maroon)
        self.canv.setLineWidth(4)
        self.canv.line(110, 30, 450, 30)


def _status_name(status):
    if status == 0:
        return 'success'
    elif status == -2:
        return 'discarded'
    elif status == 1:
        return 'failure'
    elif status == 124:
        return 'timeout'
    elif status == -3:
        return 'collected'
    elif status == -4:
        return 'untrusted'
    elif status == -5:
        return 'visibility'
    else:
        return 'queued'


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
        operations = [o.display for o in
                      await self.data_svc.locate('operations', match=await self._get_access(request))]
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
        svg_bytes = data['graph']
        with open('./graph.svg', "wb") as fh:
            fh.write(base64.b64decode(svg_bytes))
        png_convert = svg2rlg("./graph.svg")
        renderPM.drawToFile(png_convert, "./graph.png", fmt="PNG")
        if data['operation_id'] and len(data['operation_id']) == 1:
            op_id = data['operation_id'].pop()
            operation = (await self.data_svc.locate('operations', match=dict(id=int(op_id))))[0]
            filename = operation.name + '_' + operation.start.strftime('%Y-%m-%d_%H-%M-%S')
            pdf_bytes = self._build_pdf(operation)
            return web.json_response(dict(filename=filename, pdf_bytes=pdf_bytes))
        return web.json_response('None or multiple operations selected')

    async def fact_graph(self, request):
        try:
            operations = request.rel_url.query['operations'].split(',')
            graph = await self.debrief_svc.build_fact_d3(operations)
            return web.json_response(graph)
        except Exception as e:
            self.log.error(repr(e), exc_info=True)

    @staticmethod
    def _build_pdf(operation):
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=18, bottomMargin=18)
        Story = []
        styles = getSampleStyleSheet()
        title = styles['Heading1']
        normal = styles['Normal']
        title.alignment = 1
        logo = "./static/img/back-red.png"
        im = Image(logo, 1.5 * inch, 1 * inch)
        im.hAlign = 'LEFT'
        Story.append(im)
        line = DrawLine()
        Story.append(line)
        Story.append(Spacer(1, 12))
        op_name = operation.name
        pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
        text = "<font name =VeraBd size=16 color=maroon>OPERATION DEBRIEF</font>"
        Story.append(Paragraph(text, title))
        Story.append(Spacer(1, 12))
        text = "<u><font name =Helvetica-Bold size=12>OPERATION</font></u><font size=12> = %s</font>" % op_name
        Story.append(Paragraph(text, normal))
        Story.append(Spacer(1, 12))
        Story.append(Spacer(1, 12))
        Story.append(Spacer(1, 12))
        ptext = '<font size="12">GRAPH</font>'
        Story.append(Paragraph(ptext, title))
        Crop.crop_image('./graph.png', (450, 110, 800, 300), './graph_cropped.png')
        graph = "./graph_cropped.png"
        gr = Image(graph, 5 * inch, 2.5 * inch)
        Story.append(gr)
        Story.append(Spacer(1, 12))
        Story.append(Spacer(1, 12))
        ptext = '<font size="12">OPERATION STATS</font>'
        Story.append(Paragraph(ptext, title))
        time = operation.start.strftime('%Y-%m-%d %H:%M:%S')
        data = [['State', 'Planner', 'Objective', 'Time'],
                [operation.state, operation.planner.name, operation.objective.name, time]]
        t = Table(data)
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.maroon),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                               ('FONTNAME', (0, 0), (-1, 0), 'Courier-Bold'),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                               ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
                               ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                               ]))
        Story.append(t)
        Story.append(PageBreak())
        Story.append(im)
        line = DrawLine()
        Story.append(line)
        Story.append(Spacer(1, 12))
        Story.append(Spacer(1, 12))
        ptext = '<font size="12">OPERATION STEPS</font>'
        Story.append(Paragraph(ptext, title))
        count = 1
        step_num = 1
        for link in operation.chain:
            if count == 6:
                Story.append(PageBreak())
                Story.append(im)
                line = DrawLine()
                Story.append(line)
                Story.append(Spacer(1, 12))
                Story.append(Spacer(1, 12))
                count = 1
            ptext = '<font size="12" name = Courier-Bold>%s.</font>' % step_num
            Story.append(Paragraph(ptext, normal))
            link_time = link.collect.strftime('%Y-%m-%d %H:%M:%S')
            steps = [['Status', 'Time', 'Name', 'Agent'],
                     [_status_name(link.status), link_time, link.ability.name, link.paw]]
            s = Table(steps)
            s.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.maroon),
                                   ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                   ('FONTNAME', (0, 0), (-1, 0), 'Courier-Bold'),
                                   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                   ('FONTSIZE', (0, 0), (-1, -1), 10),
                                   ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
                                   ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                   ]))
            s.hAlign = 'CENTER'
            Story.append(s)

            # Create list of gathered facts, needs to be properly formatted in table
            '''
            facts_gathered = []
            for f in link.facts:
                if f.score > 0:
                    facts_gathered.append(f.value)
            '''
            steps_2 = [['Command', 'Facts'],
                       [base64.b64decode(link.command), '2 + 2 = 4']]
            s2 = Table(steps_2)
            s2.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.maroon),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Courier-Bold'),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
                                    ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                    ]))
            s2.hAlign = 'CENTER'
            Story.append(s2)
            Story.append(Spacer(1, 12))
            step_num += 1
            count += 1
        doc.build(Story)
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value.decode('utf-8', errors='ignore')


