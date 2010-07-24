#! /usr/bin/env python
import sys
import wsgi_intercept
from wsgi_intercept import test_wsgi_app, webtest_intercept

class WSGI_Test(webtest_intercept.WebCase):
    HTTP_CONN = wsgi_intercept.WSGI_HTTPConnection
    HOST = 'some_hopefully_nonexistant_domain'

    def setUp(self):
        wsgi_intercept.add_wsgi_intercept(self.HOST, self.PORT,
                                          test_wsgi_app.create_fn)
    
    def tearDown(self):
        wsgi_intercept.remove_wsgi_intercept()

    def test_page(self):
        self.getPage('http://%s:%s/' % (self.HOST, self.PORT))
        assert test_wsgi_app.success()
        
class WSGI_HTTPS_Test(webtest_intercept.WebCase):
    HTTP_CONN = wsgi_intercept.WSGI_HTTPConnection
    HOST = 'some_hopefully_nonexistant_domain'

    def setUp(self):
        wsgi_intercept.add_wsgi_intercept(self.HOST, self.PORT,
                                          test_wsgi_app.create_fn)
    
    def tearDown(self):
        wsgi_intercept.remove_wsgi_intercept()

    def test_page(self):
        self.getPage('https://%s:%s/' % (self.HOST, self.PORT))
        assert test_wsgi_app.success()

if __name__ == '__main__':
    webtest.main()
