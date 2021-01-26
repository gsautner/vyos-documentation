import re
import json
import os
from docutils import io, nodes, utils, statemachine
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst import Directive, directives, states

from sphinx.util.docutils import SphinxDirective

from testcoverage import get_working_commands


def setup(app):

    app.add_config_value(
        'vyos_phabricator_url',
        'https://phabricator.vyos.net/',
        'html'
    )

    app.add_config_value(
        'vyos_working_commands',
        #get_working_commands(),
        {"cfgcmd": [], "opcmd": []},
        'html'
    )
    app.add_config_value(
        'vyos_coverage',
        {
            'cfgcmd': [0,len(app.config.vyos_working_commands['cfgcmd'])],
            'opcmd': [0,len(app.config.vyos_working_commands['opcmd'])]
        },
        'html'
    )

    app.add_role('vytask', vytask_role)
    app.add_role('cfgcmd', cmd_role)
    app.add_role('opcmd', cmd_role)

    app.add_node(
        inlinecmd,
        html=(inlinecmd.visit_span, inlinecmd.depart_span),
        latex=(inlinecmd.visit_tex, inlinecmd.depart_tex),
        text=(inlinecmd.visit_span, inlinecmd.depart_span)
    )

    app.add_node(
        CmdDiv,
        html=(CmdDiv.visit_div, CmdDiv.depart_div),
        latex=(CmdDiv.visit_tex, CmdDiv.depart_tex),
        text=(CmdDiv.visit_div, CmdDiv.depart_div)
    )
    app.add_node(
        CmdBody,
        html=(CmdBody.visit_div, CmdBody.depart_div),
        latex=(CmdBody.visit_tex, CmdBody.depart_tex),
        text=(CmdBody.visit_div, CmdBody.depart_div)
    )
    app.add_node(
        CmdHeader,
        html=(CmdHeader.visit_div, CmdHeader.depart_div),
        latex=(CmdHeader.tex, CmdHeader.tex),
        text=(CmdHeader.visit_div, CmdHeader.depart_div)
    )
    app.add_node(CfgcmdList)
    app.add_node(CfgcmdListCoverage)
    app.add_directive('cfgcmdlist', CfgcmdlistDirective)

    app.add_node(OpcmdList)
    app.add_node(OpcmdListCoverage)
    app.add_directive('opcmdlist', OpcmdlistDirective)

    app.add_directive('cfgcmd', CfgCmdDirective)
    app.add_directive('opcmd', OpCmdDirective)
    app.add_directive('cmdinclude', CfgInclude)
    app.connect('doctree-resolved', process_cmd_nodes)

class CfgcmdList(nodes.General, nodes.Element):
    pass

class OpcmdList(nodes.General, nodes.Element):
    pass

class CfgcmdListCoverage(nodes.General, nodes.Element):
    pass

class OpcmdListCoverage(nodes.General, nodes.Element):
    pass

class CmdHeader(nodes.General, nodes.Element):

    @staticmethod
    def visit_div(self, node):
        self.body.append(self.starttag(node, 'div'))

    @staticmethod
    def depart_div(self, node=None):
        # self.body.append('</div>\n')
        self.body.append('<a class="cmdlink" href="#%s" ' %
                        node.children[0]['refid'] +
                        'title="%s"></a></div>' % (
                        'Permalink to this Command'))

    @staticmethod
    def tex(self, node=None):
        pass


class CmdDiv(nodes.General, nodes.Element):

    @staticmethod
    def visit_div(self, node):
        self.body.append(self.starttag(node, 'div'))

    @staticmethod
    def depart_div(self, node=None):
        self.body.append('</div>\n')

    @staticmethod
    def tex(self, node=None):
        pass

    @staticmethod
    def visit_tex(self, node=None):
        self.body.append('\n\n\\begin{changemargin}{0cm}{0cm}\n')

    @staticmethod
    def depart_tex(self, node=None):
        self.body.append('\n\\end{changemargin}\n\n')

