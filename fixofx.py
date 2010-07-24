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
# fixofx.py - canonicalize all recognized upload formats to OFX 2.0
#

import os
import os.path
import sys

def fixpath(filename):
    mypath = os.path.dirname(sys._getframe(1).f_code.co_filename)
    return os.path.normpath(os.path.join(mypath, filename))

sys.path.insert(0, '../3rdparty')
sys.path.insert(0, '../lib')

import ofx
import ofxtools
from optparse import OptionParser
from pyparsing import ParseException

__doc__ = \
"""Canonicalizes files from several supported data upload formats (currently
OFX 1.02, OFX 1.5, OFX 1.6, OFX 2.0, OFC, and QIF) to OFX 2.0 (which is a
standard XML 1.0 file). Since it is easiest for the database loader to use a
single, XML-based format, and since users might prefer an XML document to OFX
1.02 or other formats for export, this script essentially removes the need for
any other code to know about all of the variations in data formats. By
default, the converter will read a single file of any supported format from
standard input and write the converted OFX 2.0 file to standard output. A
command line option also allows reading a single file, and other options allow
you to insert data into the output file not available in the source file (for
instance, QIF does not contain the account number, so an option allows you to
specify that for insertion into the OFX output)."""

# Import Psyco if available, for speed.
try:
    import psyco
    psyco.full()

except ImportError:
    pass


def convert(text, filetype, verbose=False, fid="UNKNOWN", org="UNKNOWN", 
            bankid="UNKNOWN", accttype="UNKNOWN", acctid="UNKNOWN",
            balance="UNKNOWN", curdef=None, lang="ENG", dayfirst=False, 
            debug=False):
    
    # This finishes a verbosity message started by the caller, where the
    # caller explains the source command-line option and this explains the
    # source format.
    if verbose: 
        sys.stderr.write("Converting from %s format.\n" % filetype)

    if options.debug and (filetype in ["OFC", "QIF"] or filetype.startswith("OFX")):
        sys.stderr.write("Starting work on raw text:\n")
        sys.stderr.write(rawtext + "\n\n")
    
    if filetype.startswith("OFX/2"):
        if verbose: sys.stderr.write("No conversion needed; returning unmodified.\n")
        
        # The file is already OFX 2 -- return it unaltered, ignoring
        # any of the parameters passed to this method.
        return text
    
    elif filetype.startswith("OFX"):
        if verbose: sys.stderr.write("Converting to OFX/2.0...\n")
        
        # This will throw a ParseException if it is unable to recognize
        # the source format.
        response = ofx.Response(text, debug=debug)        
        return response.as_xml(original_format=filetype)
    
    elif filetype == "OFC":
        if verbose: sys.stderr.write("Beginning OFC conversion...\n")
        converter = ofxtools.OfcConverter(text, fid=fid, org=org, curdef=curdef,
                                          lang=lang, debug=debug)
        
        # This will throw a ParseException if it is unable to recognize
        # the source format.
        if verbose: 
            sys.stderr.write("Converting to OFX/1.02...\n\n%s\n\n" %
                             converter.to_ofx102())
            sys.stderr.write("Converting to OFX/2.0...\n")
                                             
        return converter.to_xml()
    
    elif filetype == "QIF":
        if verbose: sys.stderr.write("Beginning QIF conversion...\n")
        converter = ofxtools.QifConverter(text, fid=fid, org=org,
                                          bankid=bankid, accttype=accttype, 
                                          acctid=acctid, balance=balance, 
                                          curdef=curdef, lang=lang, dayfirst=dayfirst,
                                          debug=debug)
        
        # This will throw a ParseException if it is unable to recognize
        # the source format.
        if verbose: 
            sys.stderr.write("Converting to OFX/1.02...\n\n%s\n\n" %
                             converter.to_ofx102())
            sys.stderr.write("Converting to OFX/2.0...\n")
                                             
        return converter.to_xml()
    
    else:
        raise TypeError("Unable to convert source format '%s'." % filetype)

parser = OptionParser(description=__doc__)
parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  default=False, help="spit out gobs of debugging output during parse")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  default=False, help="be more talkative, social, outgoing")
parser.add_option("-t", "--type", action="store_true", dest="type",
                  default=False, help="print input file type and exit")
