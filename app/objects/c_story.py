import html

from lxml import etree as ET
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, PageBreak, Image


class Story:
    _header_logo_path = None

    def __init__(self):
        self.story_arr = []

    def append(self, data, spacing=12):
        self.story_arr.append(data)
        self.story_arr.append(Spacer(1, spacing))

    def append_text(self, text, style, space):
        self.story_arr.append(Paragraph(html.escape(text), style))
        self.story_arr.append(Spacer(1, space))

    def page_break(self):
        self.story_arr.append(PageBreak())

    @staticmethod
    def set_header_logo_path(header_logo_path):
        Story._header_logo_path = header_logo_path

    @staticmethod
    def _page_margins(canvas, doc):
        """Return (left, right, top, bottom) margins appropriate for the current page.

        Landscape pages use the frame margins (18pt) rather than the doc-level
        portrait margins (72/84pt).
        """
        page_w, page_h = canvas._pagesize
        if page_w > page_h:  # landscape
            frame = doc.frame if hasattr(doc, 'frame') else None
            if frame:
                lm = frame._x1
                bm = frame._y1
                rm = page_w - frame._x1 - frame._width
                tm = page_h - frame._y1 - frame._height
                return lm, rm, tm, bm
        return doc.leftMargin, doc.rightMargin, doc.topMargin, doc.bottomMargin

    @staticmethod
    def header_footer_first(canvas, doc):
        canvas.saveState()

        page_w, page_h = canvas._pagesize
        lm, rm, tm, bm = Story._page_margins(canvas, doc)
        is_landscape = page_w > page_h

        # Header — landscape pages have only 18pt margin, too narrow for
        # the 1-inch logo; skip header entirely on landscape first pages.
        if not is_landscape:
            caldera_logo = "./plugins/debrief/static/img/caldera.png"
            im = Image(caldera_logo, 1.5 * inch, 1 * inch)
            # Position header above the content frame (in the top margin area)
            header_y = page_h - tm + im.drawHeight / 2
            im.drawOn(canvas, lm, page_h - tm)

            if Story._header_logo_path:
                Story.draw_header_logo(canvas, doc, Story._header_logo_path)

            canvas.setStrokeColor(colors.maroon)
            canvas.setLineWidth(4)
            canvas.line(lm + im.drawWidth + 5, header_y,
                        page_w - rm, header_y)

        # Footer
        page_num = canvas.getPageNumber()
        text = "Page %s" % page_num
        canvas.drawRightString(page_w - rm, bm / 2, text)

        canvas.restoreState()

    @staticmethod
    def header_footer_rest(canvas, doc):
        canvas.saveState()

        page_w, page_h = canvas._pagesize
        lm, rm, tm, bm = Story._page_margins(canvas, doc)

        # Header — skip entirely on landscape pages (18pt margin too narrow)
        is_landscape = page_w > page_h
        if not is_landscape:
            if Story._header_logo_path:
                Story.draw_header_logo(canvas, doc, Story._header_logo_path)
            # Portrait pages have room for the full header
            header_y = page_h - tm * 0.75
            canvas.setFillColor(colors.maroon)
            canvas.setFont('Helvetica-Bold', 18)
            canvas.drawString(lm, header_y, 'OPERATIONS DEBRIEF')
            canvas.setStrokeColor(colors.maroon)
            canvas.setLineWidth(4)
            canvas.line(lm, header_y - 5, page_w - rm, header_y - 5)
        # Landscape pages: skip header — 18pt margin is too narrow

        # Footer
        canvas.setFillColor(colors.black)
        canvas.setFont('Helvetica', 10)
        page_num = canvas.getPageNumber()
        text = "Page %s" % page_num
        canvas.drawRightString(page_w - rm, bm / 2, text)

        canvas.restoreState()

    @staticmethod
    def draw_header_logo(canvas, doc, logo_path):
        page_w, page_h = canvas._pagesize
        im = Image(logo_path, 2.5 * inch, 0.75 * inch)
        im.drawOn(canvas, page_w - im.drawWidth - 10,
                  page_h - im.drawHeight - 10)

    SVG_NS = 'http://www.w3.org/2000/svg'
    _icon_cache = {}

    @classmethod
    def _load_icon_svg(cls, icon_path):
        """Read an SVG icon file and return its root element for inlining."""
        if icon_path in cls._icon_cache:
            return cls._icon_cache[icon_path]
        try:
            import os
            if not os.path.isfile(icon_path):
                return None
            parser = ET.XMLParser(
                resolve_entities=False, no_network=True,
                dtd_validation=False, load_dtd=False,
            )
            tree = ET.parse(icon_path, parser)
            cls._icon_cache[icon_path] = tree.getroot()
            return cls._icon_cache[icon_path]
        except Exception:
            return None

    @staticmethod
    def adjust_icon_svgs(path):
        parser = ET.XMLParser(
            resolve_entities=False,
            no_network=True,
            dtd_validation=False,
            load_dtd=False,
        )
        svg = ET.parse(path, parser)
        root = svg.getroot()
        ns = Story.SVG_NS

        # Inline external <image> icons that have data-icon-path attributes
        for img_el in root.iter('{%s}image' % ns):
            icon_path = img_el.get('data-icon-path')
            if not icon_path:
                continue

            icon_root = Story._load_icon_svg(icon_path)
            if icon_root is None:
                continue

            # Get placement from the <image> element
            x = float(img_el.get('x', 0))
            y = float(img_el.get('y', 0))
            w = float(img_el.get('width', 40))
            h = float(img_el.get('height', 40))

            # Create an inline <svg> with the icon's viewBox and content
            vb = icon_root.get('viewBox', '0 0 512 512')
            inline_svg = ET.SubElement(img_el.getparent(), '{%s}svg' % ns)
            inline_svg.set('data-inlined-icon', 'true')
            inline_svg.set('viewBox', vb)
            inline_svg.set('x', str(x))
            inline_svg.set('y', str(y))
            inline_svg.set('width', str(w))
            inline_svg.set('height', str(h))

            # Copy all children from the icon SVG
            import copy
            for child in icon_root:
                inline_svg.append(copy.deepcopy(child))

            # Remove the original <image> element
            img_el.getparent().remove(img_el)

        # Legacy D3 graph icon adjustment (skip inlined topology icons)
        for icon_svg in root.iter('{%s}svg' % ns):
            if icon_svg.get('id') == 'copy-svg':
                continue
            if icon_svg.get('data-inlined-icon'):
                continue
            viewbox_attr = icon_svg.get('viewBox')
            if not viewbox_attr:
                continue
            viewbox = [int(float(val)) for val in viewbox_attr.split()]
            aspect = viewbox[2] / viewbox[3]
            height = icon_svg.get('height')
            if height and not icon_svg.get('data-icon-path'):
                try:
                    icon_svg.set('width', str(round(float(height) * aspect)))
                    if not icon_svg.get('id') or 'legend' not in icon_svg.get('id'):
                        icon_svg.set('x', '-' + str(int(icon_svg.get('width')) / 2))
                except (ValueError, TypeError):
                    pass

        with open(path, 'wb') as f:
            svg.write(f)

    _TABLE_STYLE = ParagraphStyle(name='Table', fontSize=8, wordWrap='CJK')

    @staticmethod
    def get_table_object(val, escape_html=True):
        style = Story._TABLE_STYLE
        if type(val) is str:
            escaped = html.escape(val) if escape_html else val
            return Paragraph(escaped, style)
        elif type(val) is list:
            escaped = [html.escape(list_item) for list_item in val] if escape_html else val
            return Paragraph('<br/>'.join(escaped), style)
        elif type(val) is dict:
            dict_string = ''
            for k, v in val.items():
                escaped_key = html.escape(k) if escape_html else k
                dict_string += '<font color=grey>' + escaped_key + '</font><br/>'
                for list_item in v:
                    escaped = html.escape(list_item) if escape_html else list_item
                    dict_string += '&nbsp;&nbsp;&nbsp;' + escaped + '<br/>'
            return Paragraph(dict_string, style)
