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
import unittest

class ParserTests(unittest.TestCase):
    def setUp(self):
        parser = ofx.Parser()
        checking_stmt = ofx_test_utils.get_checking_stmt()
        creditcard_stmt = ofx_test_utils.get_creditcard_stmt()
        self.checkparse = parser.parse(checking_stmt)
        self.creditcardparse = parser.parse(creditcard_stmt)
    
    def test_successful_parse(self):
        """Test parsing a valid OFX document containing a 'success' message."""
        self.assertEqual("SUCCESS",
            self.checkparse["body"]["OFX"]["SIGNONMSGSRSV1"]["SONRS"]["STATUS"]["MESSAGE"])
    
    def test_body_read(self):
        """Test reading a value from deep in the body of the OFX document."""
        self.assertEqual("-5128.16",
            self.creditcardparse["body"]["OFX"]["CREDITCARDMSGSRSV1"]["CCSTMTTRNRS"]["CCSTMTRS"]["LEDGERBAL"]["BALAMT"])
    
    def test_header_read(self):
        """Test reading a header from the OFX document."""
        self.assertEqual("100", self.checkparse["header"]["OFXHEADER"])
    

if __name__ == '__main__':
    unittest.main()
