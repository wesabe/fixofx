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
#  ofx.OfcConverter - translate OFC files into OFX files.
#

import ofx
import ofxtools
import re
import sys
from ofx.builder import *

class OfcConverter:
    def __init__(self, ofc, fid="UNKNOWN", org="UNKNOWN", curdef=None,
                 lang="ENG", debug=False):
        self.ofc      = ofc
        self.fid      = fid
        self.org      = org
        self.curdef   = curdef
        self.lang     = lang
        self.debug    = debug

        self.bankid     = "UNKNOWN"
        self.accttype   = "UNKNOWN"
        self.acctid     = "UNKNOWN"
        self.balance    = "UNKNOWN"
        self.start_date = "UNKNOWN"
        self.end_date   = "UNKNOWN"

        self.parsed_ofc = None

        self.acct_types = { "0"  : "CHECKING",
                            "1"  : "SAVINGS",
                            "2"  : "CREDITCARD",
                            "3"  : "MONEYMRKT",
                            "4"  : "CREDITLINE",
                            "5"  : "UNKNOWN",
                            "6"  : "UNKNOWN",
                            "7"  : "UNKNOWN" }

        self.txn_types  = { "0"  : "CREDIT",
                            "1"  : "DEBIT",
                            "2"  : "INT",
                            "3"  : "DIV",
                            "4"  : "SRVCHG",
                            "5"  : "DEP",
                            "6"  : "ATM",
                            "7"  : "XFER",
                            "8"  : "CHECK",
                            "9"  : "PAYMENT",
                            "10" : "CASH",
                            "11" : "DIRECTDEP",
                            "12" : "OTHER" }

        if self.debug: sys.stderr.write("Parsing document.\n")

        parser = ofxtools.OfcParser(debug=debug)
        self.parsed_ofc = parser.parse(self.ofc)

        if self.debug: sys.stderr.write("Extracting document properties.\n")

        try:
            self.bankid     = self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["ACCTFROM"]["BANKID"]
            acct_code       = self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["ACCTFROM"]["ACCTTYPE"]
            self.accttype   = self.acct_types.get(acct_code, "UNKNOWN")
            self.acctid     = self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["ACCTFROM"]["ACCTID"]
        except KeyError:
            self.bankid     = self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["ACCTFROM"]["ACCOUNT"]["BANKID"]
            acct_code       = self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["ACCTFROM"]["ACCOUNT"]["ACCTTYPE"]
            self.accttype   = self.acct_types.get(acct_code, "UNKNOWN")
            self.acctid     = self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["ACCTFROM"]["ACCOUNT"]["ACCTID"]

        self.balance    = self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["STMTRS"]["LEDGER"]
        self.start_date = self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["STMTRS"]["DTSTART"]
        self.end_date   = self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["STMTRS"]["DTEND"]

    #
    # Conversion methods
    #

    def to_ofx102(self):
        if self.debug: sys.stderr.write("Making OFX/1.02.\n")
        return DOCUMENT(self._ofx_header(),
                        OFX(self._ofx_signon(),
                            self._ofx_stmt()))

    def to_xml(self):
        ofx102 = self.to_ofx102()

        if self.debug:
            sys.stderr.write(ofx102 + "\n")
            sys.stderr.write("Parsing OFX/1.02.\n")
        response = ofx.Response(ofx102, debug=self.debug)

        if self.debug: sys.stderr.write("Making OFX/2.0.\n")

        xml = response.as_xml(original_format="OFC")

        return xml

    # FIXME: Move the remaining methods to ofx.Document or ofx.Response.

    def _ofx_header(self):
        return HEADER(
            OFXHEADER("100"),
            DATA("OFXSGML"),
            VERSION("102"),
            SECURITY("NONE"),
            ENCODING("USASCII"),
            CHARSET("1252"),
            COMPRESSION("NONE"),
            OLDFILEUID("NONE"),
            NEWFILEUID("NONE"))

    def _ofx_signon(self):
        return SIGNONMSGSRSV1(
            SONRS(
                STATUS(
                  CODE("0"),
                  SEVERITY("INFO"),
                  MESSAGE("SUCCESS")),
                DTSERVER(self.end_date),
                LANGUAGE(self.lang),
                FI(
                    ORG(self.org),
                    FID(self.fid))))

    def _ofx_stmt(self):
        # Set default currency here, instead of on init, so that the caller
        # can override the currency format found in the QIF file if desired.
        # See also _guess_formats(), above.
        if self.curdef is None:
            curdef = "USD"
        else:
            curdef = self.curdef

        if self.accttype == "Credit Card":
            return CREDITCARDMSGSRSV1(
                CCSTMTTRNRS(
                    TRNUID("0"),
                    self._ofx_status(),
                    CCSTMTRS(
                        CURDEF(curdef),
                        CCACCTFROM(
                            ACCTID(self.acctid)),
                        self._ofx_txns(),
                        self._ofx_ledgerbal(),
                        self._ofx_availbal())))
        else:
            return BANKMSGSRSV1(
                STMTTRNRS(
                    TRNUID("0"),
                    self._ofx_status(),
                    STMTRS(
                        CURDEF(curdef),
                        BANKACCTFROM(
                            BANKID(self.bankid),
                            ACCTID(self.acctid),
                            ACCTTYPE(self.accttype)),
                        self._ofx_txns(),
                        self._ofx_ledgerbal(),
                        self._ofx_availbal())))

    def _ofx_status(self):
        return STATUS(
            CODE("0"),
            SEVERITY("INFO"),
            MESSAGE("SUCCESS"))

    def _ofx_ledgerbal(self):
        return LEDGERBAL(
            BALAMT(self.balance),
            DTASOF(self.end_date))

    def _ofx_availbal(self):
        return AVAILBAL(
            BALAMT(self.balance),
            DTASOF(self.end_date))

    def _ofx_txns(self):
        txns = ""
        last_date = None
        txn_index = 1

        for item in self.parsed_ofc["document"]["OFC"]["ACCTSTMT"]["STMTRS"]:
            if item[0] == "STMTTRN":
                txn = item.asDict()
                if txn.has_key('GENTRN'):
                    txn = txn['GENTRN'].asDict()

                txn_date = txn["DTPOSTED"]
                if txn_date != last_date:
                    last_date = txn_date
                    txn_index = 1

                txn_amt  = txn["TRNAMT"]
                txn_type = self.txn_types.get(txn["TRNTYPE"])
                if txn_type is None:
                    if txn_amt.startswith('-'):
                        txn["TRNTYPE"] = "DEBIT"
                    else:
                        txn["TRNTYPE"] = "CREDIT"

                # Make a synthetic transaction ID using as many
                # uniqueness guarantors as possible.
                txn["FITID"] = "%s-%s-%s-%s-%s" % (self.org, self.accttype,
                                                   txn_date, txn_index,
                                                   txn_amt)
                txns += self._ofx_txn(txn)
                txn_index += 1

        return BANKTRANLIST(
            DTSTART(self.start_date),
            DTEND(self.end_date),
            txns)

    def _ofx_txn(self, txn):
        fields = []
        if self._check_field("TRNTYPE", txn):
            fields.append(TRNTYPE(txn["TRNTYPE"].strip()))

        if self._check_field("DTPOSTED", txn):
            fields.append(DTPOSTED(txn["DTPOSTED"].strip()))

        if self._check_field("TRNAMT", txn):
            fields.append(TRNAMT(txn["TRNAMT"].strip()))

        if self._check_field("CHECKNUM", txn):
            fields.append(CHECKNUM(txn["CHECKNUM"].strip()))

        if self._check_field("FITID", txn):
            fields.append(FITID(txn["FITID"].strip()))

        if self._check_field("NAME", txn):
            fields.append(NAME(txn["NAME"].strip()))

        if self._check_field("MEMO", txn):
            fields.append(MEMO(txn["MEMO"].strip()))

        return STMTTRN(*fields)

    def _check_field(self, key, txn):
        return txn.has_key(key) and txn[key].strip() != ""


