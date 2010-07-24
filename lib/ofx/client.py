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
# ofx.client - user agent for sending OFX requests and checking responses.
#

import ofx
import urllib2

class Client:
    """Network client for communicating with OFX servers.  The client
    handles forming a valid OFX request document, transmiting that
    request to the named OFX server, parsing the server's response for
    error flags and throwing errors as exceptions, and returning the
    requested OFX document if the request was successful."""

    def __init__(self):
        """Constructs the Client object.  No configuration options
        are offered."""
        # FIXME: Need to let the client set itself for OFX 1.02 or OFX 2.0 formatting.
        self.request_msg = None

    def get_fi_profile(self, institution,
                       username="anonymous00000000000000000000000",
                       password="anonymous00000000000000000000000"):
        request = ofx.Request()
        self.request_msg = request.fi_profile(institution, username, password)
        return self._send_request(institution.ofx_url, self.request_msg)

    def get_account_info(self, institution, username, password):
        request = ofx.Request()
        self.request_msg = request.account_info(institution, username, password)
        return self._send_request(institution.ofx_url, self.request_msg)

    def get_statement(self, account, username, password):
        acct_type = account.get_ofx_accttype()
        if acct_type == "CREDITCARD":
            return self.get_creditcard_statement(account, username, password)
        elif acct_type == "CHECKING" or acct_type == "SAVINGS" \
        or acct_type == "MONEYMRKT" or acct_type == "MONEYMARKT" or acct_type == "CREDITLINE":
            return self.get_bank_statement(account, username, password)
        else:
            raise ValueError("Unknown account type '%s'." % acct_type)

    def get_bank_statement(self, account, username, password):
        """Sends an OFX request for the given user's bank account
        statement, and returns that statement as an OFX document if
        the request is successful."""
        request = ofx.Request()
        # I'm breaking out these retries by statement type since I'm assuming that bank,
        # credit card, and investment OFX servers may each have different behaviors.
        try:
            # First, try to get a statement for the full year.  The USAA and American Express
            # OFX servers return a valid statement, although USAA only includes 90 days and
            # American Express seems to only include back to the first of the year.
            self.request_msg = request.bank_stmt(account, username, password, daysago=365)
            return self._send_request(account.institution.ofx_url, self.request_msg)
        except ofx.Error, detail:
            try:
                # If that didn't work, try 90 days back.
                self.request_msg = request.bank_stmt(account, username, password, daysago=90)
                return self._send_request(account.institution.ofx_url, self.request_msg)
            except ofx.Error, detail:
                # If that also didn't work, try 30 days back, which has been our default and
                # which always seems to work across all OFX servers.
                self.request_msg = request.bank_stmt(account, username, password, daysago=30)
                return self._send_request(account.institution.ofx_url, self.request_msg)

    def get_creditcard_statement(self, account, username, password):
        """Sends an OFX request for the given user's credit card
        statement, and returns that statement if the request is
        successful.  If the OFX server returns an error, the client
        will throw an OfxException indicating the error code and
        message."""
        # See comments in get_bank_statement, above, which explain these try/catch
        # blocks.
        request = ofx.Request()
        try:
            self.request_msg = request.creditcard_stmt(account, username, password, daysago=365)
            return self._send_request(account.institution.ofx_url, self.request_msg)
        except ofx.Error, detail:
            try:
                self.request_msg = request.creditcard_stmt(account, username, password, daysago=90)
                return self._send_request(account.institution.ofx_url, self.request_msg)
            except ofx.Error, detail:
                self.request_msg = request.creditcard_stmt(account, username, password, daysago=30)
                return self._send_request(account.institution.ofx_url, self.request_msg)

    def get_closing(self, account, username, password):
        # FIXME: Make sure this list only exists in one place and isn't duplicated here.
        acct_type = account.get_ofx_accttype()
        if acct_type == "CREDITCARD":
            return self.get_creditcard_closing(account, username, password)
        elif acct_type == "CHECKING" or acct_type == "SAVINGS" \
        or acct_type == "MONEYMRKT" or acct_type == "MONEYMARKT" or acct_type == "CREDITLINE":
            return self.get_bank_closing(account, username, password)
        else:
            raise ValueError("Unknown account type '%s'." % acct_type)

    def get_bank_closing(self, account, username, password):
        """Sends an OFX request for the given user's bank account
        statement, and returns that statement as an OFX document if
        the request is successful."""
        acct_type = account.get_ofx_accttype()
        request = ofx.Request()
        self.request_msg = request.bank_closing(account, username, password)
        return self._send_request(account.institution.ofx_url, self.request_msg)

    def get_creditcard_closing(self, account, username, password):
        """Sends an OFX request for the given user's credit card
        statement, and returns that statement if the request is
        successful.  If the OFX server returns an error, the client
        will throw an OfxException indicating the error code and
        message."""
        request = ofx.Request()
        self.request_msg = request.creditcard_closing(account, username, password)
        return self._send_request(account.institution.ofx_url, self.request_msg)

    def get_request_message(self):
        """Returns the last request message (or None if no request has been
        sent) for debugging purposes."""
        return self.request_msg

    def _send_request(self, url, request_body):
        """Transmits the message to the server and checks the response
        for error status."""

        request = urllib2.Request(url, request_body,
                                  { "Content-type": "application/x-ofx",
                                    "Accept": "*/*, application/x-ofx" })
        stream = urllib2.urlopen(request)
        response = stream.read()
        stream.close()

        response = ofx.Response(response)
        response.check_signon_status()

        parsed_ofx = response.as_dict()

        # FIXME: This needs to account for statement closing responses.

        if parsed_ofx.has_key("BANKMSGSRSV1"):
            bank_status = \
                parsed_ofx["BANKMSGSRSV1"]["STMTTRNRS"]["STATUS"]
            self._check_status(bank_status, "bank statement")

        elif parsed_ofx.has_key("CREDITCARDMSGSRSV1"):
            creditcard_status = \
                parsed_ofx["CREDITCARDMSGSRSV1"]["CCSTMTTRNRS"]["STATUS"]
            self._check_status(creditcard_status, "credit card statement")

        elif parsed_ofx.has_key("SIGNUPMSGSRSV1"):
            acctinfo_status = \
                parsed_ofx["SIGNUPMSGSRSV1"]["ACCTINFOTRNRS"]["STATUS"]
            self._check_status(acctinfo_status, "account information")

        return response

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

