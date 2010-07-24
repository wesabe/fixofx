#!/usr/bin/env python

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
# fakeofx.py - a quick and ugly hack to generate fake OFX for testing
#

import os
import os.path
import sys

def fixpath(filename):
    mypath = os.path.dirname(sys._getframe(1).f_code.co_filename)
    return os.path.normpath(os.path.join(mypath, filename))

sys.path.append(fixpath('lib'))
sys.path.append(fixpath('3rdparty'))

from datetime import date
from datetime import timedelta
import ofx
from optparse import OptionParser
import random

def generate_amt(base_amt):
    return random.uniform((base_amt * 0.6), (base_amt * 1.4))

# How long should this statement be?

days = 90
end_date = date.today()

# How much spending should the statement represent?

income = 85000
take_home_pay = income * .6
paycheck_amt = "%.02f" % (take_home_pay / 26)
daily_income = take_home_pay / 365

# Assume that people spend their whole income.  At least.

total_spending = daily_income * days

# How do people usually spend their money?  Taken from
# http://www.billshrink.com/blog/consumer-income-spending/
# The fees number is made up, but seemed appropriate.

spending_pcts = \
    { "food":          0.101,
      "housing":       0.278,
      "utility":       0.056,
      "clothing":      0.031,
      "auto":          0.144,
      "health":        0.047,
      "entertainment": 0.044,
      "gift":         0.020,
      "education":     0.016,
      "fee":           0.026 }

# How much do people spend per transaction?  This is taken from
# the tag_summaries table in the live database.

avg_txn_amts = \
    { "auto":          -70.77,
      "clothing":      -58.31,
      "education":     -62.64,
      "entertainment": -30.10,
      "fee":           -20.95,
      "food":          -25.52,
      "gift":          -18.84,
      "health":        -73.05,
      "mortgage":      -1168.49,
      "rent":          -643.30,
      "utility":       -90.81 }

# For now, just throw in some merchant names for each tag. Later
# this should come from the merchant_summaries table.

top_merchants = \
    { "auto":          ["Chevron", "Jiffy Lube", "Union 76", "Arco", "Shell", "Pep Boys"],
      "clothing":      ["Nordstrom", "Banana Republic", "Macy's", "The Gap", "Kenneth Cole", "J. Crew"],
      "education":     ["Tuition", "Amazon.com", "Registration", "The Crucible", "Campus Books"],
      "entertainment": ["AMC Theaters", "Amazon.com", "Netflix", "iTunes Music Store", "Rhapsody", "Metreon Theaters"],
      "fee":           ["Bank Fee", "Overlimit Fee", "Late Fee", "Interest Fee", "Monthly Fee", "Annual Fee"],
      "food":          ["Safeway", "Starbucks", "In-N-Out Burger", "Trader Joe's", "Whole Foods", "Olive Garden"],
      "gift":          ["Amazon.com", "Nordstrom", "Neiman-Marcus", "Apple Store", "K&L Wines"],
      "health":        ["Dr. Phillips", "Dr. Jackson", "Walgreen's", "Wal-Mart", "Dr. Roberts", "Dr. Martins"],
      "mortgage":      ["Mortgage Payment"],
      "rent":          ["Rent Payment"],
      "utility":       ["AT&T", "Verizon", "PG&E", "Comcast", "Brinks", ""] }

# Choose a random account type.
accttype = random.choice(['CHECKING', 'CREDITCARD'])

if accttype == "CREDITCARD":
    # Make up a random 16-digit credit card number with a standard prefix.
    acctid = "9789" + str(random.randint(000000000000, 999999999999))
    
    # Credit card statements don't use bankid.
    bankid = None
    
    # Make up a negative balance.
    balance = "%.02f" % generate_amt(-5000)
    
else:
    # Make up a random 8-digit account number.
    acctid = random.randint(10000000, 99999999)
    
    # Use a fake bankid so it's easy to find fake OFX uploads.
    bankid = "987987987"
    
    # Make up a positive balance.
    balance = "%.02f" % generate_amt(1000)

def generate_transaction(stmt, tag, type, date=None):
    if date is None:
        days_ago = timedelta(days=random.randint(0, days))
        date = (end_date - days_ago).strftime("%Y%m%d")
    
    amount = generate_amt(avg_txn_amts[tag])
    txn_amt = "%.02f" % amount
    
    merchant = random.choice(top_merchants[tag])
    
    stmt.add_transaction(date=date, amount=txn_amt, payee=merchant, type=type)
    return amount


stmt = ofx.Generator(fid="9789789", org="FAKEOFX", acctid=acctid, accttype=accttype, 
                     bankid=bankid, availbal=balance, ledgerbal=balance)

tags = spending_pcts.keys()
tags.remove("housing")

if accttype == "CREDITCARD":
    # Add credit card payments

    payment_days_ago = 0

    while payment_days_ago < days:
        payment_days_ago += 30
        payment_amt = "%.02f" % generate_amt(1000)
        paymentday = (end_date - timedelta(days=payment_days_ago)).strftime("%Y%m%d")
        stmt.add_transaction(date=paymentday, amount=payment_amt, payee="Credit Card Payment", type="PAYMENT")
    
elif accttype == "CHECKING":
    # First deal with income

    pay_days_ago = 0

    while pay_days_ago < days:
        pay_days_ago += 15
        payday = (end_date - timedelta(days=pay_days_ago)).strftime("%Y%m%d")
        stmt.add_transaction(date=payday, amount=paycheck_amt, payee="Payroll", type="DEP")

    # Then deal with housing

    housing_tag = random.choice(["rent", "mortgage"])

    housing_days_ago = 0

    while housing_days_ago < days:
        housing_days_ago += 30
        last_housing = (end_date - timedelta(days=housing_days_ago)).strftime("%Y%m%d")
        amount = generate_transaction(stmt, housing_tag, "DEBIT")
        total_spending -= abs(amount)

# Now deal with the rest of the tags

for tag in tags:
    tag_spending = total_spending * spending_pcts[tag]
    while tag_spending > 0 and total_spending > 0:
        amount = generate_transaction(stmt, tag, "DEBIT")
        tag_spending   -= abs(amount)
        total_spending -= abs(amount)

print stmt
