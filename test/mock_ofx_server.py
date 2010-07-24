# Copyright 2005-2010 Wesabe, Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# MockOfxServer - simple mock server for testing
#

import sys
sys.path.insert(0, '../3rdparty')
sys.path.insert(0, '../lib')

import ofx_test_utils

import urllib2
from wsgi_intercept.urllib2_intercept import install_opener
import wsgi_intercept

class MockOfxServer:
    def __init__(self, port=9876):
        install_opener()
        wsgi_intercept.add_wsgi_intercept('localhost', port, self.interceptor)
    
    def handleResponse(self, environment, start_response):
        status  = "200 OK"
        headers = [('Content-Type', 'application/ofx')]
        start_response(status, headers)
        if environment.has_key("wsgi.input"):
            request_body = environment["wsgi.input"].read()
            
            if request_body.find("<ACCTTYPE>CHECKING") != -1:
                return ofx_test_utils.get_checking_stmt()
            elif request_body.find("<ACCTTYPE>SAVINGS") != -1:
                return ofx_test_utils.get_savings_stmt()
            else:
                return ofx_test_utils.get_creditcard_stmt()
        else:
            return ofx_test_utils.get_creditcard_stmt()
    
    def interceptor(self):
        return self.handleResponse

import unittest

class MockOfxServerTest(unittest.TestCase):
    def setUp(self):
        self.server = MockOfxServer()
        self.success = ofx_test_utils.get_creditcard_stmt()
    
    def test_simple_get(self):
        result = urllib2.urlopen('http://localhost:9876/')
        self.assertEqual(result.read(), self.success)

if __name__ == "__main__":
    unittest.main()
