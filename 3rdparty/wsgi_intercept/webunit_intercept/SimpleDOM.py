#
# Copyright (c) 2003 Richard Jones (http://mechanicalcat.net/richard)
# Copyright (c) 2002 ekit.com Inc (http://www.ekit-inc.com/)
# Copyright (c) 2001 Bizar Software Pty Ltd (http://www.bizarsoftware.com.au/)
#
# See the README for full license details.
#
# HISTORY:
# This code is heavily based on the TAL parsing code from the Zope Page
# Templates effort at www.zope.org. No copyright or license accompanied
# that code.
# 
# $Id: SimpleDOM.py,v 1.6 2004/01/21 22:50:09 richard Exp $

'''A Simple DOM parser

Simple usage:
>>> import SimpleDOM
>>> parser = SimpleDOM.SimpleDOMParser()
>>> parser.parseString("""<html><head><title>My Document</title></head>
... <body>
...  <p>This is a paragraph!!!</p>
...  <p>This is another para!!</p>
... </body>
... </html>""")
>>> dom = parser.getDOM()
>>> dom.getByName('p')
[<SimpleDOMNode "p" {} (1 elements)>, <SimpleDOMNode "p" {} (1 elements)>]
>>> dom.getByName('p')[0][0]
'This is a paragraph!!!'
>>> dom.getByName('title')[0][0]
'My Document'
'''

import sys, string

# NOTE this is using a modified HTMLParser
from HTMLParser import HTMLParser, HTMLParseError
from utility import Upload

BOOLEAN_HTML_ATTRS = [
    # List of Boolean attributes in HTML that may be given in
    # minimized form (e.g. <img ismap> rather than <img ismap="">)
    # From http://www.w3.org/TR/xhtml1/#guidelines (C.10)
    "compact", "nowrap", "ismap", "declare", "noshade", "checked",
    "disabled", "readonly", "multiple", "selected", "noresize",
    "defer"
    ]

EMPTY_HTML_TAGS = [
    # List of HTML tags with an empty content model; these are
    # rendered in minimized form, e.g. <img />.
    # From http://www.w3.org/TR/xhtml1/#dtds
    "base", "meta", "link", "hr", "br", "param", "img", "area",
    "input", "col", "basefont", "isindex", "frame",
    ]

PARA_LEVEL_HTML_TAGS = [
    # List of HTML elements that close open paragraph-level elements
    # and are themselves paragraph-level.
    "h1", "h2", "h3", "h4", "h5", "h6", "p",
    ]

BLOCK_CLOSING_TAG_MAP = {
    "tr": ("tr", "td", "th"),
    "td": ("td", "th"),
    "th": ("td", "th"),
    "li": ("li",),
    "dd": ("dd", "dt"),
    "dt": ("dd", "dt"),
    "option": ("option",),
    }

BLOCK_LEVEL_HTML_TAGS = [
    # List of HTML tags that denote larger sections than paragraphs.
    "blockquote", "table", "tr", "th", "td", "thead", "tfoot", "tbody",
    "noframe", "div", "form", "font", "p",
    "ul", "ol", "li", "dl", "dt", "dd",
    ]


class NestingError(HTMLParseError):
    """Exception raised when elements aren't properly nested."""

    def __init__(self, tagstack, endtag, position=(None, None)):
        self.endtag = endtag
        if tagstack:
            if len(tagstack) == 1:
                msg = ('Open tag <%s> does not match close tag </%s>'
                       % (tagstack[0], endtag))
            else:
                msg = ('Open tags <%s> do not match close tag </%s>'
                       % (string.join(tagstack, '>, <'), endtag))
        else:
            msg = 'No tags are open to match </%s>' % endtag
        HTMLParseError.__init__(self, msg, position)

class EmptyTagError(NestingError):
    """Exception raised when empty elements have an end tag."""

    def __init__(self, tag, position=(None, None)):
        self.tag = tag
        msg = 'Close tag </%s> should be removed' % tag
        HTMLParseError.__init__(self, msg, position)