class CmdBody(nodes.General, nodes.Element):

    @staticmethod
    def visit_div(self, node):
        self.body.append(self.starttag(node, 'div'))

    @staticmethod
    def depart_div(self, node=None):
        self.body.append('</div>\n')

    @staticmethod
    def visit_tex(self, node=None):
        self.body.append('\n\n\\begin{changemargin}{0.5cm}{0.5cm}\n')


    @staticmethod
    def depart_tex(self, node=None):
        self.body.append('\n\\end{changemargin}\n\n')


    @staticmethod
    def tex(self, node=None):
        pass


class inlinecmd(nodes.inline):

    @staticmethod
    def visit_span(self, node):
        self.body.append(self.starttag(node, 'span'))

    @staticmethod
    def depart_span(self, node=None):
        self.body.append('</span>\n')

    @staticmethod
    def visit_tex(self, node=None):
        self.body.append(r'\sphinxbfcode{\sphinxupquote{')
        #self.literal_whitespace += 1

    @staticmethod
    def depart_tex(self, node=None):
        self.body.append(r'}}')
        #self.literal_whitespace -= 1


class CfgInclude(SphinxDirective):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'var0': str,
        'var1': str,
        'var2': str,
        'var3': str,
        'var4': str,
        'var5': str,
        'var6': str,
        'var7': str,
        'var8': str,
        'var9': str
    }
    standard_include_path = os.path.join(os.path.dirname(states.__file__),
                                         'include')

    def run(self):
        ### Copy from include directive docutils 
        """Include a file as part of the content of this reST file."""
        rel_filename, filename = self.env.relfn2path(self.arguments[0])
        self.arguments[0] = filename
        self.env.note_included(filename)
        if not self.state.document.settings.file_insertion_enabled:
            raise self.warning('"%s" directive disabled.' % self.name)
        source = self.state_machine.input_lines.source(
            self.lineno - self.state_machine.input_offset - 1)
        source_dir = os.path.dirname(os.path.abspath(source))
        path = directives.path(self.arguments[0])
        if path.startswith('<') and path.endswith('>'):
            path = os.path.join(self.standard_include_path, path[1:-1])
        path = os.path.normpath(os.path.join(source_dir, path))
        path = utils.relative_path(None, path)
        path = nodes.reprunicode(path)
        encoding = self.options.get(
            'encoding', self.state.document.settings.input_encoding)
        e_handler=self.state.document.settings.input_encoding_error_handler
        tab_width = self.options.get(
            'tab-width', self.state.document.settings.tab_width)
        try:
            self.state.document.settings.record_dependencies.add(path)
            include_file = io.FileInput(source_path=path,
                                        encoding=encoding,
                                        error_handler=e_handler)
        except UnicodeEncodeError:
            raise self.severe(u'Problems with "%s" directive path:\n'
                              'Cannot encode input file path "%s" '
                              '(wrong locale?).' %
                              (self.name, SafeString(path)))
        except IOError as error:
            raise self.severe(u'Problems with "%s" directive path:\n%s.' %
                      (self.name, error))
        startline = self.options.get('start-line', None)
        endline = self.options.get('end-line', None)
        try:
            if startline or (endline is not None):
                lines = include_file.readlines()
                rawtext = ''.join(lines[startline:endline])
            else:
                rawtext = include_file.read()
        except UnicodeError:
            raise self.severe(u'Problem with "%s" directive:\n%s' %
                              (self.name, ErrorString(error)))
        # start-after/end-before: no restrictions on newlines in match-text,
        # and no restrictions on matching inside lines vs. line boundaries
        after_text = self.options.get('start-after', None)
        if after_text:
            # skip content in rawtext before *and incl.* a matching text
            after_index = rawtext.find(after_text)
            if after_index < 0:
                raise self.severe('Problem with "start-after" option of "%s" '
                                  'directive:\nText not found.' % self.name)
            rawtext = rawtext[after_index + len(after_text):]
        before_text = self.options.get('end-before', None)
        if before_text:
            # skip content in rawtext after *and incl.* a matching text
            before_index = rawtext.find(before_text)
            if before_index < 0:
                raise self.severe('Problem with "end-before" option of "%s" '
                                  'directive:\nText not found.' % self.name)
            rawtext = rawtext[:before_index]

        include_lines = statemachine.string2lines(rawtext, tab_width,
                                                  convert_whitespace=True)
        if 'literal' in self.options:
            # Convert tabs to spaces, if `tab_width` is positive.
            if tab_width >= 0:
                text = rawtext.expandtabs(tab_width)
            else:
                text = rawtext
            literal_block = nodes.literal_block(rawtext, source=path,
                                    classes=self.options.get('class', []))
            literal_block.line = 1
            self.add_name(literal_block)
            if 'number-lines' in self.options:
                try:
                    startline = int(self.options['number-lines'] or 1)
                except ValueError:
                    raise self.error(':number-lines: with non-integer '
                                     'start value')
                endline = startline + len(include_lines)
                if text.endswith('\n'):
                    text = text[:-1]
                tokens = NumberLines([([], text)], startline, endline)
                for classes, value in tokens:
                    if classes:
                        literal_block += nodes.inline(value, value,
                                                      classes=classes)
                    else:
                        literal_block += nodes.Text(value, value)
            else:
                literal_block += nodes.Text(text, text)
            return [literal_block]
        if 'code' in self.options:
            self.options['source'] = path
            codeblock = CodeBlock(self.name,
                                  [self.options.pop('code')], # arguments
                                  self.options,
                                  include_lines, # content
                                  self.lineno,
                                  self.content_offset,
                                  self.block_text,
                                  self.state,
                                  self.state_machine)
            return codeblock.run()
        
        new_include_lines = []
        for line in include_lines:
            for i in range(10):
                value = self.options.get(f'var{i}','')
                if value == '':
                    line = re.sub('\s?{{\s?var' + str(i) + '\s?}}',value,line)
                else:
                    line = re.sub('{{\s?var' + str(i) + '\s?}}',value,line)
            new_include_lines.append(line)
        self.state_machine.insert_input(new_include_lines, path)
        return []


