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

import sys
sys.path.insert(0, '../3rdparty')
sys.path.insert(0, '../lib')

import ofx_test_utils
import ofx
from mock_ofx_server import MockOfxServer

import unittest

class ClientTests(unittest.TestCase):
    def setUp(self):
        self.port    = 9486
        self.server  = MockOfxServer(port=self.port)
        self.mockurl = "http://localhost:" + str(self.port) + "/"
        self.institution = ofx.Institution(ofx_org="Test Bank", 
                                           ofx_fid="99999",
                                           ofx_url=self.mockurl)
        self.checking_account = ofx.Account(acct_number="1122334455", 
                                            aba_number="12345678", 
                                            acct_type="Checking",
                                            institution=self.institution)
        self.savings_account = ofx.Account(acct_number="1122334455", 
                                           aba_number="12345678", 
                                           acct_type="Savings",
                                           institution=self.institution)
        self.creditcard_account = ofx.Account(acct_number="1122334455", 
                                              aba_number="12345678", 
                                              acct_type="Credit Card",
                                              institution=self.institution)
        self.username = "username"
        self.password = "password"
        self.client  = ofx.Client()
        self.checking_stmt = ofx_test_utils.get_checking_stmt()
        self.savings_stmt = ofx_test_utils.get_savings_stmt()
        self.creditcard_stmt = ofx_test_utils.get_creditcard_stmt()
    
    def test_checking_stmt_request(self):
        response = self.client.get_bank_statement(self.checking_account,
                                                  self.username,
                                                  self.password)
        self.assertEqual(response.as_string(), self.checking_stmt)
    
    def test_savings_stmt_request(self):
        response = self.client.get_bank_statement(self.savings_account,
                                                  self.username,
                                                  self.password)
        self.assertEqual(response.as_string(), self.savings_stmt)
    
    def test_creditcard_stmt_request(self):
        response = self.client.get_creditcard_statement(self.creditcard_account,
                                                        self.username,
                                                        self.password)
        self.assertEqual(response.as_string(), self.creditcard_stmt)
    
    def test_unknown_stmt_request(self):
        checking_response = self.client.get_statement(self.checking_account,
                                                      self.username,
                                                      self.password)
        self.assertEqual(checking_response.as_string(), self.checking_stmt)
        
        savings_response = self.client.get_statement(self.savings_account, 
                                                     self.username,
                                                     self.password)
        self.assertEqual(savings_response.as_string(), self.savings_stmt)
        
        creditcard_response = self.client.get_statement(self.creditcard_account,
                                                        self.username,
                                                        self.password)
        self.assertEqual(creditcard_response.as_string(), self.creditcard_stmt)
    

if __name__ == '__main__':
    unittest.main()
