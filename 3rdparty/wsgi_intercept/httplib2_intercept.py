
"""intercept HTTP connections that use httplib2

(see wsgi_intercept/__init__.py for examples)

"""

import httplib2
import wsgi_intercept
from httplib2 import HTTPConnectionWithTimeout, HTTPSConnectionWithTimeout
import sys

InterceptorMixin = wsgi_intercept.WSGI_HTTPConnection

# might make more sense as a decorator

def connect(self):
    """
    Override the connect() function to intercept calls to certain
    host/ports.
    """
    if wsgi_intercept.debuglevel:
        sys.stderr.write('connect: %s, %s\n' % (self.host, self.port,))

    (app, script_name) = self.get_app(self.host, self.port)
    if app:
        if wsgi_intercept.debuglevel:
            sys.stderr.write('INTERCEPTING call to %s:%s\n' % \
                             (self.host, self.port,))
        self.sock = wsgi_intercept.wsgi_fake_socket(app,
                                                    self.host, self.port,
                                                    script_name)
    else:
        self._connect()

class HTTP_WSGIInterceptorWithTimeout(HTTPConnectionWithTimeout, InterceptorMixin):
    _connect = httplib2.HTTPConnectionWithTimeout.connect
    connect = connect

class HTTPS_WSGIInterceptorWithTimeout(HTTPSConnectionWithTimeout, InterceptorMixin):
    _connect = httplib2.HTTPSConnectionWithTimeout.connect
    connect = connect

def install():
    httplib2.HTTPConnectionWithTimeout = HTTP_WSGIInterceptorWithTimeout
    httplib2.HTTPSConnectionWithTimeout = HTTPS_WSGIInterceptorWithTimeout

def uninstall():
    httplib2.HTTPConnectionWithTimeout = HTTPConnectionWithTimeout
    httplib2.HTTPSConnectionWithTimeout = HTTPSConnectionWithTimeout
