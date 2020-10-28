from lxml import etree as ET
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from svglib.svglib import svg2rlg


class Story:
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

    def generate_table(self, data, col_widths):
        data[1:] = [[self._get_table_object(val) for val in row] for row in data[1:]]
        tbl = Table(data, colWidths=col_widths)
        tbl.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.maroon),
                                 ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                 ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                 ('FONTSIZE', (0, 1), (-1, -1), 8),
                                 ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                 ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
                                 ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                 ]))
        for each in range(1, len(data)):
            if each % 2 == 0:
                bg_color = colors.lightgrey
            else:
                bg_color = colors.whitesmoke

            tbl.setStyle(TableStyle([('BACKGROUND', (0, each), (-1, each), bg_color)]))
        return tbl

    def append_graph(self, name, path):
        styles = getSampleStyleSheet()
        if name == 'graph':
            self.append_text('Operations Graph', styles['Heading3'], 12)
        else:
            self.append_text('%s Graph' % name.title(), styles['Heading3'], 0)
        self.append_text(self.get_description(name), styles['Normal'], 12)

        self._adjust_icon_svgs(path)
        graph = svg2rlg(path)
        aspect = graph.height / float(graph.width)
        self.append(Image(graph, width=4*inch, height=(4*inch * aspect)))

    def generate_ttps(self, ttps):
        ttp_data = [['Tactics', 'Techniques', 'Abilities']]
        for key, tactic in ttps.items():
            technique_arr = []
            for name, tid in tactic['techniques'].items():
                technique_arr.append(tid + ': ' + name)
            ttp_data.append([tactic['name'].capitalize(), technique_arr, tactic['steps']])
        return self.generate_table(ttp_data, [1.25 * inch, 3.25 * inch, 2 * inch])

    def generate_op_steps(self, operation):
        steps = [['Time', 'Status', 'Agent', 'Name', 'Command', 'Facts']]
        for link in operation.chain:
            steps.append(
                [link.finish or '', self._status_name(link.status), link.paw, link.ability.name, link.decode_bytes(link.command),
                 'Yes' if len([f for f in link.facts if f.score > 0]) > 0 else 'No'])

        return self.generate_table(steps, [.75*inch, .6*inch, .6*inch, .85*inch, 3*inch, .6*inch])

    def generate_facts_found(self, operation):
        fact_data = [['Trait', 'Value', 'Score', 'Paw', 'Command Run']]
        for lnk in operation.chain:
            if len(lnk.facts) > 0:
                for f in lnk.facts:
                    fact_data.append([f.trait, f.value, str(f.score),
                                      '<link href="#agent-{0}" color="blue">{0}</link>'.format(lnk.paw),
                                      lnk.decode_bytes(lnk.command)])
        return self.generate_table(fact_data, [1*inch, 1.2*inch, .6*inch, .6*inch, 3*inch])

    @staticmethod
    def header_footer_first(canvas, doc):
        # Save the state of our canvas so we can draw on it
        canvas.saveState()

        # Header
        logo = "./plugins/debrief/static/img/caldera.png"
        im = Image(logo, 1.5 * inch, 1 * inch)
        im.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - im.drawHeight / 2)
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
    def _adjust_icon_svgs(path):
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
    def _get_table_object(val):
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

    @staticmethod
    def _descriptions(obj):
        if obj == 'debrief':
            return 'This document covers the overall campaign analytics made up of the selected set of operations. ' \
                   'The below sections contain general metadata about the selected operations as well as ' \
                   'graphical views of the operations, the techniques and tactics used, and the facts discovered by ' \
                   'the operations. The following sections include a more in depth review of each specific operation ' \
                   'ran.'
        elif obj == 'statistics':
            return 'An operation\'s planner makes up the decision making process. It contains logic for how a ' \
                   'running operation should make decisions about which abilities to use and in what order. An ' \
                   'objective is a collection of fact targets, called goals, which can be tied to adversaries. ' \
                   'During the course of an operation, every time the planner is evaluated, the current objective ' \
                   'status is evaluated in light of the current knowledge of the operation, with the operation ' \
                   'completing should all goals be met.'
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
        elif obj == 'attack path':
            return 'This is a graphical display of the attack path taken in the campaign. Agents link back to the ' \
                   'command and control (C2) and are linked to each other via a lateral movement node if one agent ' \
                   'performed lateral movement to gain access to the other agent.'
        elif obj == 'fact':
            return 'This graph displays the facts discovered by the operations run. Facts are attached to the ' \
                   'operation where they were discovered. Facts are also attached to the facts that led to their ' \
                   'discovery. For readability, only the first 15 facts discovered in an operation are included in ' \
                   'the graph.'
        elif obj == 'tactic':
            return 'This graph displays the order of tactics executed by the operation. A tactic explains the ' \
                   'general purpose or the "why" of a step.'
        elif obj == 'technique':
            return 'This graph displays the order of techniques executed by the operation. A technique explains the ' \
                   'technical method or the "how" of a step.'
