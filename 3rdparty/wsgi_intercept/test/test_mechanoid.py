#! /usr/bin/env python2.3
from wsgi_intercept.mechanoid_intercept import Browser
from nose.tools import with_setup
import wsgi_intercept
from wsgi_intercept import test_wsgi_app

###

_saved_debuglevel = None

def install(port=80):
    _saved_debuglevel, wsgi_intercept.debuglevel = wsgi_intercept.debuglevel, 1
    wsgi_intercept.add_wsgi_intercept('some_hopefully_nonexistant_domain', port, test_wsgi_app.create_fn)

def uninstall():
    wsgi_intercept.debuglevel = _saved_debuglevel

@with_setup(install, uninstall)
def test_success():
    b = Browser()
    b.open('http://some_hopefully_nonexistant_domain:80/')
    assert test_wsgi_app.success()
    
@with_setup(install, uninstall)
def test_https_success():
    b = Browser()
    b.open('https://some_hopefully_nonexistant_domain/')
    assert test_wsgi_app.success()
    
@with_setup(lambda: install(443), uninstall)
def test_https_specific_port_success():
    b = Browser()
    b.open('https://some_hopefully_nonexistant_domain:443/')
    assert test_wsgi_app.success()