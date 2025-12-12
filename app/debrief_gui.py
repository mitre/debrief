import base64
import glob
import logging
import os
import re

from aiohttp import web
from aiohttp_jinja2 import template
from datetime import datetime
from importlib import import_module
from io import BytesIO
from reportlab import rl_settings
from reportlab.lib.pagesizes import letter, landscape as to_landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Spacer, PageTemplate, Frame, PageBreak, Flowable


from app.service.auth_svc import for_all_public_methods, check_authorization
from app.utility.base_world import BaseWorld
from plugins.debrief.app.debrief_svc import DebriefService
from plugins.debrief.app.objects.c_story import Story


LEFT_MARGIN = RIGHT_MARGIN = 72
TOP_MARGIN = BOTTOM_MARGIN = 84


@for_all_public_methods(check_authorization)
class DebriefGui(BaseWorld):
    def __init__(self, services):
        self.services = services
        self.debrief_svc = DebriefService(services)
        self.auth_svc = services.get('auth_svc')
        self.data_svc = services.get('data_svc')
        self.file_svc = services.get('file_svc')
        self.knowledge_svc = services.get('knowledge_svc')
        self.log = logging.getLogger('debrief_gui')
        self.uploads_dir = os.path.relpath(os.path.join('plugins', 'debrief', 'uploads'))

        self._suppress_logs('PIL')
        self._suppress_logs('svglib')
        self.report_section_modules = dict()
        self.report_section_names = list()
        self.loaded_report_sections = False

        rl_settings.trustedHosts = BaseWorld.get_config(prop='reportlab_trusted_hosts', name='debrief') or None
    
    async def _get_access(self, request):
        return dict(access=tuple(await self.auth_svc.get_permissions(request)))

    @template('debrief.html')
    async def splash(self, request):
        operations = [o.display for o in
                      await self.data_svc.locate('operations', match=await self._get_access(request))]
        uploaded_logos_dir = os.path.relpath(os.path.join(self.uploads_dir, 'header-logos'))
        header_logos = [filename for filename in os.listdir(uploaded_logos_dir) if os.path.isfile(
            os.path.relpath(os.path.join(uploaded_logos_dir, filename))
        ) and not filename.startswith('.')]
        try:
            plugins = await self.data_svc.locate('plugins', match=dict(enabled=True))
            self._load_report_sections(plugins)
        except Exception as e:
            self.log.error(e)
        return dict(operations=operations, header_logos=header_logos, report_sections=self.report_section_names)

    async def report_sections(self, request):
        try:
            plugins = await self.data_svc.locate('plugins', match=dict(enabled=True))
            self._load_report_sections(plugins)
            self.log.debug("Debrief report sections loaded successfully: %s", self.report_section_names)
        except Exception as e:
            self.log.error(e, stack_info=True, exc_info=True)
        report_sections = self.report_section_names
        return web.json_response(dict(report_sections=report_sections))

    async def report(self, request):
        data = dict(await request.json())
        operations = [o for o in await self.data_svc.locate('operations', match=await self._get_access(request))
                      if str(o.id) in data.get('operations')]
        op_displays = [o.display for o in operations]
        ttps = DebriefService.generate_ttps(operations)
        return web.json_response(dict(operations=op_displays, ttps=ttps))

    async def graph(self, request):
        graphs = {
            'steps': self.debrief_svc.build_steps_d3,
            'attackpath': self.debrief_svc.build_attackpath_d3,
            'fact': self.debrief_svc.build_fact_d3,
            'tactic': self.debrief_svc.build_tactic_d3,
            'technique': self.debrief_svc.build_technique_d3
        }
        try:
            graph_type = request.rel_url.query.get('type')
            if graph_type not in graphs:
                return web.json_response({'error': f'unknown graph type: {graph_type}'}, status=400)

            operations = request.rel_url.query.get('operations', '')
            op_ids = [o for o in operations.split(',') if o]
            graph = await graphs[graph_type](op_ids)
            return web.json_response(graph)
        except Exception as e:
            self.log.error("graph() failed: %r", e, exc_info=True)
            return web.json_response({'error': 'internal error'}, status=500)

    async def download_pdf(self, request):
        data = dict(await request.json())
        svg_data = data['graphs']
        header_logo_filename = data.get('header-logo')
        self._save_svgs(svg_data)
        try:
            if data['operations']:
                header_logo_path = None
                if header_logo_filename:
                    header_logo_path = os.path.relpath(os.path.join(self.uploads_dir, 'header-logos', header_logo_filename))
                access = await self._get_access(request)
                operations = [o for o in await self.data_svc.locate('operations', match=access)
                              if str(o.id) in data.get('operations', [])]
                op_name = operations[0].name if operations else 'Operation'
                safe_op_name = re.sub(r'[^A-Za-z0-9_-]+', '-', op_name)
                runtime_paws = set()
                    for op in operations or []:
                        for ln in getattr(op, 'chain', []) or []:
                            paw = getattr(ln, 'paw', None)
                            if paw:
                                runtime_paws.add(paw)

                date_part = datetime.now().strftime('%Y_%m_%d')
                filename = f"{safe_op_name}_Debrief_{date_part}.pdf"
                pdf_bytes = await self._build_pdf(operations, agents, filename, data['report-sections'], header_logo_path)
                self._clean_downloads()
                return web.json_response(dict(filename=filename, pdf_bytes=pdf_bytes))
            return web.json_response({'error': 'No operations selected'}, status=400)
        except Exception as e:
            self.log.error("download_pdf() failed: %r", e, exc_info=True)
            return web.json_response({'error': 'Error generating PDF report'}, status=500)

    async def download_json(self, request):
        data = dict(await request.json())
        if data['operations']:
            operations = [await o.report(file_svc=self.file_svc, data_svc=self.data_svc, output=True) for o in
                          await self.data_svc.locate('operations', match=await self._get_access(request))
                          if str(o.id) in data.get('operations')]
            filename = 'debrief_' + datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
            return web.json_response(dict(filename=filename, json_bytes=operations))
        return web.json_response('No operations selected')

    async def all_logos(self, request):
        uploaded_logos_dir = os.path.relpath(os.path.join(self.uploads_dir, 'header-logos'))
        logos = [filename for filename in os.listdir(uploaded_logos_dir) if os.path.isfile(
            os.path.relpath(os.path.join(uploaded_logos_dir, filename))
        ) and not filename.startswith('.')]
        return web.json_response(dict(logos=logos))

    async def upload_logo(self, request):
        data = await request.post()
        logo_file_info = data['header-logo']
        if logo_file_info:
            logo_file = logo_file_info.file
            content = logo_file.read()
            sanitized_filename = self._sanitize_filename(logo_file_info.filename)
            try:
                self._save_uploaded_image(sanitized_filename, content)
            except Exception as e:
                return web.json_response(str(e))
            return web.json_response({"filename": sanitized_filename})
        return web.json_response('No header logo file provided.')

    def _save_uploaded_image(self, filename, content):
        filepath = os.path.relpath(os.path.join(self.uploads_dir, 'header-logos', filename))
        with open(filepath, 'wb') as f:
            f.write(content)

    def _load_report_sections(self, plugins):
        if not self.loaded_report_sections:
            for plugin in plugins:
                if plugin.name:
                    report_sections_dir = os.path.relpath(
                        os.path.join('plugins', plugin.name, 'app', 'debrief-sections'))
                    if os.path.isdir(report_sections_dir):
                        for filepath in glob.iglob(f'{report_sections_dir}/*.py'):
                            module_name = filepath.replace('/', '.').replace('\\', '.').replace('.py', '')
                            try:
                                module = import_module(module_name)
                                module_obj = module.DebriefReportSection()
                                safe_id = re.sub('[^A-Za-z0-9-_:.]', '', re.sub(r'\s+', '-', module_obj.id))
                                self.report_section_modules[safe_id] = module_obj
                                self.report_section_names.append({'key': safe_id, 'name': module_obj.display_name})
                            except Exception as e:
                                self.log.error("Skipping debrief section %s due to error: %r", module_name, e, exc_info=True)
                    self.log.debug("Finished loading debrief report sections.")
            self.report_section_names.sort(key=lambda s: s['name'].lower())
            self.loaded_report_sections = True

    def _pretty_name(self, trait: str) -> str:
        # fallback pretty name when no explicit name is present
        # examples: "server.malicious.url" -> "Server Malicious Url"
        return ' '.join(p.capitalize() for p in str(trait).replace('_', '.').split('.') if p)

    async def _build_whitecard_metrics(self, operation):
        """
        Build a list of {name, trait, value, source_id} derived from facts in the operation's 'source'
        (the white cards). We only keep numeric facts.
        """
        metrics = []
        if not getattr(operation, 'source', None):
            return metrics

        source_id = getattr(operation.source, 'id', None) or getattr(operation.source, 'source', None)
        if not source_id:
            return metrics

        # Pull all facts from this source (white cards)
        # NOTE: knowledge_svc is already available in Caldera plugins.
        facts = await self.knowledge_svc.get_facts(criteria=dict(source=source_id))  # returns c_fact objects

        for f in facts or []:
            # try to resolve a friendly name if present in metadata; else prettify the trait
            meta = getattr(f, 'meta', None) or {}
            friendly = meta.get('display_name') or meta.get('name') or self._pretty_name(getattr(f, 'trait', ''))

            # only include numeric-ish values
            val = getattr(f, 'value', None)
            if val is None:
                continue
            try:
                num = int(val)
            except (ValueError, TypeError):
                try:
                    num = float(val)
                except (ValueError, TypeError):
                    continue

            metrics.append({
                'name': friendly,
                'trait': getattr(f, 'trait', ''),
                'value': num,
                'source_id': getattr(f, 'source', ''),
            })
        return metrics

    async def _build_pdf(self, operations, agents, filename, sections, header_logo_path):
        self._landscape_locked = False 
        pdf_buffer = BytesIO()
        doc = TemplateSwitchDoc(
            pdf_buffer,
            pagesize=letter,
            rightMargin=RIGHT_MARGIN,
            leftMargin=LEFT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            title=filename
        )

        story_obj = Story()
        story_obj.set_header_logo_path(header_logo_path)
        story_obj.append(Spacer(1, 36))
        styles = getSampleStyleSheet()

        # Decide if Detections is the only section (controls first page orientation)
        sections = list(sections or [])
        detections_only = (len(sections) == 1 and sections[0] == 'ttps-detections')

        # Always render Detections last if present (unless it's the only section)
        if 'ttps-detections' in sections and not detections_only:
            sections = [s for s in sections if s != 'ttps-detections'] + ['ttps-detections']

        # Frames
        portrait_frame = Frame(
            doc.leftMargin, doc.bottomMargin,
            doc.width, doc.height,
            id="portrait-frame"
        )
        lm = bm = rm = tm = 18
        lw, lh = to_landscape(letter)
        landscape_frame = Frame(
            lm, bm,
            lw - (lm + rm),
            lh - (tm + bm),
            id="landscape-frame"
        )

        # PageTemplates
        portrait_first_tpl = PageTemplate(id="PortraitFirst", frames=[portrait_frame], pagesize=letter,
                                          onPage=story_obj.header_footer_first)
        portrait_tpl = PageTemplate(id="Portrait", frames=[portrait_frame], pagesize=letter,
                                    onPage=story_obj.header_footer_rest)
        landscape_first_tpl = PageTemplate(id="LandscapeFirst", frames=[landscape_frame], pagesize=to_landscape(letter),
                                           onPage=story_obj.header_footer_first)
        landscape_tpl = PageTemplate(id="Landscape", frames=[landscape_frame], pagesize=to_landscape(letter),
                                     onPage=story_obj.header_footer_rest)

        if detections_only:
            # Make LandscapeFirst the default starting template
            doc.addPageTemplates([
                landscape_first_tpl,  # first page: landscape + first-page header/footer
                landscape_tpl,        # subsequent pages in landscape
                portrait_tpl,
                portrait_first_tpl,
            ])
            story_obj.append(LockTemplateMarker('Landscape')) 
        else:
            # Default is portrait; we'll switch to landscape only for the detections block
            doc.addPageTemplates([
                portrait_first_tpl,
                portrait_tpl,
                landscape_tpl,
                landscape_first_tpl,
            ])

        # Collect SVG graphs if any
        graph_files = {}
        if any(('-graph' in v) for v in sections):
            for file in glob.glob('./plugins/debrief/downloads/*.svg'):
                graph_files[os.path.basename(file).split('.')[0]] = file

        try:
            # ---- COVER: ----
            cover_module = self.report_section_modules.get('main-summary')
            if cover_module:
                cover_flowables = await cover_module.generate_section_elements(
                    styles,
                    operations=operations,
                    agents=agents,
                    graph_files=graph_files,
                    selected_sections=sections
                )
                if cover_flowables:
                    for f in cover_flowables:
                        story_obj.append(f)

            # ---- SECTIONS: append each section’s flowables ----
            for section in sections:
                section_module = self.report_section_modules.get(section)
                if not section_module:
                    self.log.error("Requested debrief section module %s not found.", section)
                    continue

                flowables = await section_module.generate_section_elements(
                    styles,
                    operations=operations,
                    agents=agents,
                    graph_files=graph_files,
                    selected_sections=sections
                )
                if (section == 'ttps-detections'
                    and not getattr(self, '_landscape_locked', False)
                    and not detections_only):
                    story_obj.append(UseTemplateMarker('LandscapeFirst'))
                    story_obj.append(PageBreak())
                    # lock landscape for the remainder of the doc
                    story_obj.append(LockTemplateMarker('Landscape'))
                    self._landscape_locked = True
                for f in flowables:
                    story_obj.append(f)

            # Build PDF
            doc.build(story_obj.story_arr)

        except Exception as e:
            self.log.error(e)

        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value.decode('utf-8', errors='ignore')

    @staticmethod
    def _sanitize_filename(filename):
        _, split_name = os.path.split(filename)
        cleaned = re.sub(r'(?u)[^-\w._]', '', split_name).strip()
        return re.sub(r'\s+', '_', cleaned)

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


