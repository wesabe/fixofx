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
#  ofx.response - access to contents of an OFX response document.
#

import ofx

class Response(ofx.Document):
    def __init__(self, response, debug=False):
        # Bank of America (California) seems to be putting out bad Content-type
        # headers on manual OFX download.  I'm special-casing this out since
        # B of A is such a large bank.
        # REVIEW: Check later to see if this is still needed, espcially once
        # B of A is mechanized.
        # REVIEW: Checked.  Still needed.  Feh!
        self.raw_response = response.replace('Content- type:application/ofx', "")
        
        # Good god, another one.  Regex?
        self.raw_response = self.raw_response.replace('Content-Type: application/x-ofx', "")
        
        # I'm seeing this a lot, so here's an ugly workaround.  I wonder why multiple
        # FIs are causing it, though.
        self.raw_response = self.raw_response.replace('****OFX download terminated due to exception: Null or zero length FITID****', '')
        
        parser = ofx.Parser(debug)
        self.parse_dict = parser.parse(self.raw_response)
        self.ofx = self.parse_dict["body"]["OFX"].asDict()
    
    def as_dict(self):
        return self.ofx
    
    def as_string(self):
        return self.raw_response
    
    def get_encoding(self):
        return self.parse_dict["header"]["ENCODING"]
    
    def get_statements(self):
        # This allows us to parse out all statements from an OFX file
        # that contains multiple statements.
        
        # FIXME: I'm not positive this is legitimate.  Are there tagsets
        # a bank might use inside a bank or creditcard response *other*
        # than statements?  I bet there are.
        statements = []
        for tag in self.ofx.keys():
            if tag == "BANKMSGSRSV1" or tag == "CREDITCARDMSGSRSV1":
                for sub_tag in self.ofx[tag]:
                    statements.append(ofx.Statement(sub_tag))
        return statements
    
    def get_accounts(self):
        accounts = []
        for tag in self.ofx.keys():
            if tag == "SIGNUPMSGSRSV1":
                signup = self.ofx[tag].asDict()
                for signup_tag in signup:
                    if signup_tag == "ACCTINFOTRNRS":
                        accttrns = signup[signup_tag].asDict()
                        for accttrns_tag in accttrns:
                            if accttrns_tag == "ACCTINFORS":
                                acctrs = accttrns[accttrns_tag]
                                for acct in acctrs:
                                    if acct[0] == "ACCTINFO":
                                        account = self._extract_account(acct)
                                        if account is not None:
                                            accounts.append(account)
        return accounts
    
    def _extract_account(self, acct_block):
        acct_dict = acct_block.asDict()
        
        if acct_dict.has_key("DESC"):
            desc = acct_dict["DESC"]
        else:
            desc = None
        
        if acct_dict.has_key("BANKACCTINFO"):
            acctinfo = acct_dict["BANKACCTINFO"]
            return ofx.Account(ofx_block=acctinfo["BANKACCTFROM"], desc=desc)
        
        elif acct_dict.has_key("CCACCTINFO"):
            acctinfo = acct_dict["CCACCTINFO"]
            account = ofx.Account(ofx_block=acctinfo["CCACCTFROM"], desc=desc)
            account.acct_type = "CREDITCARD"
            return account
        
        else:
            return None
    
    def check_signon_status(self):
        status = self.ofx["SIGNONMSGSRSV1"]["SONRS"]["STATUS"]
        # This will throw an ofx.Error if the signon did not succeed.
        self._check_status(status, "signon")
        # If no exception was thrown, the signon succeeded.
        return True
    
    def _check_status(self, status_block, description):
        # Convert the PyParsing result object into a dictionary so we can
        # provide default values if the status values don't exist in the
        # response.
        status = status_block.asDict()
        
        # There is no OFX status code "-1," so I'm using that code as a
        # marker for "No status code was returned."
        code = status.get("CODE", "-1")
        
        # Code "0" is "Success"; code "1" is "data is up-to-date."  Anything
        # else represents an error.
        if code is not "0" and code is not "1":
            # Try to find information about the error.  If the bank didn't
            # provide status information, return the value "NONE," which
            # should be both clear to a user and a marker of a lack of
            # information from the bank.
            severity = status.get("SEVERITY", "NONE")
            message  = status.get("MESSAGE", "NONE")
            
            # The "description" allows the code to give some indication
            # of where the error originated (for instance, the kind of
            # account we were trying to download when the error occurred).
            error = ofx.Error(description, code, severity, message)
            raise error
    

class Statement(ofx.Document):
    def __init__(self, statement):
        self.parse_result = statement
        self.parse_dict = self.parse_result.asDict()
        
        if self.parse_dict.has_key("STMTRS"):
            stmt = self.parse_dict["STMTRS"]
            self.account = ofx.Account(ofx_block=stmt["BANKACCTFROM"])
        elif self.parse_dict.has_key("CCSTMTRS"):
            stmt = self.parse_dict["CCSTMTRS"]
            self.account = ofx.Account(ofx_block=stmt["CCACCTFROM"])
            self.account.acct_type = "CREDITCARD"
        else:
            error = ValueError("Unknown statement type: %s." % statement)
            raise error
        
        self.currency   = self._get(stmt,                 "CURDEF")
        self.begin_date = self._get(stmt["BANKTRANLIST"], "DTSTART")
        self.end_date   = self._get(stmt["BANKTRANLIST"], "DTEND")
        self.balance    = self._get(stmt["LEDGERBAL"],    "BALAMT")
        self.bal_date   = self._get(stmt["LEDGERBAL"],    "DTASOF")
    
    def _get(self, data, key):
        data_dict = data.asDict()
        return data_dict.get(key, "NONE")
    
    def as_dict(self):
        return self.parse_dict
    
    def as_xml(self, indent=4):
        taglist = self.parse_result.asList()
        return self._format_xml(taglist, indent)
    
    def get_account(self):
        return self.account
    
    def get_currency(self):
        return self.currency
    
    def get_begin_date(self):
        return self.begin_date
    
    def get_end_date(self):
        return self.end_date
    
    def get_balance(self):
        return self.balance
    
    def get_balance_date(self):
        return self.bal_date
    
