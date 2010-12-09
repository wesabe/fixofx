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
#  ofx.QifParser - comprehend the mess that is QIF.
#

import ofxtools
from pyparsing import CaselessLiteral, Group, LineEnd, Literal, \
    MatchFirst, oneOf, OneOrMore, Optional, Or, restOfLine, SkipTo, \
    White, Word, ZeroOrMore

class QifParser:
    def __init__(self, debug=False):
        account_items       = { 'N' : "Name",
                                'T' : "AccountType",
                                'D' : "Description",
                                'L' : "CreditLimit",
                                'X' : "UnknownField",
                                'B' : "Balance",
                                '/' : "BalanceDate",
                                '$' : "Balance" }
        
        noninvestment_items = { 'D' : "Date",
                                'T' : "Amount",
                                'U' : "Amount2",
                                'C' : "Cleared",
                                'N' : "Number",
                                'P' : "Payee",
                                'M' : "Memo",
                                'L' : "Category",
                                'A' : "Address",
                                'S' : "SplitCategory",
                                'E' : "SplitMemo",
                                '$' : "SplitAmount",
                                '-' : "NegativeSplitAmount" }
        
        investment_items    = { 'D' : "Date",
                                'N' : "Action",
                                'Y' : "Security",
                                'I' : "Price",
                                'Q' : "Quantity",
                                'T' : "Amount",
                                'C' : "Cleared",
                                'P' : "Text",
                                'M' : "Memo",
                                'O' : "Commission",
                                'L' : "TransferAccount",
                                '$' : "TransferAmount" }
        
        category_items      = { 'N' : "Name",
                                'D' : "Description",
                                'T' : "TaxRelated",
                                'I' : "IncomeCategory",
                                'E' : "ExpenseCategory",
                                'B' : "BudgetAmount",
                                'R' : "TaxSchedule" }
        
        class_items         = { 'N' : "Name",
                                'D' : "Description" }
        
        options   = Group(CaselessLiteral('!Option:') + restOfLine).suppress()
        
        banktxns  = Group(CaselessLiteral('!Type:Bank').suppress() + 
                          ZeroOrMore(Or([self._items(noninvestment_items),
                                         options]))
                          ).setResultsName("BankTransactions")
        
        cashtxns  = Group(CaselessLiteral('!Type:Cash').suppress() + 
                          ZeroOrMore(Or([self._items(noninvestment_items),
                                         options]))
                          ).setResultsName("CashTransactions")
        
        ccardtxns = Group(Or([CaselessLiteral('!Type:CCard').suppress(),
                              CaselessLiteral('!Type!CCard').suppress()]) + 
                          ZeroOrMore(Or([self._items(noninvestment_items),
                                         options]))
                          ).setResultsName("CreditCardTransactions")
        
        liabilitytxns = Group(CaselessLiteral('!Type:Oth L').suppress() + 
                          ZeroOrMore(Or([self._items(noninvestment_items),
                                         options]))
                          ).setResultsName("CreditCardTransactions")
        
        invsttxns = Group(CaselessLiteral('!Type:Invst').suppress() + 
                          ZeroOrMore(self._items(investment_items))
                          ).setResultsName("InvestmentTransactions")
        
        acctlist  = Group(CaselessLiteral('!Account').suppress() +
                          ZeroOrMore(Or([self._items(account_items, name="AccountInfo")]))
                          ).setResultsName("AccountList")
        
        category  = Group(CaselessLiteral('!Type:Cat').suppress() +
                          ZeroOrMore(self._items(category_items))
                          ).setResultsName("CategoryList")
        
        classlist = Group(CaselessLiteral('!Type:Class').suppress() +
                          ZeroOrMore(self._items(category_items))
                          ).setResultsName("ClassList")
        
        self.parser = Group(ZeroOrMore(White()).suppress() +
                            ZeroOrMore(acctlist).suppress() +
                            OneOrMore(ccardtxns | cashtxns | banktxns | liabilitytxns | invsttxns) +
                            ZeroOrMore(White()).suppress()
                            ).setResultsName("QifStatement")
        
        if (debug):
            self.parser.setDebugActions(ofxtools._ofxtoolsStartDebugAction, 
                                        ofxtools._ofxtoolsSuccessDebugAction, 
                                        ofxtools._ofxtoolsExceptionDebugAction)
        
    
    def _items(self, items, name="Transaction"):
        item_list = []
        for (code, name) in items.iteritems():
            item = self._item(code, name)
            item_list.append(item)
        return Group(OneOrMore(Or(item_list)) +
                     oneOf('^EUR ^').setResultsName('Currency') +
                     LineEnd().suppress()
                     ).setResultsName(name)
    
    def _item(self, code, name):
        return CaselessLiteral(code).suppress() + \
               restOfLine.setResultsName(name) + \
               LineEnd().suppress()
    
    def parse(self, qif):
        return self.parser.parseString(qif)
    
