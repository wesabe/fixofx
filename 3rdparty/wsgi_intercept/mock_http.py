#
# mock_http.py
#
# Written by Marc Hedlund <marc@precipice.org>.
# Released under the same terms as wsgi_intercept.
#

"""
This is a dirt-simple example of using wsgi_intercept to set up a mock
object HTTP server for testing HTTP clients.
"""

import sys
sys.path.insert(0, 'urllib2')

import unittest
import urllib2
import wsgi_intercept
from wsgi_intercept import urllib2_intercept as wsgi_urllib2

test_page = """
    <html>
    <head>
        <title>Mock HTTP Server</title>
    </head>
    <body>
        <h1>Mock HTTP Server</h1>
        <p>You have successfully reached the Mock HTTP Server.</p>
    </body>
    </html>
"""

class MockHttpServer:
    def __init__(self, port=8000):
        """Initializes the mock server on localhost port 8000.  Use
        urllib2.urlopen('http://localhost:8000') to reach the test
        server.  The constructor takes a 'port=<int>' argument if you
        want the server to listen on a different port."""
        wsgi_intercept.add_wsgi_intercept('localhost', port, self.interceptor)
        wsgi_urllib2.install_opener()
    
    def handleResponse(self, environment, start_response):
        """Processes a request to the mock server, and returns a
        String object containing the response document.  The mock server
        will send this to the client code, which can read it as a
        StringIO document.  This example always returns a successful
        response to any request; a more intricate mock server could
        examine the request environment to determine what sort of
        response to give."""
        status  = "200 OK"
        headers = [('Content-Type', 'text/html')]
        start_response(status, headers)
        return test_page
    
    def interceptor(self):
        """Sets this class as the handler for intercepted urllib2
        requests."""
        return self.handleResponse

class MockHttpServerTest(unittest.TestCase):
    """Demonstrates the use of the MockHttpServer from client code."""
    def setUp(self):
        self.server = MockHttpServer()
        
    def test_simple_get(self):
        result = urllib2.urlopen('http://localhost:8000/')
        self.assertEqual(result.read(), test_page)

if __name__ == "__main__":
    unittest.main()
