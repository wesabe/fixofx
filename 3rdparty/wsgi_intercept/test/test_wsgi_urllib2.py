#! /usr/bin/env python
import sys, os.path
from nose.tools import with_setup
import urllib2
from wsgi_intercept import urllib2_intercept
import wsgi_intercept
from wsgi_intercept import test_wsgi_app

_saved_debuglevel = None

def add_intercept():
    _saved_debuglevel, wsgi_intercept.debuglevel = wsgi_intercept.debuglevel, 1
    wsgi_intercept.add_wsgi_intercept('some_hopefully_nonexistant_domain', 80, test_wsgi_app.create_fn)
    
def add_https_intercept():
    _saved_debuglevel, wsgi_intercept.debuglevel = wsgi_intercept.debuglevel, 1
    wsgi_intercept.add_wsgi_intercept('some_hopefully_nonexistant_domain', 443, test_wsgi_app.create_fn)

def remove_intercept():
    wsgi_intercept.debuglevel = _saved_debuglevel
    wsgi_intercept.remove_wsgi_intercept()

@with_setup(add_intercept, remove_intercept)
def test():
    urllib2_intercept.install_opener()
    urllib2.urlopen('http://some_hopefully_nonexistant_domain:80/')
    assert test_wsgi_app.success()
    
@with_setup(add_https_intercept, remove_intercept)
def test_https():
    urllib2_intercept.install_opener()
    urllib2.urlopen('https://some_hopefully_nonexistant_domain:443/')
    assert test_wsgi_app.success()
    
@with_setup(add_intercept, remove_intercept)
def test_https_default_port():
    # I guess the default port for https is 80 but I thoght it would be 443
    urllib2_intercept.install_opener()
    urllib2.urlopen('https://some_hopefully_nonexistant_domain/')
    assert test_wsgi_app.success()