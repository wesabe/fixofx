import sys
from wsgi_intercept import WSGI_HTTPConnection

import urllib2, httplib
from urllib2 import HTTPHandler, HTTPSHandler
from httplib import HTTP

#
# ugh, version dependence.
#

if sys.version_info[:2] == (2, 3):
    class WSGI_HTTP(HTTP):
        _connection_class = WSGI_HTTPConnection

    class WSGI_HTTPHandler(HTTPHandler):
        """
        Override the default HTTPHandler class with one that uses the
        WSGI_HTTPConnection class to open HTTP URLs.
        """
        def http_open(self, req):
            return self.do_open(WSGI_HTTP, req)
    
    # I'm not implementing HTTPS for 2.3 until someone complains about it! -Kumar
    WSGI_HTTPSHandler = None
    
else:
    class WSGI_HTTPHandler(HTTPHandler):
        """
        Override the default HTTPHandler class with one that uses the
        WSGI_HTTPConnection class to open HTTP URLs.
        """
        def http_open(self, req):
            return self.do_open(WSGI_HTTPConnection, req)
    
    if hasattr(httplib, 'HTTPS'):
        # urllib2 does this check as well, I assume it's to see if 
        # python was compiled with SSL support
        class WSGI_HTTPSHandler(HTTPSHandler):
            """
            Override the default HTTPSHandler class with one that uses the
            WSGI_HTTPConnection class to open HTTPS URLs.
            """
            def https_open(self, req):
                return self.do_open(WSGI_HTTPConnection, req)
    else:
        WSGI_HTTPSHandler = None
    
def install_opener():
    handlers = [WSGI_HTTPHandler()]
    if WSGI_HTTPSHandler is not None:
        handlers.append(WSGI_HTTPSHandler())
    opener = urllib2.build_opener(*handlers)
    urllib2.install_opener(opener)

    return opener

def uninstall_opener():
    urllib2.install_opener(None)