class CfgcmdlistDirective(Directive):
    has_content = False
    required_arguments = 0
    option_spec = {
        'show-coverage': directives.flag
    }

    def run(self):
        cfglist = CfgcmdList()
        cfglist['coverage'] = False
        if 'show-coverage' in self.options:
            cfglist['coverage'] = True
        return [cfglist]


class OpcmdlistDirective(Directive):
    has_content = False
    required_arguments = 0
    option_spec = {
        'show-coverage': directives.flag
    }

    def run(self):
        oplist = OpcmdList()
        oplist['coverage'] = False
        if 'show-coverage' in self.options:
            oplist['coverage'] = True
            
        return [oplist]



class CmdDirective(SphinxDirective):

    has_content = True
    custom_class = ''

    def run(self):        

        title_list = []
        content_list = []
        title_text = ''
        content_text = ''
        has_body = False

        cfgmode = self.custom_class + "cmd"

        if '' in self.content:
            index = self.content.index('')
            title_list = self.content[0:index]
            content_list = self.content[index + 1:]
            title_text = ' '.join(title_list)
            content_text = '\n'.join(content_list)
            has_body = True
        else:
            title_text = ' '.join(self.content)

        anchor_id = nodes.make_id(self.custom_class + "cmd-" + title_text)
        target = nodes.target(ids=[anchor_id])

        panel_name = 'cmd-{}'.format(self.custom_class)
        panel_element = CmdDiv()
        panel_element['classes'] += ['cmd', panel_name]

        heading_element = CmdHeader(title_text)
        title_nodes, messages = self.state.inline_text(title_text,
                                                       self.lineno)

        title = inlinecmd(title_text, '', *title_nodes)
        target['classes'] += []
        title['classes'] += [cfgmode]
        heading_element.append(target)
        heading_element.append(title)

        heading_element['classes'] += [self.custom_class + 'cmd-heading']

        panel_element.append(heading_element)

        append_list = {
            'docname': self.env.docname,
            'cmdnode': title.deepcopy(),
            'cmd': title_text,
            'target': target,
        }

        if cfgmode == 'opcmd':
            if not hasattr(self.env, "vyos_opcmd"):
                self.env.vyos_opcmd = []
            self.env.vyos_opcmd.append(append_list)

        if cfgmode == 'cfgcmd':
            if not hasattr(self.env, "vyos_cfgcmd"):
                self.env.vyos_cfgcmd = []
            self.env.vyos_cfgcmd.append(append_list)

        if has_body:
            body_element = CmdBody(content_text)
            self.state.nested_parse(
                content_list,
                self.content_offset,
                body_element
            )

            body_element['classes'] += [self.custom_class + 'cmd-body']
            panel_element.append(body_element)
        return [panel_element]


