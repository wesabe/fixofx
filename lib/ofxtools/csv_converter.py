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
#  ofxtools.CsvConverter - translate CSV files into OFX files.
#

import datetime
import dateutil.parser
import ofx
import ofxtools
import re
import sys
import xml.sax.saxutils as sax
from decimal import *
from ofx.builder import *

class CsvConverter:
    def __init__(self, qif, colspec=None, fid="UNKNOWN", org="UNKNOWN",
                 bankid="UNKNOWN", accttype="UNKNOWN", acctid="UNKNOWN",
                 balance="UNKNOWN", curdef=None, lang="ENG", dayfirst=False,
                 debug=False):
        self.qif      = qif
        self.colspec  = colspec
        self.fid      = fid
        self.org      = org
        self.bankid   = bankid
        self.accttype = accttype
        self.acctid   = acctid
        self.balance  = balance
        self.curdef   = curdef
        self.lang     = lang
        self.debug    = debug
        self.dayfirst = dayfirst

        self.parsed_csv = None

        # FIXME: Move this to one of the OFX generation classes (Document or Response).
        self.txns_by_date = {}

        if self.debug: sys.stderr.write("Parsing document.\n")

        parser = ofxtools.QifParser()  # debug=debug)
        self.parsed_qif = parser.parse(self.qif)

        if self.debug: sys.stderr.write("Cleaning transactions.\n")

        # We do a two-pass conversion in order to check the dates of all
        # transactions in the statement, and convert all the dates using
        # the same date format.  The first pass does nothing but look
        # at dates; the second actually applies the date conversion and
        # all other conversions, and extracts information needed for
        # the final output (like date range).
        txn_list = self._extract_txn_list(self.parsed_qif)
        self._guess_formats(txn_list)
        self._clean_txn_list(txn_list)

    def _extract_txn_list(self, qif):
        stmt_obj = qif.asDict()["QifStatement"]

        if self.accttype == "UNKNOWN":
            if "BankTransactions" in stmt_obj:
                self.accttype = "CHECKING"
            elif "CreditCardTransactions" in stmt_obj:
                self.accttype = "CREDITCARD"

        txn_list = []
        for stmt in stmt_obj:
            for txn in stmt:
                txn_list.append(txn)

        if len(txn_list) == 0:
            raise ValueError("Found no transactions to convert " +
                             "in the QIF source.")
        else:
            return txn_list

    #
    # Date methods
    #

    def _guess_formats(self, txn_list):
        # Go through the transactions one at a time, and try to parse the date
        # field and currency format. If we check the date format and find a
        # transaction where the first number must be the day (that is, the first
        # number is in the range 13..31), then set the state of the converter to
        # use dayfirst for all transaction cleanups. This is a guess because the
        # method will only work for UK dates if the statement contains a day in
        # the 13..31 range. (We could also test whether a date appears out of
        # order, or whether the jumps between transactions are especially long,
        # if this guessing method doesn't work reliably.)
        for txn_obj in txn_list:
            txn = txn_obj.asDict()
            txn_date     = txn.get("Date",     "UNKNOWN")
            txn_currency = txn.get("Currency", "UNKNOWN")
            # Look for date format.
            parsed_date = self._parse_date(txn_date)
            self._check_date_format(parsed_date)

    def _parse_date(self, txn_date, dayfirst=False):

    def _check_date_format(self, parsed_date):
        # If we *ever* find a date that parses as dayfirst, treat
        # *all* transactions in this statement as dayfirst.
        if parsed_date is not None and parsed_date != "UNKNOWN" and parsed_date.microsecond == 3:
            self.dayfirst = True

    #
    # Cleanup methods
    #

    def _clean_txn_list(self, txn_list):
        for txn_obj in txn_list:
            try:
                txn = self._clean_txn(txn_obj)
                txn_date = txn["Date"]
                txn_date_list = self.txns_by_date.get(txn_date, [])
                txn_date_list.append(txn)
                self.txns_by_date[txn_date] = txn_date_list
            except ValueError:
                # The _clean_txn method will sometimes find transactions
                # that are inherently unclean and are unable to be purified.
                # In these cases it will reject the transaction by throwing
                # a ValueError, which signals us not to store the transaction.
                if self.debug: sys.stderr.write("Skipping transaction '%s'." %
                                                str(txn_obj.asDict()))

        # Sort the dates (in YYYYMMDD format) and choose the lowest
        # date as our start date, and the highest date as our end
        # date.
        date_list = self.txns_by_date.keys()
        date_list.sort()

        self.start_date = date_list[0]
        self.end_date   = date_list[-1]

    def _clean_txn(self, txn_obj):
        # This is sort of the brute-force method of the converter.  It
        # looks at the data we get from the bank and tries as hard as
        # possible to make best-effort guesses about what the OFX 2.0
        # standard values for the transaction should be.  There's a
        # reasonable amount of guesswork in here -- some of it wise,
        # maybe some of it not.  If the cleanup method determines that
        # the txn_obj shouldn't be in the data, it will return None.
        # Otherwise, it will return a transaction cleaned to the best
        # of our abilities.
        txn = txn_obj.asDict()
        self._clean_txn_date(txn)
        self._clean_txn_amount(txn)
        self._clean_txn_number(txn)
        self._clean_txn_type(txn)
        self._clean_txn_payee(txn)
        return txn

    def _clean_txn_date(self, txn):
        txn_date    = txn.get("Date", "UNKNOWN").strip()
        if txn_date != "UNKNOWN":
            parsed_date = self._parse_date(txn_date, dayfirst=self.dayfirst)
            txn["Date"] = parsed_date.strftime("%Y%m%d")
        else:
            txn["Date"] = "UNKNOWN"

    def _clean_txn_amount(self, txn):
        txn_amount  = txn.get("Amount",  "00.00")
        txn_amount2 = txn.get("Amount2", "00.00")

        # Home Depot Credit Card seems to send two transaction records for each
        # transaction. They're out of order (that is, the second record is not
        # directly after the first, nor even necessarily after it at all), and
        # the second one *sometimes* appears to be a memo field on the first one
        # (e.g., a credit card payment will show up with an amount and date, and
        # then the next transaction will have the same date and a payee that
        # reads, "Thank you for your payment!"), and *sometimes* is the real
        # payee (e.g., the first will say "Home Depot" and the second will say
        # "Seasonal/Garden"). One of the two transaction records will have a
        # transaction amount of "-", and the other will have the real
        # transaction amount. Ideally, we would pull out the memo and attach it
        # to the right transaction, but unless the two transactions are the only
        # transactions on that date, there doesn't seem to be a good clue (order
        # in statement, amount, etc.) as to how to associate them. So, instead,
        # we're returning None, which means this transaction should be removed
        # from the statement and not displayed to the user. The result is that
        # for Home Depot cards, sometimes we lose the memo (which isn't that big
        # a deal), and sometimes we make the memo into the payee (which sucks).
        if txn_amount == "-" or txn_amount == " ":
            raise ValueError("Transaction amount is undefined.")

        # Some QIF sources put the amount in Amount2 instead, for unknown
        # reasons.  Here we ignore Amount2 unless Amount is unknown.
        if txn_amount == "00.00":
            txn_amount = txn_amount2

        # Okay, now strip out whitespace padding.
        txn_amount = txn_amount.strip()

        # Some QIF files have dollar signs in the amount.  Hey, why not?
        txn_amount = txn_amount.replace('$', '', 1)

        # Some QIF sources put three digits after the decimal, and the Ruby
        # code thinks that means we're in Europe.  So.....let's deal with
        # that now.
        try:
            txn_amount = str(Decimal(txn_amount).quantize(Decimal('.01')))
        except:
            # Just keep truckin'.
            pass

        txn["Amount"] = txn_amount

    def _clean_txn_number(self, txn):
        txn_number  = txn.get("Number", "UNKNOWN").strip()

        # Clean up bad check number behavior
        all_digits = re.compile("\d+")

        if txn_number == "N/A":
            # Get rid of brain-dead Chase check number "N/A"s
            del txn["Number"]

        elif txn_number.startswith("XXXX-XXXX-XXXX"):
            # Home Depot credit cards throw THE CREDIT CARD NUMBER
            # into the check number field.  Oy!  At least they mask
            # the first twelve digits, so we know they're insane.
            del txn["Number"]

        elif txn_number != "UNKNOWN" and self.accttype == "CREDITCARD":
            # Several other credit card companies (MBNA, CapitalOne)
            # seem to use the number field as a transaction ID.  Get
            # rid of this.
            del txn["Number"]

        elif txn_number == "0000000000" and self.accttype != "CREDITCARD":
            # There's some bank that puts "N0000000000" in every non-check
            # transaction.  (They do use normal check numbers for checks.)
            del txn["Number"]

        elif txn_number != "UNKNOWN" and all_digits.search(txn_number):
            # Washington Mutual doesn't indicate a CHECK transaction
            # when a check number is present.
            txn["Type"] = "CHECK"

    def _clean_txn_type(self, txn):
        txn_type    = "UNKNOWN"
        txn_amount  = txn.get("Amount", "UNKNOWN")
        txn_payee   = txn.get("Payee",  "UNKNOWN")
        txn_memo    = txn.get("Memo",   "UNKNOWN")
        txn_number  = txn.get("Number", "UNKNOWN")
        txn_sign    = self._txn_sign(txn_amount)

        # Try to figure out the transaction type from the Payee or
        # Memo field.
        for typestr in self.txn_types.keys():
            if txn_number == typestr:
                # US Bank sends "DEBIT" or "CREDIT" as a check number
                # on credit card transactions.
                txn["Type"] = self.txn_types[typestr]
                del txn["Number"]
                break

            elif txn_payee.startswith(typestr + "/") or \
            txn_memo.startswith(typestr + "/") or \
            txn_memo == typestr or txn_payee == typestr:
                if typestr == "ACH" and txn_sign == "credit":
                    txn["Type"] = "DIRECTDEP"

                elif typestr == "ACH" and txn_sign == "debit":
                    txn["Type"] = "DIRECTDEBIT"

                else:
                    txn["Type"] = self.txn_types[typestr]
                break

    def _clean_txn_payee(self, txn):
        txn_payee   = txn.get("Payee",  "UNKNOWN")
        txn_memo    = txn.get("Memo",   "UNKNOWN")
        txn_number  = txn.get("Number", "UNKNOWN")
        txn_type    = txn.get("Type",   "UNKNOWN")
        txn_amount  = txn.get("Amount", "UNKNOWN")
        txn_sign    = self._txn_sign(txn_amount)

        # Try to fill in the payee field with some meaningful value.
        if txn_payee == "UNKNOWN":
            if txn_number != "UNKNOWN" and (self.accttype == "CHECKING" or
            self.accttype == "SAVINGS"):
                txn["Payee"] = "Check #%s" % txn_number
                txn["Type"]  = "CHECK"

            elif txn_type == "INT" and txn_sign == "debit":
                txn["Payee"] = "Interest paid"

            elif txn_type == "INT" and txn_sign == "credit":
                txn["Payee"] = "Interest earned"

            elif txn_type == "ATM" and txn_sign == "debit":
                txn["Payee"] = "ATM Withdrawal"

            elif txn_type == "ATM" and txn_sign == "credit":
                txn["Payee"] = "ATM Deposit"

            elif txn_type == "POS" and txn_sign == "debit":
                txn["Payee"] = "Point of Sale Payment"

            elif txn_type == "POS" and txn_sign == "credit":
                txn["Payee"] = "Point of Sale Credit"

            elif txn_memo != "UNKNOWN":
                txn["Payee"] = txn_memo

            # Down here, we have no payee, no memo, no check number,
            # and no type.  Who knows what this stuff is.
            elif txn_type == "UNKNOWN" and txn_sign == "debit":
                txn["Payee"] = "Other Debit"
                txn["Type"]  = "DEBIT"

            elif txn_type == "UNKNOWN" and txn_sign == "credit":
                txn["Payee"] = "Other Credit"
                txn["Type"]  = "CREDIT"

        # Make sure the transaction type has some valid value.
        if not txn.has_key("Type") and txn_sign == "debit":
            txn["Type"] = "DEBIT"

        elif not txn.has_key("Type") and txn_sign == "credit":
            txn["Type"] = "CREDIT"

    def _txn_sign(self, txn_amount):
        # Is this a credit or a debit?
        if txn_amount.startswith("-"):
            return "debit"
        else:
            return "credit"

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
        response = ofx.Response(ofx102) #, debug=self.debug)

        if self.debug: sys.stderr.write("Making OFX/2.0.\n")
        if self.dayfirst:
            date_format = "DD/MM/YY"
        else:
            date_format = "MM/DD/YY"
        xml = response.as_xml(original_format="QIF", date_format=date_format)

        return xml


