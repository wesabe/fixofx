
from nose.tools import with_setup, raises
from urllib2 import URLError
from wsgi_intercept.zope_testbrowser.wsgi_testbrowser import WSGI_Browser
import wsgi_intercept
from wsgi_intercept import test_wsgi_app

_saved_debuglevel = None
    
def add_intercept(port=80):
    # _saved_debuglevel, wsgi_intercept.debuglevel = wsgi_intercept.debuglevel, 1
    wsgi_intercept.add_wsgi_intercept('some_hopefully_nonexistant_domain', port, test_wsgi_app.create_fn)

def remove_intercept():
    wsgi_intercept.remove_wsgi_intercept()
    # wsgi_intercept.debuglevel = _saved_debuglevel

@with_setup(add_intercept, remove_intercept)
def test_intercepted():
    b = WSGI_Browser()
    b.open('http://some_hopefully_nonexistant_domain:80/')
    assert test_wsgi_app.success()

@with_setup(add_intercept)
@raises(URLError)
def test_intercept_removed():
    remove_intercept()
    b = WSGI_Browser()
    b.open('http://some_hopefully_nonexistant_domain:80/')
    
@with_setup(add_intercept, remove_intercept)
def test_https_intercepted():
    b = WSGI_Browser()
    b.open('https://some_hopefully_nonexistant_domain/')
    assert test_wsgi_app.success()
    
@with_setup(lambda: add_intercept(443), remove_intercept)
def test_https_intercepted_443_port():
    b = WSGI_Browser()
    b.open('https://some_hopefully_nonexistant_domain:443/')
    assert test_wsgi_app.success()