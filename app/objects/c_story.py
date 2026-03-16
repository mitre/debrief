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
        self.story_arr.append(Paragraph(text, style))
        self.story_arr.append(Spacer(1, space))

    def get_description(self, desc):
        return self._descriptions(desc)

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

        # Header
        caldera_logo = "./plugins/debrief/static/img/caldera.png"
        im = Image(caldera_logo, 1.5 * inch, 1 * inch)
        header_y = page_h - tm
        im.drawOn(canvas, lm, header_y - im.drawHeight / 2)

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

        # Header
        if Story._header_logo_path:
            Story.draw_header_logo(canvas, doc, Story._header_logo_path)

        is_landscape = page_w > page_h
        if not is_landscape:
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

    @staticmethod
    def adjust_icon_svgs(path):
        parser = ET.XMLParser(resolve_entities=False)
        svg = ET.parse(path, parser)
        for icon_svg in svg.getroot().iter("{http://www.w3.org/2000/svg}svg"):
            if icon_svg.get('id') == 'copy-svg':
                continue
            viewbox_attr = icon_svg.get('viewBox')
            if not viewbox_attr:
                continue
            viewbox = [int(float(val)) for val in viewbox_attr.split()]
            aspect = viewbox[2] / viewbox[3]
            icon_svg.set('width', str(round(float(icon_svg.get('height')) * aspect)))
            if not icon_svg.get('id') or 'legend' not in icon_svg.get('id'):
                icon_svg.set('x', '-' + str(int(icon_svg.get('width')) / 2))
        with open(path, 'wb') as f:
            svg.write(f)

    @staticmethod
    def get_table_object(val):
        table = ParagraphStyle(name='Table', fontSize=8)
        if type(val) is str:
            return Paragraph(val, table)
        elif type(val) is list:
            list_string = ''
            for list_item in val:
                list_string += list_item + '<br/>'
            return Paragraph(list_string, table)
        elif type(val) is dict:
            dict_string = ''
            for k, v in val.items():
                dict_string += '<font color=grey>' + k + '</font><br/>'
                for list_item in v:
                    dict_string += '&nbsp;&nbsp;&nbsp;' + list_item + '<br/>'
            return Paragraph(dict_string, table)