# --- Template switch primitives that work on all ReportLab versions ---

class UseTemplateMarker(Flowable):
    """A zero-size flowable that signals a page-template switch."""
    def __init__(self, name: str):
        super().__init__()
        self.name = name
    def wrap(self, *args, **kwargs):
        return (0, 0)
    def draw(self):
        pass

class LockTemplateMarker(Flowable):
    """Locks the page template for all subsequent pages."""
    def __init__(self, name: str):
        super().__init__()
        self.name = name
    def wrap(self, *args, **kwargs):
        return (0, 0)
    def draw(self):
        pass

class TemplateSwitchDoc(SimpleDocTemplate):
    """SimpleDocTemplate that reacts to UseTemplateMarker/LockTemplateMarker."""
    def afterFlowable(self, flowable):
        try:
            if isinstance(flowable, UseTemplateMarker):
                # Force the very next page
                self.handle_nextPageTemplate(flowable.name)

            if isinstance(flowable, LockTemplateMarker):
                # Persistently force all subsequent pages
                self._locked_template = flowable.name
                self.handle_nextPageTemplate(self._locked_template)
            
            if isinstance(flowable, PageBreak) and getattr(self, '_locked_template', None):
                self.handle_nextPageTemplate(self._locked_template)

            # If locked, keep reasserting the template after each flowable
            if getattr(self, '_locked_template', None):
                self.handle_nextPageTemplate(self._locked_template)
        except Exception:
            pass
