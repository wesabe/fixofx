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
#  ofx.QifConverter - translate QIF files into OFX files.
#

import datetime
import dateutil.parser
import ofx
import ofxtools
import re
import sys
import xml.sax.saxutils as sax
from decimal import *
from time import localtime, strftime
from ofx.builder import *

class QifConverter:
    def __init__(self, qif, fid="UNKNOWN", org="UNKNOWN", bankid="UNKNOWN",
                 accttype="UNKNOWN", acctid="UNKNOWN", balance="UNKNOWN",
                 curdef=None, lang="ENG", dayfirst=False, debug=False):
        self.qif      = qif
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

        self.parsed_qif = None

        # FIXME: Move this to one of the OFX generation classes (Document or Response).
        self.txns_by_date = {}

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
                           "Checks"      : "CHECK",
                           "PAYMENT"     : "PAYMENT",
                           "CASH"        : "CASH",
                           "DIRECTDEP"   : "DIRECTDEP",
                           "DIRECTDEBIT" : "DIRECTDEBIT",
                           "REPEATPMT"   : "REPEATPMT",
                           "OTHER"       : "OTHER"        }

        # Some joker British bank starts QIF with a single bang and nothing
        # else.
        if re.match("!\n", self.qif) is not None:
            if self.debug: sys.stderr.write("Fixing typeless bang header.\n")
            self.qif = self.qif.replace("!", "!Type:Bank", 1)

        # Chase does not provide a Type header, so force one in the
        # case where it is omitted.
        if re.search("!Type:", self.qif, re.IGNORECASE) == None:
            if self.debug: sys.stderr.write("Forcing bank type header.\n")
            self.qif = "!Type:Bank\n" + self.qif

        acctblock = re.search("(!Account.*?\^\s*)", self.qif, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if acctblock is not None:
            block = acctblock.group(1)
            if self.debug:
                sys.stderr.write("Discarding account block from QIF file:\n%s" % block)
            self.qif = self.qif.replace(block, '', 1)

        # Some other personal finance program puts out a spurious transaction
        # showing current balance, but not as a balance -- instead as a
        # transaction before the type header.  And, there are a bunch of other
        # cases where crap before the type header is messing us up right now.
        # So, this is an awfully big hammer but one that at least lets people
        # import from other finance programs and broken banks.
        straycrap = re.search("^(.*?)!Type", self.qif, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if straycrap is not None:
            crap = straycrap.group(1)
            if len(crap) > 0:
              if self.debug:
                  sys.stderr.write("Discarding stray crap from beginning of QIF file:\n%s" % crap)
              self.qif = self.qif.replace(crap, '', 1)

        if self.debug: sys.stderr.write("Parsing document.\n")

        parser = ofxtools.QifParser(debug=debug)
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
            # Look for currency format.
            if self.curdef is None and txn_currency == '^EUR':
                self.curdef = 'EUR'

    def _parse_date(self, txn_date, dayfirst=False):
        # Try as best we can to parse the date into a datetime object. Note:
        # this assumes that we never see a timestamp, just the date, in any
        # QIF date.
        if txn_date != "UNKNOWN":
            try:
                return dateutil.parser.parse(txn_date, dayfirst=dayfirst)

            except ValueError:
                # dateutil.parser doesn't recognize dates of the
                # format "MMDDYYYY", though it does recognize
                # "MM/DD/YYYY".  So, if parsing has failed above,
                # try shoving in some slashes and see if that
                # parses.
                try:
                    if len(txn_date) == 8:
                        # The int() cast will only succeed if all 8
                        # characters of txn_date are numbers.  If
                        # it fails, it will throw an exception we
                        # can catch below.
                        date_int = int(txn_date)
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

        if len(txn_list) > 0:
            # Sort the dates (in YYYYMMDD format) and choose the lowest
            # date as our start date, and the highest date as our end
            # date.
            date_list = self.txns_by_date.keys()
            date_list.sort()

            self.start_date = date_list[0]
            self.end_date   = date_list[-1]

        else:
            # If we didn't get any transactions (which actually happens
            # quite a lot -- QIF statements are often just the type header,
            # presumably since there was no activity in the downloaded
            # statement), just assume that the start and end date were
            # both today.
            self.start_date = strftime("%Y%m%d", localtime())
            self.end_date   = self.start_date

    def _clean_txn(self, txn_obj):
        # This is sort of the brute-force method of the converter.  It
        # looks at the data we get from the bank and tries as hard as
        # possible to make best-effort guesses about what the OFX 2.0
        # standard values for the transaction should be.  There's a
        # reasonable amount of guesswork in here -- some of it wise,
        # maybe some of it not.  If the cleanup method determines that
        # the txn_obj shouldn't be in the data, it will throw a ValueError.
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
        # we're throwing a ValueError, which means this transaction should be removed
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

        # Some QIF files (usually from non-US banks) put the minus sign at
        # the end of the amount, rather than at the beginning. Let's fix that.
        if txn_amount[-1] == "-":
            txn_amount = "-" + txn_amount[:-1]

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
        txn_payee  = txn.get("Payee", "UNKNOWN").strip()

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

        elif txn_payee.startswith("CHECK # "):
            # USAA QIF export sends blank number fields but has the check
            # number in the payee field instead padded with leading zeros
            number = re.search("^CHECK # (\d+)", txn_payee)
            if number is not None:
                txn["Number"] = number.group(1).lstrip('0')

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


