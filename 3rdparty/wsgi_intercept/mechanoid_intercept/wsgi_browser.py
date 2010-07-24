"""
A mechanoid browser that redirects specified HTTP connections to a WSGI
object.
"""

from httplib import HTTP
import httplib
from mechanoid import Browser as MechanoidBrowser
from mechanoid.useragent.http_handlers.HTTPHandler import HTTPHandler
from mechanoid.useragent.http_handlers.HTTPSHandler import HTTPSHandler

import sys, os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from wsgi_intercept import WSGI_HTTPConnection

class WSGI_HTTP(HTTP):
    _connection_class = WSGI_HTTPConnection

class WSGI_HTTPHandler(HTTPHandler):
    def http_open(self, req):
        return self.do_open(WSGI_HTTP, req)

if hasattr(httplib, 'HTTPS'):
    class WSGI_HTTPSHandler(HTTPSHandler):
        def https_open(self, req):
            return self.do_open(WSGI_HTTP, req)
else:
    WSGI_HTTPSHandler = None

class Browser(MechanoidBrowser):
    def __init__(self, *args, **kwargs):
        self.handler_classes['http'] = WSGI_HTTPHandler
        if WSGI_HTTPSHandler is not None:
            self.handler_classes['https'] = WSGI_HTTPSHandler
        MechanoidBrowser.__init__(self, *args, **kwargs)
