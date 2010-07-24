
from distutils.cmd import Command
from distutils.errors import *
from distutils import log
from docutils import statemachine
from docutils.parsers.rst import directives
from docutils.core import (
    publish_file, publish_string, publish_doctree, publish_from_doctree)
from docutils.parsers import rst
from docutils.nodes import SparseNodeVisitor
from docutils.readers.standalone import Reader
from docutils.writers.html4css1 import HTMLTranslator, Writer
from docutils import nodes
import compiler
from compiler import visitor
from pprint import pprint
import pydoc, os, shutil

class DocInspector(object):
    """expose docstrings for objects by parsing the abstract syntax tree.
    
    splitdocfor() is the interface around this
    """
    def __init__(self, filename):
        self.filename = filename
        self.top_level_doc = None
        self.map = {}
    
    def __getitem__(self, path):
        return self.map[path]
    
    def __contains__(self, path):
        return path in self.map
    
    def makepath(self, node):
        path = [n.name for n in node.lineage] + [node.name]
        # skip first name in lineage because that's the file ...
        return ".".join(path[1:])
        
    def default(self, node):
        for child in node.getChildNodes():
            self.visit(child, node.lineage + [node])
            
    def visitModule(self, node):
        self.top_level_doc = node.doc
        node.name = self.filename
        node.lineage = []
        # descend into classes and functions
        self.default(node)
        
    def visitClass(self, node, lineage=[]):
        node.lineage = lineage
        self.map[self.makepath(node)] = node.doc
        self.default(node) 
        
    def visitFunction(self, node, lineage=[]):
        node.lineage = lineage
        self.map[self.makepath(node)] = node.doc
        self.default(node) 

def splitdocfor(path):
    """split the docstring for a path
    
    valid paths are::
        
        ./path/to/module.py
        ./path/to/module.py:SomeClass.method
    
    returns (description, long_description) from the docstring for path 
    or (None, None) if there isn't a docstring.
    
    Example::
    
        >>> splitdocfor("./wsgi_intercept/__init__.py")[0]
        'installs a WSGI application in place of a real URI for testing.'
        >>> splitdocfor("./wsgi_intercept/__init__.py:WSGI_HTTPConnection.get_app")[0]
        'Return the app object for the given (host, port).'
        >>> 
        
    """
    if ":" in path:
        filename, objpath = path.split(':')
    else:
        filename, objpath = path, None
    inspector = DocInspector(filename)
    visitor.walk(compiler.parseFile(filename), inspector)
    if objpath is None:
        if inspector.top_level_doc is None:
            return None, None
        return pydoc.splitdoc(inspector.top_level_doc)
    else:
        if inspector[objpath] is None:
            return None, None
        return pydoc.splitdoc(inspector[objpath])

def include_docstring(  
        name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
    """include reStructuredText from a docstring.  use the directive like:
        
        | .. include_docstring:: path/to/module.py
        | .. include_docstring:: path/to/module.py:SomeClass
        | .. include_docstring:: path/to/module.py:SomeClass.method
    
    """
    rawpath = arguments[0]
    summary, body = splitdocfor(rawpath)
    # nabbed from docutils.parsers.rst.directives.misc.include
    include_lines = statemachine.string2lines(body, convert_whitespace=1)
    state_machine.insert_input(include_lines, None)
    return []
    # return [publish_doctree(body)]

include_docstring.arguments = (1, 0, 0)
include_docstring.options = {}
include_docstring.content = 0

directives.register_directive('include_docstring', include_docstring)

class build_docs(Command):
    description = "build documentation for wsgi_intercept"
    user_options = [
        # ('optname=', None, ""),
    ]
    def initialize_options(self):
        pass
        
    def finalize_options(self):
        pass
        
    def run(self):
        """build end-user documentation."""
        if not os.path.exists('./build'):
            os.mkdir('./build')
            log.info("created build dir")
        if os.path.exists('./build/docs'):
            shutil.rmtree('./build/docs')
        os.mkdir("./build/docs")
        body = publish_file(open("./docs/index.rst", 'r'),
                    destination=open("./build/docs/index.html", 'w'),
                    writer_name='html',
                    # settings_overrides={'halt_level':2,
                    #                     'report_level':5}
                    )
        log.info("published docs to: ./build/docs/index.html")
        