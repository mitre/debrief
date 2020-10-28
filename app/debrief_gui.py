import base64
import glob
import logging
import os

from aiohttp import web
from aiohttp_jinja2 import template
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Spacer

from app.service.auth_svc import for_all_public_methods, check_authorization
from app.utility.base_world import BaseWorld
from plugins.debrief.app.debrief_svc import DebriefService
from plugins.debrief.app.objects.c_story import Story


@for_all_public_methods(check_authorization)
class DebriefGui(BaseWorld):

    def __init__(self, services):
        self.services = services
        self.debrief_svc = DebriefService(services)
        self.auth_svc = services.get('auth_svc')
        self.data_svc = services.get('data_svc')
        self.file_svc = services.get('file_svc')
        self.log = logging.getLogger('debrief_gui')

        self._suppress_logs('PIL')
        self._suppress_logs('svglib')

    async def _get_access(self, request):
        return dict(access=tuple(await self.auth_svc.get_permissions(request)))

    @template('debrief.html')
    async def splash(self, request):
        operations = [o.display for o in
                      await self.data_svc.locate('operations', match=await self._get_access(request))]
        return dict(operations=operations)

    async def report(self, request):
        data = dict(await request.json())
        operations = [o for o in await self.data_svc.locate('operations', match=await self._get_access(request))
                      if str(o.id) in data.get('operations')]
        op_displays = [o.display for o in operations]
        agents = [a.display for a in await self.data_svc.locate('agents', match=await self._get_access(request))]
        ttps = self._generate_ttps(operations)
        return web.json_response(dict(operations=op_displays, agents=agents, ttps=ttps))

    async def graph(self, request):
        graphs = {
            'graph': self.debrief_svc.build_operation_d3,
            'attackpath': self.debrief_svc.build_attackpath_d3,
            'fact': self.debrief_svc.build_fact_d3,
            'tactic': self.debrief_svc.build_tactic_d3,
            'technique': self.debrief_svc.build_technique_d3
        }
        try:
            graph_type = request.rel_url.query['type']
            operations = request.rel_url.query['operations'].split(',')
            graph = await graphs[graph_type](operations)
            return web.json_response(graph)
        except Exception as e:
            self.log.error(repr(e), exc_info=True)

    async def download_pdf(self, request):
        data = dict(await request.json())
        svg_data = data['graphs']
        self._save_svgs(svg_data)
        if data['operations']:
            operations = [o for o in await self.data_svc.locate('operations', match=await self._get_access(request))
                          if str(o.id) in data.get('operations')]
            filename = 'debrief_' + datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
            agents = await self.data_svc.locate('agents')
            pdf_bytes = self._build_pdf(operations, agents, filename, data['sections'])
            self._clean_downloads()
            return web.json_response(dict(filename=filename, pdf_bytes=pdf_bytes))
        return web.json_response('No or multiple operations selected')

    def _build_pdf(self, operations, agents, filename, sections):
        # pdf setup
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72, title=filename)
        story_obj = Story()
        styles = getSampleStyleSheet()
        pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
        title = styles['Heading1']
        title.fontName = 'VeraBd'
        title.textColor = 'maroon'
        title.fontSize = 24

        # content generation
        story_obj.append(Spacer(1, 36))
        story_obj.append_text("OPERATIONS DEBRIEF", title, 6)
        story_obj.append_text("<i>Generated on %s</i>" % datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                              styles['Normal'], 12)
        story_obj.append_text(story_obj.get_description('debrief'), styles['Normal'], 12)

        story_obj.append_text('STATISTICS', styles['Heading2'], 0)
        story_obj.append_text(story_obj.get_description('statistics'), styles['Normal'], 12)
        data = [['Name', 'State', 'Planner', 'Objective', 'Time']]
        for o in operations:
            finish = o.finish if o.finish else 'Not finished'
            data.append([o.name, o.state, o.planner.name, o.objective.name, finish])
        story_obj.append(story_obj.generate_table(data, '*'))

        story_obj.append_text('AGENTS', styles['Heading2'], 0)
        story_obj.append_text(story_obj.get_description('agents'), styles['Normal'], 12)
        agent_data = [['Paw', 'Host', 'Platform', 'Username', 'Privilege', 'Executable']]
        for a in agents:
            agent_data.append(['<a name="agent-{0}"/>{0}'.format(a.paw), a.host, a.platform, a.username, a.privilege,
                               a.exe_name])
        story_obj.append(story_obj.generate_table(agent_data, '*'))
        story_obj.page_break()

        if any(v for k, v in sections.items() if '-graph' in k):
            story_obj.append_text('OPERATIONS GRAPHS', styles['Heading2'], 0)
            graph_files = dict()
            for file in glob.glob('./plugins/debrief/downloads/*.svg'):
                graph_files[os.path.basename(file).split('.')[0]] = file
            if sections['default-graph']:
                story_obj.append_graph('graph', graph_files['graph'])
            if sections['attackpath-graph']:
                story_obj.append_graph('attack path', graph_files['attackpath'])
            if sections['tactic-graph']:
                story_obj.append_graph('tactic', graph_files['tactic'])
            if sections['technique-graph']:
                story_obj.append_graph('technique', graph_files['technique'])
            if sections['fact-graph']:
                story_obj.append_graph('fact', graph_files['fact'])
            story_obj.page_break()

        if sections['tactic-technique-table']:
            story_obj.append_text('TACTICS AND TECHNIQUES', styles['Heading2'], 0)
            ttps = self._generate_ttps(operations)
            story_obj.append(story_obj.generate_ttps(ttps))

        for o in operations:
            if sections['steps-table']:
                story_obj.append_text('STEPS IN OPERATION <font name=Courier-Bold size=17>%s</font>' % o.name.upper(),
                                      styles['Heading2'], 0)
                story_obj.append_text(story_obj.get_description('op steps'), styles['Normal'], 12)
                story_obj.append(story_obj.generate_op_steps(o))
            if sections['facts-table']:
                story_obj.append_text('FACTS FOUND IN OPERATION <font name=Courier-Bold size=17>%s</font>' % o.name.upper(),
                                      styles['Heading2'], 0)
                story_obj.append_text(story_obj.get_description('op facts'), styles['Normal'], 12)
                story_obj.append(story_obj.generate_facts_found(o))
                story_obj.page_break()

        # pdf teardown
        doc.build(story_obj.story_arr,
                  onFirstPage=story_obj.header_footer_first,
                  onLaterPages=story_obj.header_footer_rest)
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value.decode('utf-8', errors='ignore')

    @staticmethod
    def _generate_ttps(operations):
        ttps = dict()
        for op in operations:
            for link in op.chain:
                if not link.cleanup:
                    tactic_name = link.ability.tactic
                    if tactic_name not in ttps.keys():
                        tactic = dict(name=tactic_name,
                                      techniques={link.ability.technique_name: link.ability.technique_id},
                                      steps={op.name: [link.ability.name]})
                        ttps[tactic_name] = tactic
                    else:
                        if link.ability.technique_name not in ttps[tactic_name]['techniques'].keys():
                            ttps[tactic_name]['techniques'][link.ability.technique_name] = link.ability.technique_id
                        if op.name not in ttps[tactic_name]['steps'].keys():
                            ttps[tactic_name]['steps'][op.name] = [link.ability.name]
                        elif link.ability.name not in ttps[tactic_name]['steps'][op.name]:
                            ttps[tactic_name]['steps'][op.name].append(link.ability.name)
        return dict(sorted(ttps.items()))

    @staticmethod
    def _save_svgs(svgs):
        for filename, svg_bytes in svgs.items():
            save_location = './plugins/debrief/downloads/'
            with open(save_location + filename + '.svg', "wb") as fh:
                fh.write(base64.b64decode(svg_bytes))

    @staticmethod
    def _clean_downloads():
        imgs = []
        imgs.extend(glob.glob('./plugins/debrief/downloads/*.png'))
        imgs.extend(glob.glob('./plugins/debrief/downloads/*.svg'))
        for f in imgs:
            os.remove(f)

    @staticmethod
    def _suppress_logs(library):
        lib = logging.getLogger(library)
        lib.setLevel(logging.INFO)
