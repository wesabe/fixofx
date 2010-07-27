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
import ofx_test_utils

import os
import pprint
import unittest
from xml.parsers.expat import ExpatError
import xml.etree.ElementTree as ElementTree 

class ResponseTests(unittest.TestCase):
    def setUp(self):
        self.response_text = ofx_test_utils.get_checking_stmt()
        self.response = ofx.Response(self.response_text)

    def test_signon_success(self):
        status = self.response.check_signon_status()
        self.assertTrue(status)

    def test_account_list(self):
        statements = self.response.get_statements()
        self.assertEqual(1, len(statements))

        for stmt in statements:
            self.assertEqual("USD", stmt.get_currency())
            self.assertEqual("20100424", stmt.get_begin_date())
            self.assertEqual("20100723", stmt.get_end_date())
            self.assertEqual("1129.49",        stmt.get_balance())
            self.assertEqual("20100723", stmt.get_balance_date())

            account = stmt.get_account()
            self.assertEqual("987987987", account.aba_number)
            self.assertEqual("58152460", account.acct_number)
            self.assertEqual("CHECKING", account.get_ofx_accttype())

    def test_as_xml(self):
        # First just sanity-check that ElementTree will throw an error
        # if given a non-XML document.
        try:
            response_elem = ElementTree.fromstring(self.response_text)
            self.fail("Expected parse exception but did not get one.")
        except ExpatError:
            pass

        # Then see if we can get a real parse success, with no ExpatError.
        xml = self.response.as_xml()
        xml_elem = ElementTree.fromstring(xml)
        self.assertTrue(isinstance(xml_elem, ElementTree._ElementInterface))

        # Finally, for kicks, try to get a value out of it.
        org_iter = xml_elem.getiterator("ORG")
        for org in org_iter:
            self.assertEqual("FAKEOFX", org.text)

if __name__ == '__main__':
    unittest.main()