parser.add_option("-f", "--file", dest="filename", default=None,
                  help="source file to convert (writes to STDOUT)")
parser.add_option("--fid", dest="fid", default="UNKNOWN",
                  help="(OFC/QIF only) FID to use in output")
parser.add_option("--org", dest="org", default="UNKNOWN",
                  help="(OFC/QIF only) ORG to use in output")
parser.add_option("--curdef", dest="curdef", default=None,
                  help="(OFC/QIF only) Currency identifier to use in output")
parser.add_option("--lang", dest="lang", default="ENG",
                  help="(OFC/QIF only) Language identifier to use in output")
parser.add_option("--bankid", dest="bankid", default="UNKNOWN",
                  help="(QIF only) Routing number to use in output")
parser.add_option("--accttype", dest="accttype", default="UNKNOWN",
                  help="(QIF only) Account type to use in output")
parser.add_option("--acctid", dest="acctid", default="UNKNOWN",
                  help="(QIF only) Account number to use in output")
parser.add_option("--balance", dest="balance", default="UNKNOWN",
                  help="(QIF only) Account balance to use in output")
parser.add_option("--dayfirst", action="store_true", dest="dayfirst", default=False,
                  help="(QIF only) Parse dates day first (UK format)")
(options, args) = parser.parse_args()

#
# Check the python environment for minimum sanity levels.
#

if options.verbose and not hasattr(open, 'newlines'):
    # Universal newlines are generally needed to deal with various QIF downloads.
    sys.stderr.write('Warning: universal newline support NOT available.\n')

if options.verbose: print "Options: %s" % options

#
# Load up the raw text to be converted.
#

rawtext = None

if options.filename:
    if os.path.isfile(options.filename):
        if options.verbose: 
            sys.stderr.write("Reading from '%s'\n." % options.filename)
        
        try:
            srcfile = open(options.filename, 'rU')
            rawtext = srcfile.read()
            srcfile.close()
        except StandardError, detail:
            print "Exception during file read:\n%s" % detail
            print "Exiting."
            sys.stderr.write("fixofx failed with error code 1\n")
            sys.exit(1)
        
    else:
        print "'%s' does not appear to be a file.  Try --help." % options.filename
        sys.stderr.write("fixofx failed with error code 2\n")
        sys.exit(2)

else:
    if options.verbose: 
        sys.stderr.write("Reading from standard input.\n")
    
    stdin_universal = os.fdopen(os.dup(sys.stdin.fileno()), "rU")
    rawtext = stdin_universal.read()
    
    if rawtext == "" or rawtext is None:
        print "No input.  Pipe a file to convert to the script,\n" + \
              "or call with -f.  Call with --help for more info."
        sys.stderr.write("fixofx failed with error code 3\n")
        sys.exit(3)

#
# Convert the raw text to OFX 2.0.
#

try:
    # Determine the type of file contained in 'text', using a quick guess
    # rather than parsing the file to make sure.  (Parsing will fail
    # below if the guess is wrong on OFX/1 and QIF.)
    filetype  = ofx.FileTyper(rawtext).trust()
    
    if options.type:
        print "Input file type is %s." % filetype
        sys.exit(0)
    elif options.debug:
        sys.stderr.write("Input file type is %s.\n" % filetype)
    
    converted = convert(rawtext, filetype, verbose=options.verbose, 
                        fid=options.fid, org=options.org, bankid=options.bankid, 
                        accttype=options.accttype, acctid=options.acctid, 
                        balance=options.balance, curdef=options.curdef,
                        lang=options.lang, dayfirst=options.dayfirst,
                        debug=options.debug)
    print converted
    sys.exit(0)

except ParseException, detail:
    print "Parse exception during '%s' conversion:\n%s" % (filetype, detail)
    print "Exiting."
    sys.stderr.write("fixofx failed with error code 4\n")
    sys.exit(4)

except TypeError, detail:
    print detail
    print "Exiting."
    sys.stderr.write("fixofx failed with error code 5\n")
    sys.exit(5)
