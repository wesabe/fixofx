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

class RequestTests(unittest.TestCase):
    def setUp(self):
        self.request = ofx.Request()
        self.institution = ofx.Institution(ofx_org="fi_name", ofx_fid="1000")
        self.account = ofx.Account(acct_number="00112233",
                                   aba_number="12345678",
                                   acct_type="Checking",
                                   institution=self.institution)
        self.username = "joeuser"
        self.password = "mypasswd"
        self.parser  = ofx.Parser()

    # FIXME: Need to add tests for date formatting.

    def test_header(self):
        """Test the correctness of an OFX document header by examining
        some of the dynamically-generated values at the bottom of the
        header.  This test uses a bank statement request, since that
        is our most common use, and since that will build a full, parsable
        document, including the header."""
        parsetree = self.parser.parse(self.request.bank_stmt(self.account,
                                                             self.username,
                                                             self.password))
        self.assertEqual("NONE", parsetree["header"]["OLDFILEUID"])
        self.assertNotEqual("NONE", parsetree["header"]["NEWFILEUID"])

    def test_sign_on(self):
        """Test the OFX document sign-on block, using a bank statement
        request again."""
        parsetree = self.parser.parse(self.request.bank_stmt(self.account,
                                                             self.username,
                                                             self.password))
        # FIXME: add DTCLIENT test here.
        signon = parsetree["body"]["OFX"]["SIGNONMSGSRQV1"]["SONRQ"]
        self.assertEqual("joeuser", signon["USERID"])
        self.assertEqual("mypasswd", signon["USERPASS"])
        self.assertEqual("fi_name", signon["FI"]["ORG"])
        self.assertEqual("1000", signon["FI"]["FID"])
        self.assertEqual("Money", signon["APPID"])
        self.assertEqual("1400", signon["APPVER"])

    def test_account_info(self):
        """Test the values sent for an account info request."""
        parsetree = self.parser.parse(self.request.account_info(self.institution,
                                                                self.username,
                                                                self.password))
        info = parsetree["body"]["OFX"]["SIGNUPMSGSRQV1"]["ACCTINFOTRNRQ"]
        self.assertNotEqual("NONE", info["TRNUID"])
        self.assertEqual("4", info["CLTCOOKIE"])
        self.assertEqual("19980101", info["ACCTINFORQ"]["DTACCTUP"])

    def test_bank_stmt(self):
        """Test the specific values for a bank statement request."""
        parsetree = self.parser.parse(self.request.bank_stmt(self.account,
                                                             self.username,
                                                             self.password))
        stmt = parsetree["body"]["OFX"]["BANKMSGSRQV1"]["STMTTRNRQ"]
        self.assertNotEqual("NONE", stmt["TRNUID"])
        self.assertEqual("4", stmt["CLTCOOKIE"])
        self.assertEqual("12345678", stmt["STMTRQ"]["BANKACCTFROM"]["BANKID"])
        self.assertEqual("00112233", stmt["STMTRQ"]["BANKACCTFROM"]["ACCTID"])
        self.assertEqual("CHECKING",stmt["STMTRQ"]["BANKACCTFROM"]["ACCTTYPE"])
        # FIXME: Add DTSTART and DTEND tests here.

    def test_creditcard_stmt(self):
        """Test the specific values for a credit card statement request."""
        self.account.acct_number = "412345678901"
        parsetree = self.parser.parse(self.request.creditcard_stmt(self.account,
                                                                   self.username,
                                                                   self.password))
        stmt = parsetree["body"]["OFX"]["CREDITCARDMSGSRQV1"]["CCSTMTTRNRQ"]
        self.assertNotEqual("NONE", stmt["TRNUID"])
        self.assertEqual("4", stmt["CLTCOOKIE"])
        self.assertEqual("412345678901", stmt["CCSTMTRQ"]["CCACCTFROM"]["ACCTID"])
        # FIXME: Add DTSTART and DTEND tests here.

if __name__ == '__main__':
    unittest.main()
