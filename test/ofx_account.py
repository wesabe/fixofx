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

import ofx
import unittest

class AccountTests(unittest.TestCase):
    def setUp(self):
        self.institution = ofx.Institution(name="Test Bank", 
                                           ofx_org="Test Bank", 
                                           ofx_url="https://ofx.example.com", 
                                           ofx_fid="9999999")
        self.good_acct = ofx.Account(acct_type="CHECKING", 
                                     acct_number="1122334455", 
                                     aba_number="123456789", 
                                     institution=self.institution)
        self.bad_acct  = ofx.Account(acct_type="Fnargle",
                                     acct_number="", aba_number="", 
                                     institution=None)
    
    def test_account_complete(self):
        self.assertEqual(self.good_acct.is_complete(), True)
        self.assertEqual(self.bad_acct.is_complete(), False)
    
    def test_as_dict(self):
        testdict = self.good_acct.as_dict()
        self.assertEqual(testdict["acct_type"], "CHECKING")
        self.assertEqual(testdict["acct_number"], "1122334455")
        self.assertEqual(testdict["aba_number"], "123456789")
        self.assertEqual(testdict["desc"], None)
        self.assertEqual(testdict["balance"], None)
        
        fi_dict = testdict["institution"]
        self.assertEqual(fi_dict["name"], "Test Bank")
        self.assertEqual(fi_dict["ofx_org"], "Test Bank")
        self.assertEqual(fi_dict["ofx_url"], "https://ofx.example.com")
        self.assertEqual(fi_dict["ofx_fid"], "9999999")
    
    def test_load_from_dict(self):
        testdict = self.good_acct.as_dict()
        new_acct = ofx.Account.load_from_dict(testdict)
        self.assertEqual(new_acct.acct_type, "CHECKING")
        self.assertEqual(new_acct.acct_number, "1122334455")
        self.assertEqual(new_acct.aba_number, "123456789")
        self.assertEqual(new_acct.desc, None)
        self.assertEqual(new_acct.balance, None)
        
        new_fi = ofx.Institution.load_from_dict(testdict['institution'])
        self.assertEqual(new_fi.name, "Test Bank")
        self.assertEqual(new_fi.ofx_org, "Test Bank")
        self.assertEqual(new_fi.ofx_url, "https://ofx.example.com")
        self.assertEqual(new_fi.ofx_fid, "9999999")
    

if __name__ == '__main__':
    unittest.main()
