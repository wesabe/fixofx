#! /usr/bin/env python
import sys, os.path

import wsgi_intercept
from wsgi_intercept import WSGI_HTTPConnection
from wsgi_intercept import test_wsgi_app

from httplib import HTTP

class WSGI_HTTP(HTTP):
    _connection_class = WSGI_HTTPConnection

###

from wsgi_intercept.webunit_intercept import WebTestCase
import unittest

class WSGI_WebTestCase(WebTestCase):
    scheme_handlers = dict(http=WSGI_HTTP)

    def setUp(self):
        wsgi_intercept.add_wsgi_intercept('some_hopefully_nonexistant_domain', 80,
                                          test_wsgi_app.create_fn)
    
    def tearDown(self):
        wsgi_intercept.remove_wsgi_intercept()

    def test_get(self):
        r = self.page('http://some_hopefully_nonexistant_domain/')
        assert test_wsgi_app.success()
        
class WSGI_HTTPS_WebTestCase(WebTestCase):
    scheme_handlers = dict(https=WSGI_HTTP)

    def setUp(self):
        wsgi_intercept.add_wsgi_intercept('some_hopefully_nonexistant_domain', 443,
                                          test_wsgi_app.create_fn)
    
    def tearDown(self):
        wsgi_intercept.remove_wsgi_intercept()

    def test_get(self):
        r = self.page('https://some_hopefully_nonexistant_domain/')
        assert test_wsgi_app.success()

if __name__ == '__main__':
    unittest.main()
