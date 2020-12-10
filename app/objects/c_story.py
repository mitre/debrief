from lxml import etree as ET
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, PageBreak, Image, CondPageBreak


class Story:
    _header_logo_path = None

    def __init__(self):
        self.story_arr = []

    def append(self, data):
        self.story_arr.append(data)
        self.story_arr.append(Spacer(1, 12))

    def append_text(self, text, style, space):
        self.story_arr.append(Paragraph(text, style))
        self.story_arr.append(Spacer(1, space))

    def get_description(self, desc):
        return self._descriptions(desc)

    def page_break(self):
        self.story_arr.append(PageBreak())

    def conditional_page_break(self, height):
        self.story_arr.append(CondPageBreak(height))

    @staticmethod
    def set_header_logo_path(header_logo_path):
        Story._header_logo_path = header_logo_path

    @staticmethod
    def header_footer_first(canvas, doc):
        # Save the state of our canvas so we can draw on it
        canvas.saveState()

        # Header
        caldera_logo = "./plugins/debrief/static/img/caldera.png"
        im = Image(caldera_logo, 1.5 * inch, 1 * inch)
        im.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - im.drawHeight / 2)

        if Story._header_logo_path:
            Story.draw_header_logo(canvas, doc, Story._header_logo_path)

        canvas.setStrokeColor(colors.maroon)
        canvas.setLineWidth(4)
        canvas.line(doc.leftMargin + im.drawWidth + 5,
                    doc.height + doc.topMargin,
                    doc.width + doc.leftMargin,
                    doc.height + doc.topMargin)

        # Footer
        page_num = canvas.getPageNumber()
        text = "Page %s" % page_num
        canvas.drawRightString(doc.width + doc.rightMargin * 1.5, doc.bottomMargin / 2, text)

        # Release the canvas
        canvas.restoreState()

    @staticmethod
    def header_footer_rest(canvas, doc):
        # Save the state of our canvas so we can draw on it
        canvas.saveState()

        # Header
        if Story._header_logo_path:
            Story.draw_header_logo(canvas, doc, Story._header_logo_path)

        canvas.setFillColor(colors.maroon)
        canvas.setFont('VeraBd', 18)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin * 1.25, 'OPERATIONS DEBRIEF')
        canvas.setStrokeColor(colors.maroon)
        canvas.setLineWidth(4)
        canvas.line(doc.leftMargin,
                    doc.height + doc.topMargin * 1.25 - 5,
                    doc.width + doc.leftMargin,
                    doc.height + doc.topMargin * 1.25 - 5)

        # Footer
        canvas.setFillColor(colors.black)
        canvas.setFont('Helvetica', 10)
        page_num = canvas.getPageNumber()
        text = "Page %s" % page_num
        canvas.drawRightString(doc.width + doc.rightMargin * 1.5, doc.bottomMargin / 2, text)

        # Release the canvas
        canvas.restoreState()

    @staticmethod
    def draw_header_logo(canvas, doc, logo_path):
        im = Image(logo_path, 2.5 * inch, 0.75 * inch)
        im.drawOn(canvas, doc.width + doc.leftMargin + doc.rightMargin - im.drawWidth - 10,
                  doc.height + doc.topMargin + doc.bottomMargin - im.drawHeight - 10)

    @staticmethod
    def adjust_icon_svgs(path):
        svg = ET.parse(path)
        for icon_svg in svg.getroot().iter("{http://www.w3.org/2000/svg}svg"):
            if icon_svg.get('id') == 'copy-svg':
                continue
            viewbox = [int(float(val)) for val in icon_svg.get('viewBox').split()]
            aspect = viewbox[2] / viewbox[3]
            icon_svg.set('width', str(round(float(icon_svg.get('height')) * aspect)))
            if not icon_svg.get('id') or 'legend' not in icon_svg.get('id'):
                icon_svg.set('x', '-' + str(int(icon_svg.get('width')) / 2))
        svg.write(open(path, 'wb'))

    @staticmethod
    def get_table_object(val):
        table = ParagraphStyle(name='Table', fontSize=8)
        if type(val) == str:
            return Paragraph(val, table)
        elif type(val) == list:
            list_string = ''
            for list_item in val:
                list_string += list_item + '<br/>'
            return Paragraph(list_string, table)
        elif type(val) == dict:
            dict_string = ''
            for k, v in val.items():
                dict_string += '<font color=grey>' + k + '</font><br/>'
                for list_item in v:
                    dict_string += '&nbsp;&nbsp;&nbsp;' + list_item + '<br/>'
            return Paragraph(dict_string, table)

    @staticmethod
    def _descriptions(obj):
        if obj == 'debrief':
            return 'This document covers the overall campaign analytics made up of the selected set of operations. ' \
                   'The below sections contain general metadata about the selected operations as well as ' \
                   'graphical views of the operations, the techniques and tactics used, and the facts discovered by ' \
                   'the operations. The following sections include a more in depth review of each specific operation ' \
                   'ran.'
        elif obj == 'agents':
            return 'The table below displays information about the agents used. An agent\'s paw is the unique' \
                   ' identifier, or paw print, of an agent. Also included are the username of the user who executed ' \
                   'the agent, the privilege level of the agent process, and the name of the agent executable.'
        elif obj == 'op steps':
            return 'The table below shows detailed information about the steps taken in an operation and whether the ' \
                   'command run discovered any facts.'
        elif obj == 'op facts':
            return 'The table below displays the facts found in the operation, the command run and the agent that ' \
                   'found the fact. Every fact, by default, gets a score of 1. If a host.user.password fact is ' \
                   'important or has a high chance of success if used, you may assign it a score of 5. When an ' \
                   'ability uses a fact to fill in a variable, it will use those with the highest scores first. A ' \
                   'fact with a score of 0, is blacklisted - meaning it cannot be used in an operation.'
        elif obj == 'graph':
            return 'This is a graphical display of the agents connected to the command and control (C2), the ' \
                   'operations run, and the steps of each operation as they relate to the agents.'
        elif obj == 'fact':
            return 'This graph displays the facts discovered by the operations run. Facts are attached to the ' \
                   'operation where they were discovered. Facts are also attached to the facts that led to their ' \
                   'discovery. For readability, only the first 15 facts discovered in an operation are included in ' \
                   'the graph.'
        elif obj == 'technique':
            return 'This graph displays the order of techniques executed by the operation. A technique explains the ' \
                   'technical method or the "how" of a step.'
