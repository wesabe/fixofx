#! /usr/bin/env python2.4
import warnings
from nose.tools import eq_
from wsgi_intercept.httplib2_intercept import install, uninstall
import wsgi_intercept
from wsgi_intercept import test_wsgi_app
import httplib2
from paste import lint

_saved_debuglevel = None

def prudent_wsgi_app():
    return lint.middleware(test_wsgi_app.create_fn())

def setup():
    warnings.simplefilter("error")
    _saved_debuglevel, wsgi_intercept.debuglevel = wsgi_intercept.debuglevel, 1
    install()
    wsgi_intercept.add_wsgi_intercept('some_hopefully_nonexistant_domain', 80, prudent_wsgi_app)

def test():
    http = httplib2.Http()
    resp, content = http.request('http://some_hopefully_nonexistant_domain:80/', 'GET')
    assert test_wsgi_app.success()

def test_quoting_issue11():
    # see http://code.google.com/p/wsgi-intercept/issues/detail?id=11
    http = httplib2.Http()
    inspected_env = {}
    def make_path_checking_app():
        def path_checking_app(environ, start_response):
            inspected_env ['QUERY_STRING'] = environ['QUERY_STRING']
            inspected_env ['PATH_INFO'] = environ['PATH_INFO']
            status = '200 OK'
            response_headers = [('Content-type','text/plain')]
            start_response(status, response_headers)
            return []
        return path_checking_app
    wsgi_intercept.add_wsgi_intercept('some_hopefully_nonexistant_domain', 80, make_path_checking_app)
    resp, content = http.request('http://some_hopefully_nonexistant_domain:80/spaced+words.html?word=something%20spaced', 'GET')
    assert ('QUERY_STRING' in inspected_env and 'PATH_INFO' in inspected_env), "path_checking_app() was never called?"
    eq_(inspected_env['PATH_INFO'], '/spaced+words.html')
    eq_(inspected_env['QUERY_STRING'], 'word=something%20spaced')

def teardown():
    warnings.resetwarnings()
    wsgi_intercept.debuglevel = _saved_debuglevel
    uninstall()

if __name__ == '__main__':
    setup()
    try:
        test()
    finally:
        teardown()
