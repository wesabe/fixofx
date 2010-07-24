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
#  ofx.generator - build up an OFX statement from source data.
#

from datetime import date
import ofx
from ofx.builder import *
import uuid

class Generator:
    def __init__(self, fid="UNKNOWN", org="UNKNOWN", bankid="UNKNOWN",
                 accttype="UNKNOWN", acctid="UNKNOWN", availbal="0.00",
                 ledgerbal="0.00", stmtdate=None, curdef="USD", lang="ENG"):
        self.fid       = fid
        self.org       = org
        self.bankid    = bankid
        self.accttype  = accttype
        self.acctid    = acctid
        self.availbal  = availbal
        self.ledgerbal = ledgerbal
        self.stmtdate  = stmtdate
        self.curdef    = curdef
        self.lang      = lang
        self.txns_by_date = {}
    
    def add_transaction(self, date=None, amount=None, number=None, 
                        txid=None, type=None, payee=None, memo=None):
        txn = ofx.Transaction(date=date, amount=amount, number=number, 
                              txid=txid, type=type, payee=payee, memo=memo)
        txn_date_list = self.txns_by_date.get(txn.date, [])
        txn_date_list.append(txn)
        self.txns_by_date[txn.date] = txn_date_list
    
    def to_ofx1(self):
        # Sort transactions and fill in date information.
        # OFX transactions appear most recent first, and oldest last.
        self.date_list = self.txns_by_date.keys()
        self.date_list.sort()
        self.date_list.reverse()
        
        self.startdate = self.date_list[-1]
        self.enddate   = self.date_list[0] 
        if self.stmtdate is None:
            self.stmtdate = date.today().strftime("%Y%m%d")
        
        # Generate the OFX statement.
        return DOCUMENT(self._ofx_header(),
                        OFX(self._ofx_signon(),
                            self._ofx_stmt()))
    
    def to_str(self):
        return self.to_ofx1()
    
    def __str__(self):
        return self.to_ofx1()
    
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
                DTSERVER(self.stmtdate),
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
                        CURDEF(self.curdef),
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
                        CURDEF(self.curdef),
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
            BALAMT(self.ledgerbal),
            DTASOF(self.stmtdate))

    def _ofx_availbal(self):
        return AVAILBAL(
            BALAMT(self.availbal),
            DTASOF(self.stmtdate))

    def _ofx_txns(self):
        txns = ""
        
        for date in self.date_list:
            txn_list = self.txns_by_date[date]
            txn_index = len(txn_list)
            for txn in txn_list:
                txn_date = txn.date
                txn_amt  = txn.amount
        
                # Make a synthetic transaction ID using as many
                # uniqueness guarantors as possible.
                txn.txid = "%s-%s-%s-%s-%s" % (self.org, self.accttype,
                                                txn_date, txn_index,
                                                txn_amt)
                txns += txn.to_ofx()
                txn_index -= 1
        
        return BANKTRANLIST(
            DTSTART(self.startdate),
            DTEND(self.enddate),
            txns)
    
    
#
#  ofx.Transaction - clean and format transaction information.
#

class Transaction:
    def __init__(self, date="UNKNOWN", amount="0.00", number=None, 
                 txid=None, type="UNKNOWN", payee="UNKNOWN", memo=None):
        self.date     = date
        self.amount   = amount
        self.number   = number
        self.txid     = txid
        self.type     = type
        self.payee    = payee
        self.memo     = memo
    
    def to_ofx(self):
        fields = []
        
        if self.type is None:
            self.type = "DEBIT"
        
        fields.append(TRNTYPE(self.type))
        fields.append(DTPOSTED(self.date))
        fields.append(TRNAMT(self.amount))
        
        if self.number is not None:
            fields.append(CHECKNUM(self.number))
        
        if self.txid is None:
            self.txid = uuid.generate().upper()
        
        fields.append(FITID(self.txid))
        fields.append(NAME(self.payee))
        
        if self.memo is not None:
            fields.append(MEMO(self.memo))

        return STMTTRN(*fields)
    