class OpCmdDirective(CmdDirective):
    custom_class = 'op'


class CfgCmdDirective(CmdDirective):
    custom_class = 'cfg'


def strip_cmd(cmd, debug=False):
    if debug:
        print("")
        print(cmd)
    cmd = re.sub('set','',cmd)
    if debug:
        print(cmd)
    #while " | " in cmd:
    cmd = re.sub('\s+\|\s+','',cmd)
    if debug:
        print(cmd)
    cmd = re.sub('<\S*>','',cmd)
    if debug:
        print(cmd)
    cmd = re.sub('\[\S\]','',cmd)
    if debug:
        print(cmd)
    cmd = re.sub('\s+','',cmd)
    if debug:
        print(cmd)
        print("")
    return cmd

def build_row(app, fromdocname, rowdata):   
    row = nodes.row()
    for cell in rowdata:
        entry = nodes.entry()
        row += entry
        if isinstance(cell, list):
            for item in cell:
                if isinstance(item, dict):
                    entry += process_cmd_node(app, item, fromdocname, '')
                else:
                    entry += nodes.paragraph(text=item)
        elif isinstance(cell, bool):
            if cell:
                entry += nodes.paragraph(text="")
                entry['classes'] = ['coverage-ok']
            else:
                entry += nodes.paragraph(text="")
                entry['classes'] = ['coverage-fail']
        else:
            entry += nodes.paragraph(text=cell)
    return row



