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
# ofx.request - build an OFX request document
#

from ofx.builder import *
import datetime
import uuid

class Request:
    def __init__(self, cookie=4, app_name="Money", app_version="1400"):
        # Note that American Express, at least, requires the app name
        # to be titlecase, and not all uppercase, for the request to
        # succeed.  Memories of Mozilla....
        self.app_name    = app_name
        self.app_version = app_version
        self.cookie      = cookie # FIXME: find out the meaning of this magic value.  Why not 3 or 5?
        self.request_id  = str(uuid.uuid4()).upper()
    
    def _format_date(self, date=None, datetime=datetime.datetime.now()):
        if date == None:
            return datetime.strftime("%Y%m%d%H%M%S")
        else:
            return date.strftime("%Y%m%d")
    
    def _message(self, institution, username, password, body):
        """Composes a complete OFX message document."""
        return DOCUMENT(self._header(),
                   OFX(self._sign_on(institution, username, password),
                       body))
    
    def _header(self):
        """Formats an OFX message header."""
        return HEADER(
            OFXHEADER("100"),
            DATA("OFXSGML"),
            VERSION("102"),
            SECURITY("NONE"),
            ENCODING("USASCII"),
            CHARSET("1252"),
            COMPRESSION("NONE"),
            OLDFILEUID("NONE"),
            NEWFILEUID(self.request_id))
    
    def _sign_on(self, institution, username, password):
        """Formats an OFX sign-on block."""
        return SIGNONMSGSRQV1(
            SONRQ(
                DTCLIENT(self._format_date()),
                USERID(username),
                USERPASS(password),
                LANGUAGE("ENG"),
                FI(
                    ORG(institution.ofx_org),
                    FID(institution.ofx_fid)),
                APPID(self.app_name),
                APPVER(self.app_version)))
    
    def fi_profile(self, institution, username, password):
        return self._message(institution, username, password,
            PROFMSGSRQV1(
                PROFTRNRQ(
                    TRNUID(self.request_id),
                    CLTCOOKIE(self.cookie),
                    PROFRQ(
                        CLIENTROUTING("NONE"),
                        DTPROFUP("19980101")))))
    
    def account_info(self, institution, username, password):
        """Returns a complete OFX account information request document."""
        return self._message(institution, username, password,
            SIGNUPMSGSRQV1(
                ACCTINFOTRNRQ(
                    TRNUID(self.request_id),
                    CLTCOOKIE(self.cookie),
                    ACCTINFORQ(
                        DTACCTUP("19980101")))))
    
    def bank_stmt(self, account, username, password, daysago=90):
        """Returns a complete OFX bank statement request document."""
        dt_start = datetime.datetime.now() - datetime.timedelta(days=daysago)
        return self._message(account.institution, username, password,
            BANKMSGSRQV1(
                STMTTRNRQ(
                    TRNUID(self.request_id),
                    CLTCOOKIE(self.cookie),
                    STMTRQ(
                        BANKACCTFROM(
                            BANKID(account.aba_number),
                            ACCTID(account.acct_number),
                            ACCTTYPE(account.get_ofx_accttype())),
                        INCTRAN(
                            DTSTART(self._format_date(date=dt_start)),
                            INCLUDE("Y"))))))
    
    def bank_closing(self, account, username, password):
        """Returns a complete OFX bank closing information request document."""
        return self._message(account.institution, username, password,
            BANKMSGSRQV1(
                STMTENDTRNRQ(
                    TRNUID(self.request_id),
                    CLTCOOKIE(self.cookie),
                    STMTENDRQ(
                        BANKACCTFROM(
                            BANKID(account.aba_number),
                            ACCTID(account.acct_number),
                            ACCTTYPE(account.get_ofx_accttype()))))))
    
    def creditcard_stmt(self, account, username, password, daysago=90):
        """Returns a complete OFX credit card statement request document."""
        dt_start = datetime.datetime.now() - datetime.timedelta(days=daysago)
        return self._message(account.institution, username, password,
            CREDITCARDMSGSRQV1(
                CCSTMTTRNRQ(
                    TRNUID(self.request_id),
                    CLTCOOKIE(self.cookie),
                    CCSTMTRQ(
                        CCACCTFROM(
                            ACCTID(account.acct_number)),
                        INCTRAN(
                            DTSTART(self._format_date(date=dt_start)),
                            INCLUDE("Y"))))))
    
    def creditcard_closing(self, account, username, password):
        """Returns a complete OFX credit card closing information request document."""
        dt_start = datetime.datetime.now() - datetime.timedelta(days=61)
        dt_end   = datetime.datetime.now() - datetime.timedelta(days=31)
        return self._message(account.institution, username, password,
            CREDITCARDMSGSRQV1(
                CCSTMTENDTRNRQ(
                    TRNUID(self.request_id),
                    CLTCOOKIE(self.cookie),
                    CCSTMTENDRQ(
                        CCACCTFROM(
                            ACCTID(account.acct_number)),
                        DTSTART(self._format_date(date=dt_end)),
                        DTEND(self._format_date(date=dt_end))))))
        
    
