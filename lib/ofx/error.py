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
# ofx.error - OFX error message exception 
# 


class Error(Exception):
    def __init__(self, summary, code=None, severity=None, message=None):
        self.summary  = summary
        self.code     = int(code)
        self.severity = severity
        self.msg      = message

        self.codetable = \
            { 0: "OK",
              1: "Client is up-to-date",
              2000: "General error",
              2001: "Invalid account",
              2002: "General account error",
              2003: "Account not found",
              2004: "Account closed",
              2005: "Account not authorized",
              2006: "Source account not found",
              2007: "Source account closed",
              2008: "Source account not authorized",
              2009: "Destination account not found",
              2010: "Destination account closed",
              2011: "Destination account not authorized",
              2012: "Invalid amount",
              # Don't know why 2013 is missing from spec (1.02)
              2014: "Date too soon",
              2015: "Date too far in the future",
              2016: "Already committed",
              2017: "Already cancelled",
              2018: "Unknown server ID",
              2019: "Duplicate request",
              2020: "Invalid date",
              2021: "Unsupported version",
              2022: "Invalid TAN",
              10000: "Stop check in process",
              10500: "Too many checks to process",
              10501: "Invalid payee",
              10502: "Invalid payee address",
              10503: "Invalid payee account number",
              10504: "Insufficient funds",
              10505: "Cannot modify element",
              10506: "Cannot modify source account",
              10507: "Cannot modify destination account",
              10508: "Invalid frequency", # "..., Kenneth"
              10509: "Model already cancelled",
              10510: "Invalid payee ID",
              10511: "Invalid payee city",
              10512: "Invalid payee state",
              10513: "Invalid payee postal code",
              10514: "Bank payment already processed",
              10515: "Payee not modifiable by client",
              10516: "Wire beneficiary invalid",
              10517: "Invalid payee name",
              10518: "Unknown model ID",
              10519: "Invalid payee list ID",
              12250: "Investment transaction download not supported",
              12251: "Investment position download not supported",
              12252: "Investment positions for specified date not available",
              12253: "Investment open order download not supoorted",
              12254: "Investment balances download not supported",
              12500: "One or more securities not found",
              13000: "User ID & password will be sent out-of-band",
              13500: "Unable to enroll user",
              13501: "User already enrolled",
              13502: "Invalid service",
              13503: "Cannot change user information",
              15000: "Must change USERPASS",
              15500: "Signon (for example, user ID or password) invalid",
              15501: "Customer account already in use",
              15502: "USERPASS lockout",
              15503: "Could not change USERPASS",
              15504: "Could not provide random data",
              16500: "HTML not allowed",
              16501: "Unknown mail To:",
              16502: "Invalid URL",
              16503: "Unable to get URL", }

    def interpret_code(self, code=None):
        if code is None:
            code = self.code
        
        if self.codetable.has_key(code):
            return self.codetable[code]
        else:
            return "Unknown error code"
    
    def str(self):
        format = "%s\n(%s %s: %s)"
        return format % (self.msg, self.severity, self.code,
                         self.interpret_code())

    def __str__(self):
        return self.str()

    def __repr__(self):
        return self.str()