_marker=[]
class SimpleDOMNode:
    '''Simple class that represents a tag in a HTML document. The node may
       have contents which are represented as a sequence of tags or strings
       of text.

       node.name  -- get the "name" attribute
       node[N]    -- get the Nth entry in the contents list
       len(node)  -- number of sub-content objects
    '''
    def __init__(self, name, attributes, contents):
        self.__dict__['__name'] = name
        self.__dict__['__attributes'] = attributes
        self.__dict__['__contents'] = contents

    def getByName(self, name, r=None):
        '''Return all nodes of type "name" from the contents of this DOM
           using a depth-first search.
        '''
        if r is None:
            r = []
        for entry in self.getContents():
            if isinstance(entry, SimpleDOMNode):
                if entry.__dict__['__name'] == name:
                    r.append(entry)
                entry.getByName(name, r)
        return r

    def getById(self, name, id):
        '''Return all nodes of type "name" from the contents of this DOM
           using a depth-first search.
        '''
        l = self.getByName(name)
        for entry in l:
            if hasattr(entry, 'id') and entry.id == id:
                return entry
        raise ValueError, 'No %r with id %r'%(name, id)

    def getByNameFlat(self, name):
        '''Return all nodes of type "name" from the contents of this node.
           NON-RECURSIVE.
        '''
        r = []
        for entry in self.getContents():
            if isinstance(entry, SimpleDOMNode):
                if entry.__dict__['__name'] == name:
                    r.append(entry)
        return r

    def getPath(self, path):
        '''Return all nodes of type "name" from the contents of this node.
           NON-RECURSIVE.
        '''
        current = self
        for name, count in path:
            for entry in current.getContents():
                if isinstance(entry, SimpleDOMNode) and \
                        entry.__dict__['__name'] == name:
                    if not count:
                        current = entry
                        break
                    count -= 1
        return current

    def hasChildNodes(self):
        '''Determine if the Node has any content nodes (rather than just text).
        '''
        for entry in self.getContents():
            if isinstance(entry, SimpleDOMNode):
                return 1
        return 0

    def getContents(self):
        return self.__dict__['__contents']

    def __getitem__(self, item):
        return self.getContents()[item]

    def hasattr(self, attr):
        return self.__dict__['__attributes'].has_key(attr)

    def getattr(self, attr, default=_marker):
        if self.__dict__['__attributes'].has_key(attr):
            return self.__dict__['__attributes'][attr]
        if default is _marker:
            raise AttributeError, attr
        return default

    def __getattr__(self, attr):
        if self.__dict__['__attributes'].has_key(attr):
            return self.__dict__['__attributes'][attr]
        if self.__dict__.has_key(attr):
            return self.__dict__[attr]
        raise AttributeError, attr
    
    def __len__(self):
        return len(self.getContents())

    def getContentString(self):
        s = ''
        for content in self.getContents():
            s = s + str(content)
        return s

    def __str__(self):
        attrs = []
        for attr in self.__dict__['__attributes'].items():
            if attr[0] in BOOLEAN_HTML_ATTRS:
                attrs.append(attr[0])
            else:
                attrs.append('%s="%s"'%attr)
        if attrs:
            s = '<%s %s>'%(self.__dict__['__name'], ' '.join(attrs))
        else:
            s = '<%s>'%self.__dict__['__name']
        s = s + self.getContentString()
        if self.__dict__['__name'] in EMPTY_HTML_TAGS:
            return s
        else:
            return s + '</%s>'%self.__dict__['__name']

    def __repr__(self):
        return '<SimpleDOMNode "%s" %s (%s elements)>'%(self.__dict__['__name'],
            self.__dict__['__attributes'], len(self.getContents()))

    def extractElements(self, path=[], include_submit=0, include_button=0):
        ''' Pull a form's elements out of the document given the path to the
            form.

            For most elements, the returned dictionary has a key:value pair
            holding the input elements name and value.

            For radio, checkboxes and selects, the value is a dictionary
            holding:

              value or name: 'selected'    (note: not 'checked')

            where the value of the input/option is used but if not
            present then the name is used.
        '''
        form = self
        for name, element in path:
            form = form.getByName(name)[element]
        elements = {}
        submits = 0
        buttons = 0
        for input in form.getByName('input'):
            if not hasattr(input, 'type'):
                elements[input.name] = input.getattr('value', '')
            elif input.type == 'image':
                continue
            elif input.type == 'button' and not include_button:
                continue
            elif input.type == 'submit' and not include_submit:
                continue
            elif input.type == 'file':
                elements[input.name] = Upload('')
            elif input.type in ['checkbox', 'radio']:
                l = elements.setdefault(input.name, {})
                key = input.hasattr('value') and input.value or input.name
                if input.hasattr('checked'):
                    l[key] = 'selected'
                else:
                    l[key] = ''
            elif input.type == 'submit':
                name = input.getattr('name', 'submit')
                if name == 'submit':
                    name = 'submit%s'%str(submits)
                    submits = submits + 1
                elements[name] = input.getattr('value', '')
            elif input.type == 'button':
                name = input.getattr('name', 'button')
                if name == 'button':
                    name = 'button%s'%str(buttons)
                    buttons = buttons + 1
                elements[name] = input.getattr('value', '')
            else:
                elements[input.name] = input.getattr('value', '')
        for textarea in form.getByName('textarea'):
            if len(textarea):
                elements[textarea.name] = textarea.getContentString()
            else:
                elements[textarea.name] = ''
        for input in form.getByName('select'):
            options = input.getByName('option')
            d = elements[input.name] = {}
            selected = first = None
            for option in options:
                if option.hasattr('value'):
                    key = option.value
                elif len(option) > 0:
                    key = option[0]
                else:
                    continue
                if first is None:
                    first = key
                if option.hasattr('selected'):
                    d[key] = 'selected'
                    selected = 1
                else: d[key] = ''
            if ((not input.hasattr('size') or input.size == 1)
                    and selected is None and first is not None):
                d[first] = 'selected'

        return elements

