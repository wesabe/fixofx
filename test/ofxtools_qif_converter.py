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

import ofxtools
import textwrap
import unittest
from pyparsing import ParseException
from time import localtime, strftime

class QifConverterTests(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_bank_stmttype(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/13/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertEqual(converter.accttype, "CHECKING")
    
    def test_ccard_stmttype(self):
        qiftext = textwrap.dedent('''\
        !Type:CCard
        D01/13/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertEqual(converter.accttype, "CREDITCARD")
    
    def test_no_stmttype(self):
        qiftext = textwrap.dedent('''\
        D01/13/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertEqual(converter.accttype, "CHECKING")
    
    def test_no_txns(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        ''')
        today = strftime("%Y%m%d", localtime())
        converter = ofxtools.QifConverter(qiftext)
        self.assertEqual(converter.start_date, today)
        self.assertEqual(converter.end_date, today)
    
    def test_us_date(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/13/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertTrue(converter.txns_by_date.has_key("20050113"))
    
    def test_uk_date(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D13/01/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertTrue(converter.txns_by_date.has_key("20050113"))
    
    def test_ambiguous_date(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D12/01/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertTrue(converter.txns_by_date.has_key("20051201"))
    
    def test_mixed_us_dates(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/12/2005
        ^
        D01/13/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertTrue(converter.txns_by_date.has_key("20050112"))
        self.assertTrue(converter.txns_by_date.has_key("20050113"))
    
    def test_mixed_uk_dates(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D12/01/2005
        ^
        D13/01/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertTrue(converter.txns_by_date.has_key("20050112"))
        self.assertTrue(converter.txns_by_date.has_key("20050113"))
    
    def test_slashfree_date(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D12012005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertTrue(converter.txns_by_date.has_key("20051201"))
    
    def test_unparseable_date(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        DFnargle
        ^
        ''')
        self.assertRaises(ValueError, ofxtools.QifConverter, qiftext)
    
    def test_len_eight_no_int_date(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        DAAAAAAAA
        ^
        ''')
        self.assertRaises(ValueError, ofxtools.QifConverter, qiftext)
    
    def test_asc_dates(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/13/2005
        ^
        D01/27/2005
        ^
        D02/01/2005
        ^
        D02/01/2005
        ^        
        D02/13/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertEqual(converter.start_date, "20050113")
        self.assertEqual(converter.end_date, "20050213")
        self.assertEqual(len(converter.txns_by_date.keys()), 4)
    
    def test_desc_dates(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D02/13/2005
        ^
        D02/01/2005
        ^
        D02/01/2005
        ^        
        D01/27/2005
        ^
        D01/13/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertEqual(converter.start_date, "20050113")
        self.assertEqual(converter.end_date, "20050213")
        self.assertEqual(len(converter.txns_by_date.keys()), 4)
    
    def test_mixed_dates(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D02/01/2005
        ^
        D02/13/2005
        ^
        D01/13/2005
        ^
        D02/01/2005
        ^        
        D01/27/2005
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        self.assertEqual(converter.start_date, "20050113")
        self.assertEqual(converter.end_date, "20050213")
        self.assertEqual(len(converter.txns_by_date.keys()), 4)
    
    def test_default_currency(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/25/2007
        T417.93
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        ofx102 = converter.to_ofx102()
        self.assertTrue(ofx102.find('<CURDEF>USD') != -1)
    
    def test_found_currency(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/25/2007
        T417.93
        ^EUR
        ''')
        converter = ofxtools.QifConverter(qiftext)
        ofx102 = converter.to_ofx102()
        self.assertTrue(ofx102.find('<CURDEF>EUR') != -1)
    
    def test_explicit_currency(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/25/2007
        T417.93
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext, curdef='GBP')
        ofx102 = converter.to_ofx102()
        self.assertTrue(ofx102.find('<CURDEF>GBP') != -1)
    
    def test_amount2(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D02/01/2005
        U25.42
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        txn = converter.txns_by_date["20050201"][0]
        self.assertEqual(txn["Amount"], "25.42")
    
    def test_bad_amount_precision(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/25/2007
        T417.930
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        txn = converter.txns_by_date["20070125"][0]
        self.assertEqual(txn["Amount"], "417.93")
    
    def test_dash_amount(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D02/01/2005
        T25.42
        ^
        D02/01/2005
        T-
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        txn_list = converter.txns_by_date["20050201"]
        self.assertEqual(len(txn_list), 1)
        txn = txn_list[0]
        self.assertEqual(txn["Amount"], "25.42")
    
    def test_trailing_minus(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D08/06/2008
        T26.24-
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        txn = converter.txns_by_date["20080806"][0]
        self.assertEqual(txn["Amount"], "-26.24")
    
    def test_n_a_number(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/25/2007
        T417.93
        NN/A
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        txn = converter.txns_by_date["20070125"][0]
        self.assertEqual(txn.has_key("Number"), False)
    
    def test_creditcard_number(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/25/2007
        T417.93
        NXXXX-XXXX-XXXX-1234
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        txn = converter.txns_by_date["20070125"][0]
        self.assertEqual(txn.has_key("Number"), False)
    
    def test_creditcard_stmt_number(self):
        qiftext = textwrap.dedent('''\
        !Type:CCard
        D01/25/2007
        T417.93
        N1234
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        txn = converter.txns_by_date["20070125"][0]
        self.assertEqual(txn.has_key("Number"), False)
    
    def test_check_stmt_number(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/25/2007
        T417.93
        N1234
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        txn = converter.txns_by_date["20070125"][0]
        self.assertEqual(txn.get("Type"), "CHECK")
    
    def test_usaa_check(self):
        qiftext = textwrap.dedent('''\
        !Type:Bank
        D01/25/2007
        T-22.00
        N
        PCHECK # 0000005287
        MChecks
        ^
        ''')
        converter = ofxtools.QifConverter(qiftext)
        txn = converter.txns_by_date["20070125"][0]
        self.assertEqual(txn.get("Type"), "CHECK")
        self.assertEqual(txn.get("Number"), "5287")

if __name__ == '__main__':
    unittest.main()
