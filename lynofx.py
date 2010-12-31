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
# lynofx.py - Issue OFX requests from the command line
# 

import getpass
import optparse
import os
import os.path
import sys
import urllib2

sys.path.insert(0, '3rdparty')
sys.path.insert(0, 'lib')

import ofx

VERSION = "%prog 1.0"

actions = ["profile", "accounts", "statement"]

__doc__ = \
"""Command-line client for making OFX requests and showing the responses that
come back. Use option flags to pass the OFX client parameters for the request,
and then specify the request type as the action. Each financial institution
has a set of parameters that are needed to make requests; those parameters are
not provided by this script but must be found elsewhere (for instance, see
http://wiki.gnucash.org/wiki/OFX_Direct_Connect_Bank_Settings). By default, the
response will be shown as a pretty-printed OFX/2.0 document, but the raw
response will be shown instead if the -r/--raw option is passed.

Possible actions are: 
`profile` - get a profile of this OFX server's capabilities. 
`accounts` - get a list of accounts for an authenticated user. 
`statement` - get a single account statement for an authenticated user.
"""

parser = optparse.OptionParser(usage="%prog [options] (profile|accounts|statement)", 
                               version=VERSION, description=__doc__)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  default=False, help="be more talkative, social, outgoing")
parser.add_option("-r", "--raw", action="store_true", dest="raw",
                  default=False, help="show raw response (don't pretty-print as OFX/2.0)")
parser.add_option("-f", "--fid", dest="fid",
                  help="OFX ID of the financial institution")
parser.add_option("-o", "--org", dest="org", 
                  help="OFX organization of the financial institution")
parser.add_option("-u", "--url", dest="url", 
                  help="OFX URL of the financial institution")
parser.add_option("-t", "--accttype", dest="accttype", 
                  help="type of the account")
parser.add_option("-i", "--acctid", dest="acctid", 
                  help="ID of the account (a.k.a. account number)")
parser.add_option("-b", "--bankid", dest="bankid", 
                  help="ID of the bank (a.k.a. routing number)")
(options, args) = parser.parse_args()

if len(args) != 1:
    print "Call lynofx.py with one and only one action (use --help for more info)."
    sys.exit(1)

action = args[0]  # just for clarity

if action not in actions:
    print "Unrecognized option '%s' (use --help for more info)." % action
    sys.exit(1)

if options.verbose:
    print "Using options:"
    print "  action:   %s" % action
    if options.fid:      print "  fid:      %s" % options.fid
    if options.org:      print "  org:      %s" % options.org
    if options.url:      print "  url:      %s" % options.url
    if options.accttype: print "  accttype: %s" % options.accttype
    if options.acctid:   print "  acctid:   %s" % options.acctid
    if options.bankid:   print "  bankid:   %s" % options.bankid
    print

# FIXME: should check to make sure all required options for this action were provided.

if action != "profile":
    # The following allows the username prompt to be written even if output is redirected.
    # On UNIX and Mac, that is. The sys.stdout fallback should work elsewhere, assuming
    # people on those other platforms aren't redirecting output like the UNIX-heads are.
    terminal = None
    if os.access("/dev/tty", os.W_OK):
        terminal = open("/dev/tty", 'w')
    else:
        terminal = sys.stdout
    terminal.write("Enter account username: ")
    username = sys.stdin.readline().rstrip()
    password = getpass.getpass("Enter account password: ")
    print

institution = ofx.Institution(ofx_org=options.org, 
                              ofx_url=options.url, 
                              ofx_fid=options.fid)

account     = ofx.Account(acct_type=options.accttype, 
                          acct_number=options.acctid, 
                          aba_number=options.bankid, 
                          institution=institution)

try:
    client   = ofx.Client(debug=options.verbose)
    response = None

    if options.verbose:
        # Install an HTTP handler with debug output
        http_handler  = urllib2.HTTPHandler(debuglevel=1)
        https_handler = urllib2.HTTPSHandler(debuglevel=1)
        opener = urllib2.build_opener(http_handler, https_handler)
        urllib2.install_opener(opener)
        
        print "HTTP Debug Output:"
        print "=================="
        print
    
    if action == "profile":
        response = client.get_fi_profile(institution)

    elif action == "accounts":
        response = client.get_account_info(institution, username, password)

    elif action == "statement":
        response = client.get_statement(account, username, password)
    
    if options.verbose:
        print
        print "Request Message:"
        print "================"
        print
        print client.get_request_message() 
        print
        print "Response Message:"
        print "================="
        print
    
    if options.raw:
        print response.as_string()
    else:
        print response.as_xml()

except ofx.Error, exception:
    if options.verbose:
        print
        print "Request Message:"
        print "================"
        print
        print client.get_request_message() 
        print
    
    sys.stderr.write("*** Server returned an OFX error:\n")
    sys.stderr.write(str(exception))
    sys.stderr.write("\n")
    sys.exit(3)

except urllib2.HTTPError, exception:
    if options.verbose:
        print
        print "Request Message:"
        print "================"
        print
        print client.get_request_message() 
        print
    
    sys.stderr.write("*** Server returned an HTTP error:\n")
    sys.stderr.write(str(exception))
    sys.stderr.write(str(exception.hdrs))
    sys.stderr.write(exception.fp.read())
    sys.stderr.write("\n")
    sys.exit(4)
    