class SimpleDOMParser(HTMLParser):
    def __init__(self, debug=0):
        HTMLParser.__init__(self)
        self.tagstack = []
        self.__debug = debug

        #  DOM stuff
        self.content = self.dom = []
        self.stack = []

    def parseFile(self, file):
        f = open(file)
        data = f.read()
        f.close()
        self.parseString(data)

    def parseString(self, data):
        self.feed(data)
        self.close()
        while self.tagstack:
            self.implied_endtag(self.tagstack[-1], 2)

    def getDOM(self):
        return SimpleDOMNode('The Document', {}, self.dom)

    # Overriding HTMLParser methods

    def handle_starttag(self, tag, attrs):
        if self.__debug:
            print '\n>handle_starttag', tag
            print self.tagstack
        self.close_para_tags(tag)
        self.tagstack.append(tag)
        d = {}
        for k, v in attrs:
            d[string.lower(k)] = v
        self.emitStartElement(tag, d)
        if tag in EMPTY_HTML_TAGS:
            self.implied_endtag(tag, -1)

    def handle_startendtag(self, tag, attrs):
        if self.__debug:
            print '><handle_startendtag', tag
            print self.tagstack
        self.close_para_tags(tag)
        d = {}
        for k, v in attrs:
            d[string.lower(k)] = v
        self.emitStartElement(tag, d, isend=1)

    def handle_endtag(self, tag):
        if self.__debug:
            print '<handle_endtag', tag
            print self.tagstack
        if tag in EMPTY_HTML_TAGS:
            # </img> etc. in the source is an error
            raise EmptyTagError(tag, self.getpos())
        self.close_enclosed_tags(tag)
        self.emitEndElement(tag)
        self.tagstack.pop()

    def close_para_tags(self, tag):
        if tag in EMPTY_HTML_TAGS:
            return
        close_to = -1
        if BLOCK_CLOSING_TAG_MAP.has_key(tag):
            blocks_to_close = BLOCK_CLOSING_TAG_MAP[tag]
            for i in range(len(self.tagstack)):
                t = self.tagstack[i]
                if t in blocks_to_close:
                    if close_to == -1:
                        close_to = i
                elif t in BLOCK_LEVEL_HTML_TAGS:
                    close_to = -1
        elif tag in PARA_LEVEL_HTML_TAGS + BLOCK_LEVEL_HTML_TAGS:
            for i in range(len(self.tagstack)):
                if self.tagstack[i] in BLOCK_LEVEL_HTML_TAGS:
                    close_to = -1
                elif self.tagstack[i] in PARA_LEVEL_HTML_TAGS:
                    if close_to == -1:
                        close_to = i
        if close_to >= 0:
            while len(self.tagstack) > close_to:
                self.implied_endtag(self.tagstack[-1], 1)

    def close_enclosed_tags(self, tag):
        if tag not in self.tagstack:
            raise NestingError(self.tagstack, tag, self.getpos())
        while tag != self.tagstack[-1]:
            self.implied_endtag(self.tagstack[-1], 1)
        assert self.tagstack[-1] == tag

    def implied_endtag(self, tag, implied):
        if self.__debug:
            print '<implied_endtag', tag, implied
            print self.tagstack
        assert tag == self.tagstack[-1]
        assert implied in (-1, 1, 2)
        isend = (implied < 0)
        self.emitEndElement(tag, isend=isend, implied=implied)
        self.tagstack.pop()

    def handle_charref(self, name):
        self.emitText("&#%s;" % name)

    def handle_entityref(self, name):
        self.emitText("&%s;" % name)

    def handle_data(self, data):
        self.emitText(data)

    def handle_comment(self, data):
        self.emitText("<!--%s-->" % data)

    def handle_decl(self, data):
        self.emitText("<!%s>" % data)

    def handle_pi(self, data):
        self.emitText("<?%s>" % data)

    def emitStartTag(self, name, attrlist, isend=0):
        if isend:
            if self.__debug: print '*** content'
            self.content.append(SimpleDOMNode(name, attrlist, []))
        else:
            # generate a new scope and push the current one on the stack
            if self.__debug: print '*** push'
            newcontent = []
            self.stack.append(self.content)
            self.content.append(SimpleDOMNode(name, attrlist, newcontent))
            self.content = newcontent

    def emitEndTag(self, name):
        if self.__debug: print '*** pop'
        self.content = self.stack.pop()

    def emitText(self, text):
        self.content.append(text)

    def emitStartElement(self, name, attrlist, isend=0):
        # Handle the simple, common case
        self.emitStartTag(name, attrlist, isend)
        if isend:
            self.emitEndElement(name, isend)

    def emitEndElement(self, name, isend=0, implied=0):
        if not isend or implied:
            self.emitEndTag(name)


if __name__ == '__main__':
    tester = SimpleDOMParser(debug=0)
    tester.parseFile('/tmp/test.html')
    dom = tester.getDOM()
#    html = dom.getByNameFlat('html')[0]
#    body = html.getByNameFlat('body')[0]
#    table = body.getByNameFlat('table')[0]
#    tr = table.getByNameFlat('tr')[1]
#    td = tr.getByNameFlat('td')[2]
#    print td
    import pprint;pprint.pprint(dom)

