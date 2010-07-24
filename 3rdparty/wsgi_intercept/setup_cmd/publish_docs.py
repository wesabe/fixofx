
import re, pydoc
from distutils.cmd import Command
from distutils.errors import *
from distutils import log
from docutils.core import publish_string, publish_parts
from docutils import nodes
from docutils.nodes import SparseNodeVisitor
from docutils.writers import Writer
import wsgi_intercept
from mechanize import Browser
wiki_word_re = re.compile(r'^[A-Z][a-z]+(?:[A-Z][a-z]+)+')
    
class WikiWriter(Writer):
    def translate(self):
        visitor = WikiVisitor(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()
        
class WikiVisitor(SparseNodeVisitor):
    """visits RST nodes and transforms into Moin Moin wiki syntax.
    
    swiped from the nose project, originally written by Jason Pellerin.
    """
    def __init__(self, document):
        SparseNodeVisitor.__init__(self, document)
        self.list_depth = 0
        self.list_item_prefix = None
        self.indent = self.old_indent = ''
        self.output = []
        self.preformat = False
        self.section_level = 0
        
    def astext(self):
        return ''.join(self.output)

    def visit_Text(self, node):
        #print "Text", node
        data = node.astext()
        if not self.preformat:
            data = data.lstrip('\n\r')
            data = data.replace('\r', '')
            data = data.replace('\n', ' ')
        self.output.append(data)
    
    def visit_bullet_list(self, node):
        self.list_depth += 1
        self.list_item_prefix = (' ' * self.list_depth) + '* '

    def depart_bullet_list(self, node):
        self.list_depth -= 1
        if self.list_depth == 0:
            self.list_item_prefix = None
        else:
            self.list_item_prefix = (' ' * self.list_depth) + '* '
        self.output.append('\n\n')
                           
    def visit_list_item(self, node):
        self.old_indent = self.indent
        self.indent = self.list_item_prefix

    def depart_list_item(self, node):
        self.indent = self.old_indent
        
    def visit_literal_block(self, node):
        self.output.extend(['{{{', '\n'])
        self.preformat = True

    def depart_literal_block(self, node):
        self.output.extend(['\n', '}}}', '\n\n'])
        self.preformat = False

    def visit_doctest_block(self, node):
        self.output.extend(['{{{', '\n'])
        self.preformat = True

    def depart_doctest_block(self, node):
        self.output.extend(['\n', '}}}', '\n\n'])
        self.preformat = False
        
    def visit_paragraph(self, node):
        self.output.append(self.indent)
        
    def depart_paragraph(self, node):
        self.output.append('\n')
        if not isinstance(node.parent, nodes.list_item):
            self.output.append('\n')
        if self.indent == self.list_item_prefix:
            # we're in a sub paragraph of a list item
            self.indent = ' ' * self.list_depth
        
    def visit_reference(self, node):
        if node.has_key('refuri'):
            href = node['refuri']
        elif node.has_key('refid'):
            href = '#' + node['refid']
        else:
            href = None
        self.output.append('[' + href + ' ')

    def depart_reference(self, node):
        self.output.append(']')
    
    def _find_header_level(self, node):
        if isinstance(node.parent, nodes.topic):
            h_level = 2 # ??
        elif isinstance(node.parent, nodes.document):
            h_level = 1
        else:
            assert isinstance(node.parent, nodes.section), (
                "unexpected parent: %s" % node.parent.__class__)
            h_level = self.section_level
        return h_level
    
    def _depart_header_node(self, node):
        h_level = self._find_header_level(node)
        self.output.append(' %s\n\n' % ('='*h_level))
        self.list_depth = 0
        self.indent = ''
    
    def _visit_header_node(self, node):
        h_level = self._find_header_level(node)
        self.output.append('%s ' % ('='*h_level))

    def visit_subtitle(self, node):
        self._visit_header_node(node)

    def depart_subtitle(self, node):
        self._depart_header_node(node)
        
    def visit_title(self, node):
        self._visit_header_node(node)

    def depart_title(self, node):
        self._depart_header_node(node)
        
    def visit_title_reference(self, node):
        self.output.append("`")

    def depart_title_reference(self, node):
        self.output.append("`")

    def visit_section(self, node):
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1

    def visit_emphasis(self, node):
        self.output.append('*')

    def depart_emphasis(self, node):
        self.output.append('*')
        
    def visit_literal(self, node):
        self.output.append('`')
        
    def depart_literal(self, node):
        self.output.append('`')
        
class publish_docs(Command):
    description = "publish documentation to front page of Google Code project"
    user_options = [
        ('google-user=', None, "Google Code username"),
        ('google-password=', None, "Google Code password"),
    ]
    def initialize_options(self):
        self.google_user = None
        self.google_password = None
    def finalize_options(self):
        if self.google_user is None and self.google_password is None:
            raise DistutilsOptionError("--google-user and --google-password are required")
    def run(self):        
        summary, doc = pydoc.splitdoc(wsgi_intercept.__doc__)
        wikidoc = publish_string(doc, writer=WikiWriter())
        print wikidoc
        
        ## Google html is so broken that this isn't working :/
        
        # br = Browser()
        # br.open('http://code.google.com/p/wsgi-intercept/admin')
        # url = br.geturl()
        # assert url.startswith('https://www.google.com/accounts/Login'), (
        #     "unexpected URL: %s" % url)
        # log.info("logging in to Google Code...")
        # forms = [f for f in br.forms()]
        # assert len(forms)==1, "unexpected forms: %s for %s" % (forms, br.geturl())
        # br.select_form(nr=0)
        # br['Email'] = self.google_user
        # br['Passwd'] = self.google_password
        # admin = br.submit()
        # url = admin.geturl()
        # assert url=='http://code.google.com/p/wsgi-intercept/admin', (
        #     "unexpected URL: %s" % url) 
        # br.select_form(nr=0)
        # br['projectdescription'] = wikidoc
        # br.submit()
        # print br.geturl()
        
