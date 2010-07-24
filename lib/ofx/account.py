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
# ofx.account - container for information about a bank or credit card account.
#

import ofx

class Account:
    def __init__(self, acct_type="", acct_number="", aba_number="",
                 balance=None, desc=None, institution=None, ofx_block=None):
        self.balance     = balance
        self.desc        = desc
        self.institution = institution

        if ofx_block is not None:
            self.acct_type   = self._get_from_ofx(ofx_block, "ACCTTYPE")
            self.acct_number = self._get_from_ofx(ofx_block, "ACCTID")
            self.aba_number  = self._get_from_ofx(ofx_block, "BANKID")
        else:
            self.acct_type   = acct_type
            self.acct_number = acct_number
            self.aba_number  = aba_number

    def _get_from_ofx(self, data, key):
        data_dict = data.asDict()
        return data_dict.get(key, "")

    def get_ofx_accttype(self):
        # FIXME: I nominate this for the stupidest method in the Uploader.

        # OFX requests need to have a the account type match one of a few
        # known types.  This converts from the "display" version of the
        # type to the one OFX servers will recognize.
        if self.acct_type == "Checking" or self.acct_type == "CHECKING":
            return "CHECKING"
        elif self.acct_type == "Savings" or self.acct_type == "SAVINGS":
            return "SAVINGS"
        elif self.acct_type == "Credit Card" or self.acct_type == "CREDITCARD":
            return "CREDITCARD"
        elif self.acct_type == "Money Market" or self.acct_type == "MONEYMRKT"\
        or self.acct_type == "MONEYMARKT":
            return "MONEYMRKT"
        elif self.acct_type == "Credit Line" or self.acct_type == "CREDITLINE":
            return "CREDITLINE"
        else:
            return self.acct_type

    def is_complete(self):
        if self.institution is None:
            return False
        elif self.acct_type != "" and self.acct_number != "":
            if self.get_ofx_accttype() == "CREDITCARD":
                return True
            else:
                return self.aba_number != ""
        else:
            return False

    def is_equal(self, other):
        if self.acct_type == other.acct_type   and \
        self.acct_number  == other.acct_number and \
        self.aba_number   == other.aba_number:
            return True
        else:
            return False

    def to_s(self):
        return ("Account: %s; Desc: %s; Type: %s; ABA: %s; Institution: %s") % \
                (self.acct_number, self.desc, self.acct_type,
                 self.aba_number, self.broker_id, self.institution)

    def __repr__(self):
        return self.to_s()

    def as_dict(self):
        acct_dict = { 'acct_number' : self.acct_number,
                      'acct_type'   : self.get_ofx_accttype(),
                      'aba_number'  : self.aba_number,
                      'balance'     : self.balance,
                      'desc'        : self.desc }
        if self.institution is not None:
            acct_dict['institution'] = self.institution.as_dict()
        return acct_dict

    def load_from_dict(acct_dict):
        return ofx.Account(acct_type=acct_dict.get('acct_type'),
                           acct_number=acct_dict.get('acct_number'),
                           aba_number=acct_dict.get('aba_number'),
                           balance=acct_dict.get('balance'),
                           desc=acct_dict.get('desc'))
    load_from_dict = staticmethod(load_from_dict)