def process_coverage(app, fromdocname, doccmd, xmlcmd, cli_type):
    coverage_list = {}
    int_docs = 0
    int_xml = 0
    for cmd in doccmd:
        coverage_item = {
            'doccmd': None,
            'xmlcmd': None,
            'doccmd_item': None,
            'xmlcmd_item': None,
            'indocs': False,
            'inxml': False,
            'xmlfilename': None
        }
        coverage_item['doccmd'] = cmd['cmd']
        coverage_item['doccmd_item'] = cmd
        coverage_item['indocs'] = True
        int_docs += 1

        coverage_list[strip_cmd(cmd['cmd'])] = dict(coverage_item)

    
    #print(coverage_list.keys())
    
    for cmd in xmlcmd:
        
        strip = strip_cmd(cmd['cmd'])
        if strip not in coverage_list.keys():
            coverage_item = {
                'doccmd': None,
                'xmlcmd': None,
                'doccmd_item': None,
                'xmlcmd_item': None,
                'indocs': False,
                'inxml': False,
                'xmlfilename': None
            }
            coverage_item['xmlcmd'] = cmd['cmd']
            coverage_item['xmlcmd_item'] = cmd
            coverage_item['inxml'] = True
            coverage_item['xmlfilename'] = cmd['filename']
            int_xml += 1
            coverage_list[strip] = dict(coverage_item)
        else:
            coverage_list[strip]['xmlcmd'] = cmd['cmd']
            coverage_list[strip]['xmlcmd_item'] = cmd
            coverage_list[strip]['inxml'] = True
            coverage_list[strip]['xmlfilename'] = cmd['filename']
            int_xml += 1


    

    table = nodes.table()
    tgroup = nodes.tgroup(cols=3)
    table += tgroup

    header = (f'{int_docs}/{len(coverage_list)} in Docs', f'{int_xml}/{len(coverage_list)} in XML', 'Command')
    colwidths = (1, 1, 8)
    table = nodes.table()
    tgroup = nodes.tgroup(cols=len(header))
    table += tgroup
    for colwidth in colwidths:
        tgroup += nodes.colspec(colwidth=colwidth)
    thead = nodes.thead()
    tgroup += thead
    thead += build_row(app, fromdocname, header)
    tbody = nodes.tbody()
    tgroup += tbody
    for entry in sorted(coverage_list):
        body_text_list = []
        if coverage_list[entry]['indocs']:
            body_text_list.append(coverage_list[entry]['doccmd_item'])
        else:
            body_text_list.append('Not documented yet')

        if coverage_list[entry]['inxml']:
            body_text_list.append("------------------")
            body_text_list.append(str(coverage_list[entry]['xmlfilename']) + ":")
            body_text_list.append(coverage_list[entry]['xmlcmd'])
        else:
            body_text_list.append('Nothing found in XML Definitions')

            
        tbody += build_row(app, fromdocname, 
            (
                coverage_list[entry]['indocs'],
                coverage_list[entry]['inxml'],
                body_text_list
            )
        )

    return table

def process_cmd_node(app, cmd, fromdocname, cli_type):
    para = nodes.paragraph()
    newnode = nodes.reference('', '')
    innernode = cmd['cmdnode']
    newnode['refdocname'] = cmd['docname']
    newnode['refuri'] = app.builder.get_relative_uri(
        fromdocname, cmd['docname'])
    newnode['refuri'] += '#' + cmd['target']['refid']
    newnode['classes'] += ['cmdlink']
    newnode.append(innernode)
    para += newnode
    return para


def process_cmd_nodes(app, doctree, fromdocname):
    try:
        env = app.builder.env
        
        for node in doctree.traverse(CfgcmdList):
            content = []
            if node.attributes['coverage']:
                node.replace_self(
                    process_coverage(
                        app,
                        fromdocname,
                        env.vyos_cfgcmd,
                        app.config.vyos_working_commands['cfgcmd'],
                        'cfgcmd'
                        )
                    )
            else:
                for cmd in sorted(env.vyos_cfgcmd, key=lambda i: i['cmd']):
                    content.append(process_cmd_node(app, cmd, fromdocname, 'cfgcmd'))                
                node.replace_self(content)
            
        for node in doctree.traverse(OpcmdList):
            content = []
            if node.attributes['coverage']:
                node.replace_self(
                    process_coverage(
                        app,
                        fromdocname,
                        env.vyos_opcmd,
                        app.config.vyos_working_commands['opcmd'],
                        'opcmd'
                        )
                    )
            else:
                for cmd in sorted(env.vyos_opcmd, key=lambda i: i['cmd']):
                    content.append(process_cmd_node(app, cmd, fromdocname, 'opcmd'))
                node.replace_self(content)

    except Exception as inst:
        print(inst)


def vytask_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    app = inliner.document.settings.env.app
    base = app.config.vyos_phabricator_url
    ref = base + str(text)
    set_classes(options)
    node = nodes.reference(
        rawtext, utils.unescape(str(text)), refuri=ref, **options)
    return [node], []


def cmd_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    node = nodes.literal(text, text)
    return [node], []