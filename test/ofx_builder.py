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

from ofx.builder import *
from ofx.builder import Tag  # not exported by default
import unittest

class BuilderTests(unittest.TestCase):
    def test_blank_node(self):
        """Test generation of a blank node tag."""
        BLANK = Tag("BLANK")
        self.assertEqual("<BLANK>\r\n", BLANK())
    
    def test_node(self):
        """Test generation of a node tag."""
        NODE = Tag("NODE")
        self.assertEqual("<NODE>text\r\n", NODE("text"))
    
    def test_blank_aggregate_node(self):
        """Test generation of an empty aggregate tag."""
        AGGREGATE = Tag("AGGREGATE", aggregate=True)
        self.assertEqual("<AGGREGATE>\r\n</AGGREGATE>\r\n", AGGREGATE())
    
    def test_nested_tags(self):
        """Test generation of an aggregate containing three nodes."""
        ONE = Tag("ONE")
        TWO = Tag("TWO")
        THREE = Tag("THREE")
        CONTAINER = Tag("CONTAINER", aggregate=True)
        self.assertEqual(
            "<CONTAINER>\r\n<ONE>one\r\n<TWO>two\r\n<THREE>three\r\n</CONTAINER>\r\n",
            CONTAINER(ONE("one"), TWO("two"), THREE("three")))
    
    def test_blank_header(self):
        """Test generation of a blank header."""
        HEADER = Tag("HEADER", header=True)
        self.assertEqual("HEADER:\r\n", HEADER())
    
    def test_header(self):
        """Test generation of a header."""
        ONE = Tag("ONE", header=True)
        self.assertEqual("ONE:value\r\n", ONE("value"))
    
    def test_blank_header_block(self):
        """Stupid test of a blank header block."""
        BLOCK = Tag("", header_block=True)
        self.assertEqual("\r\n", BLOCK())
    
    def test_header_block(self):
        ONE = Tag("ONE", header=True)
        TWO = Tag("TWO", header=True)
        THREE = Tag("THREE", header=True)
        BLOCK = Tag("", header_block=True)
        self.assertEqual("ONE:one\r\nTWO:two\r\nTHREE:three\r\n\r\n",
            BLOCK(ONE("one"), TWO("two"), THREE("three")))
    
    def test_bankaccount_request(self):
        """Generate a full, real OFX message, and compare it to static
        test data."""
        testquery = DOCUMENT(
            HEADER(
                OFXHEADER("100"),
                DATA("OFXSGML"),
                VERSION("102"),
                SECURITY("NONE"),
                ENCODING("USASCII"),
                CHARSET("1252"),
                COMPRESSION("NONE"),
                OLDFILEUID("NONE"),
                NEWFILEUID("9B33CA3E-C237-4577-8F00-7AFB0B827B5E")),
            OFX(
                SIGNONMSGSRQV1(
                    SONRQ(
                        DTCLIENT("20060221150810"),
                        USERID("username"),
                        USERPASS("userpass"),
                        LANGUAGE("ENG"),
                        FI(
                            ORG("FAKEOFX"),
                            FID("1000")),
                        APPID("MONEY"),
                        APPVER("1200"))),
                BANKMSGSRQV1(
                    STMTTRNRQ(
                        TRNUID("9B33CA3E-C237-4577-8F00-7AFB0B827B5E"),
                        CLTCOOKIE("4"),
                        STMTRQ(
                            BANKACCTFROM(
                                BANKID("2000"),
                                ACCTID("12345678"),
                                ACCTTYPE("CHECKING")),
                            INCTRAN(
                                DTSTART("20060221150810"),
                                INCLUDE("Y")))))))
        
        controlquery = "OFXHEADER:100\r\nDATA:OFXSGML\r\nVERSION:102\r\nSECURITY:NONE\r\nENCODING:USASCII\r\nCHARSET:1252\r\nCOMPRESSION:NONE\r\nOLDFILEUID:NONE\r\nNEWFILEUID:9B33CA3E-C237-4577-8F00-7AFB0B827B5E\r\n\r\n<OFX>\r\n<SIGNONMSGSRQV1>\r\n<SONRQ>\r\n<DTCLIENT>20060221150810\r\n<USERID>username\r\n<USERPASS>userpass\r\n<LANGUAGE>ENG\r\n<FI>\r\n<ORG>FAKEOFX\r\n<FID>1000\r\n</FI>\r\n<APPID>MONEY\r\n<APPVER>1200\r\n</SONRQ>\r\n</SIGNONMSGSRQV1>\r\n<BANKMSGSRQV1>\r\n<STMTTRNRQ>\r\n<TRNUID>9B33CA3E-C237-4577-8F00-7AFB0B827B5E\r\n<CLTCOOKIE>4\r\n<STMTRQ>\r\n<BANKACCTFROM>\r\n<BANKID>2000\r\n<ACCTID>12345678\r\n<ACCTTYPE>CHECKING\r\n</BANKACCTFROM>\r\n<INCTRAN>\r\n<DTSTART>20060221150810\r\n<INCLUDE>Y\r\n</INCTRAN>\r\n</STMTRQ>\r\n</STMTTRNRQ>\r\n</BANKMSGSRQV1>\r\n</OFX>"
        self.assertEqual(testquery, controlquery)

if __name__ == '__main__':
    unittest.main()
