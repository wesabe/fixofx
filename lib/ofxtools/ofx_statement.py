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
#  ofxtools.OfxStatement - build up an OFX statement from source data.
#

import datetime
import dateutil.parser
import ofx
import ofxtools

class OfxStatement:
    def __init__(self, fid="UNKNOWN", org="UNKNOWN", bankid="UNKNOWN",
                 accttype="UNKNOWN", acctid="UNKNOWN", balance="UNKNOWN",
                 curdef="USD", lang="ENG"):
        self.fid      = fid
        self.org      = org
        self.bankid   = bankid
        self.accttype = accttype
        self.acctid   = acctid
        self.balance  = balance
        self.curdef   = curdef
        self.lang     = lang

    def add_transaction(self, date=None, amount=None, number=None,
                        type=None, payee=None, memo=None):
        txn = ofxtools.OfxTransaction(date, amount, number, type, payee, memo)

    def to_str(self):
        pass

    def __str__(self):
        pass

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
        if self.accttype == "CREDITCARD":
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

        # OFX transactions appear most recent first, and oldest last,
        # so we do a reverse sort of the dates in this statement.
        date_list = self.txns_by_date.keys()
        date_list.sort()
        date_list.reverse()
        for date in date_list:
            txn_list = self.txns_by_date[date]
            txn_index = len(txn_list)
            for txn in txn_list:
                txn_date = txn.get("Date", "UNKNOWN")
                txn_amt  = txn.get("Amount", "00.00")

                # Make a synthetic transaction ID using as many
                # uniqueness guarantors as possible.
                txn["ID"] = "%s-%s-%s-%s-%s" % (self.org, self.accttype,
                                                txn_date, txn_index,
                                                txn_amt)
                txns += self._ofx_txn(txn)
                txn_index -= 1

        # FIXME: This should respect the type of statement being generated.
        return BANKTRANLIST(
            DTSTART(self.start_date),
            DTEND(self.end_date),
            txns)

    def _ofx_txn(self, txn):
        fields = []
        if self._check_field("Type", txn):
            fields.append(TRNTYPE(txn["Type"].strip()))

        if self._check_field("Date", txn):
            fields.append(DTPOSTED(txn["Date"].strip()))

        if self._check_field("Amount", txn):
            fields.append(TRNAMT(txn["Amount"].strip()))

        if self._check_field("Number", txn):
            fields.append(CHECKNUM(txn["Number"].strip()))

        if self._check_field("ID", txn):
            fields.append(FITID(txn["ID"].strip()))

        if self._check_field("Payee", txn):
            fields.append(NAME(sax.escape(sax.unescape(txn["Payee"].strip()))))

        if self._check_field("Memo", txn):
            fields.append(MEMO(sax.escape(sax.unescape(txn["Memo"].strip()))))

        return STMTTRN(*fields)

    def _check_field(self, key, txn):
        return txn.has_key(key) and txn[key].strip() != ""

#
#  ofxtools.OfxTransaction - clean and format transaction information.
#
#  Copyright Wesabe, Inc. (c) 2005-2007. All rights reserved.
#

class OfxTransaction:
    def __init__(self, date=None, amount=None, number=None,
                 type=None, payee=None, memo=None):
        self.raw_date = date
        self.date     = None
        self.amount   = amount
        self.number   = number
        self.type     = type
        self.payee    = payee
        self.memo     = memo
        self.dayfirst = False

        # This is a list of possible transaction types embedded in the
        # QIF Payee or Memo field (depending on bank and, it seems,
        # other factors).  The keys are used to match possible fields
        # that we can identify.  The values are used as substitutions,
        # since banks will use their own vernacular (like "DBT"
        # instead of "DEBIT") for some transaction types.  All of the
        # types in the values column (except "ACH", which is given
        # special treatment) are OFX-2.0 standard transaction types;
        # the keys are not all standard.  To add a new translation,
        # find the QIF name for the transaction type, and add it to
        # the keys column, then add the appropriate value from the
        # OFX-2.0 spec (see page 180 of doc/ofx/ofx-2.0/ofx20.pdf).
        # The substitution will be made if either the payee or memo
        # field begins with one of the keys followed by a "/", OR if
        # the payee or memo field exactly matches a key.
        self.txn_types = { "ACH"         : "ACH",
                           "CHECK CARD"  : "POS",
                           "CREDIT"      : "CREDIT",
                           "DBT"         : "DEBIT",
                           "DEBIT"       : "DEBIT",
                           "INT"         : "INT",
                           "DIV"         : "DIV",
                           "FEE"         : "FEE",
                           "SRVCHG"      : "SRVCHG",
                           "DEP"         : "DEP",
                           "DEPOSIT"     : "DEP",
                           "ATM"         : "ATM",
                           "POS"         : "POS",
                           "XFER"        : "XFER",
                           "CHECK"       : "CHECK",
                           "PAYMENT"     : "PAYMENT",
                           "CASH"        : "CASH",
                           "DIRECTDEP"   : "DIRECTDEP",
                           "DIRECTDEBIT" : "DIRECTDEBIT",
                           "REPEATPMT"   : "REPEATPMT",
                           "OTHER"       : "OTHER"        }

    def guess_date_format(self):
        pass

    def set_date_format(self, dayfirst=False):
        self.dayfirst = dayfirst

    def parse_date(self):
        # Try as best we can to parse the date into a datetime object. Note:
        # this assumes that we never see a timestamp, just the date, in any
        # QIF date.
        if self.date != "UNKNOWN":
            try:
                return dateutil.parser.parse(self.date, dayfirst=self.dayfirst)

            except ValueError:
                # dateutil.parser doesn't recognize dates of the
                # format "MMDDYYYY", though it does recognize
                # "MM/DD/YYYY".  So, if parsing has failed above,
                # try shoving in some slashes and see if that
                # parses.
                try:
                    if len(self.date) == 8:
                        # The int() cast will only succeed if all 8
                        # characters of txn_date are numbers.  If
                        # it fails, it will throw an exception we
                        # can catch below.
                        date_int = int(self.date)
                        # No exception?  Great, keep parsing the
                        # string (dateutil wants a string
                        # argument).
                        slashified = "%s/%s/%s" % (txn_date[0:2],
                                                   txn_date[2:4],
                                                   txn_date[4:])
                        return dateutil.parser.parse(slashified,
                                                     dayfirst=dayfirst)
                except:
                    pass

            # If we've made it this far, our guesses have failed.
            raise ValueError("Unrecognized date format: '%s'." % txn_date)
        else:
            return "UNKNOWN"

    def clean_date(self):
        pass

    def clean_amount(self):
        pass

    def clean_number(self):
        pass

    def clean_type(self):
        pass

    def clean_payee(self):
        pass

    def to_str(self):
        pass

    def __str__(self):
        pass

