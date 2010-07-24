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
#  ofx.builder - OFX document generator with focus on clean generation code.
#

"""
Builder of OFX message documents.  This module exposes a large set of
instances that are called as methods to generate an OFX document
component using the name of the instance.  Example usage:

    import ofx

    request = MESSAGE(
        HEADER(
            OFXHEADER("100"),
            DATA("OFXSGML"),
            VERSION("102"),
            SECURITY("NONE"),
            ENCODING("USASCII"),
            CHARSET("1252"),
            COMPRESSION("NONE"),
            OLDFILEUID("NONE"),
            NEWFILEUID("9B33CA3E-C237-4577-8F00-7AFB0B827B5E")),
        OFX(
            SIGNONMSGSRQV1(),
            # ... other OFX message components here ...
"""

# FIXME: This supports OFX 1.02.  Make something that supports OFX 2.0.

# REVIEW: This class is pretty hackish, and it's not easy to maintain
# (you have to add new tags in a few different places). However, it works,
# and it has a reasonable test suite, so I'm leaving it alone for now.
# I do need to have a way of generating OFX 2.0, and that will probably
# be the next major addition to the class.

class Tag:
    ofx1 = "OFX/1.0"
    ofx2 = "OFX/2.0"
    output = ofx1

    def _output_version(cls, version=ofx1):
        cls.output = version

    def __init__(self, tag, aggregate=False, header=False, encoding=False,
    header_block=False, payload_block=False, message_block=False, document_type=None):
        """Builds an OfxTag instance to be called by the name of
        the tag it represents.  For instance, to make an "APPID" tag,
        create the tag object with 'APPID = Tag("APPID")', and
        then use the instance as a method: 'APPID("MONEY")'."""
        self.tag           = tag
        self.aggregate     = aggregate
        self.header        = header
        self.encoding      = encoding
        self.header_block  = header_block
        self.message_block = message_block
        self.payload_block = payload_block
        self.document_type = document_type

    def __call__(self, *values, **params):
        """Invoked when an OfxTag instance is invoked as a method
        call (see constructor documentation for an example).  The
        instance will return a string using its tag as a marker,
        with the arguments to the call used as the value of the tag."""
        if self.document_type is not None:
            self._output_version(self.document_type)

        elif self.message_block:
            # For consistency, we use an empty join to put together
            # parts of an OFX message in a "message block" tag.
            return ''.join(values)

        elif self.header_block:
            if self.output == "ofx2":
                return "<?OFX " + ' '.join(values) + " ?>\r\n"
            else:
                # The header block takes all the headers and adds an
                # extra newline to signal the end of the block.
                return ''.join(values) + "\r\n"

        elif self.payload_block:
            # This is really a hack, to make sure that the OFX
            # tag generation doesn't end with a newline.  Hmm...
            return "<" + self.tag + ">" + "\r\n" + ''.join(values) \
                + "</" + self.tag + ">"

        elif self.header:
            # This is an individual name/value pair in the header.
            return self.tag + ":" + ''.join(values) + "\r\n"

        elif self.aggregate:
            return "<" + self.tag + ">" + "\r\n" + ''.join(values) \
                + "</" + self.tag + ">" + "\r\n"

        else:
            if values is None: return ""
            values = [str(x) for x in values]
            if values == "": return ""
            return "<" + self.tag + ">" + ''.join(values) + "\r\n"

# The following is really dumb and hackish.  Is there any way to know the
# name of the variable called when __call__ is invoked?  I guess that
# wouldn't help since we have no way of using closures to make a real
# builder.  :(

# This list of variable names is needed to avoid importing the unit test
# suite into any file that uses ofxbuilder.  Any new tags added below should
# also be added here, unfortunately.
__all__ = ['ACCTID', 'ACCTINFORQ', 'ACCTINFOTRNRQ', 'ACCTTYPE', 'APPID',
'APPVER', 'AVAILBAL', 'BALAMT', 'BANKACCTFROM', 'BANKID', 'BANKMSGSRQV1',
'BANKMSGSRSV1', 'BANKTRANLIST', 'BROKERID', 'CCACCTFROM', 'CCSTMTENDRQ',
'CCSTMTENDTRNRQ', 'CCSTMTRQ', 'CCSTMTRS', 'CCSTMTTRNRQ', 'CCSTMTTRNRS',
'CHARSET', 'CHECKNUM', 'CLIENTROUTING', 'CLTCOOKIE', 'CODE', 'COMPRESSION',
'CREDITCARDMSGSRQV1', 'CREDITCARDMSGSRSV1', 'CURDEF', 'DATA', 'DOCUMENT',
'DTACCTUP', 'DTASOF', 'DTCLIENT', 'DTEND', 'DTPOSTED', 'DTPROFUP', 'DTSERVER',
'DTSTART', 'ENCODING', 'FI', 'FID', 'FITID', 'HEADER', 'INCBAL', 'INCLUDE',
'INCOO', 'INCPOS', 'INCTRAN', 'INVACCTFROM', 'INVSTMTMSGSRQV1', 'INVSTMTRQ',
'INVSTMTTRNRQ', 'LANGUAGE', 'LEDGERBAL', 'MEMO', 'MESSAGE', 'NAME',
'NEWFILEUID', 'OFX', 'OFXHEADER', 'OFX1', 'OFX2', 'OLDFILEUID', 'ORG',
'PROFMSGSRQV1', 'PROFRQ', 'PROFTRNRQ', 'SECURITY', 'SEVERITY',
'SIGNONMSGSRQV1', 'SIGNONMSGSRSV1', 'SIGNUPMSGSRQV1', 'SONRQ', 'SONRS',
'STATUS', 'STMTENDRQ', 'STMTENDTRNRQ', 'STMTRQ', 'STMTTRN', 'STMTRS',
'STMTTRNRQ', 'STMTTRNRS', 'TRNAMT', 'TRNTYPE', 'TRNUID', 'USERID', 'USERPASS',
'VERSION']

# FIXME: Can I add a bunch of fields to the module with a loop?

ACCTID             = Tag("ACCTID")
ACCTINFORQ         = Tag("ACCTINFORQ", aggregate=True)
ACCTINFOTRNRQ      = Tag("ACCTINFOTRNRQ", aggregate=True)
ACCTTYPE           = Tag("ACCTTYPE")
APPID              = Tag("APPID")
APPVER             = Tag("APPVER")
AVAILBAL           = Tag("AVAILBAL", aggregate=True)
BALAMT             = Tag("BALAMT")
BANKACCTFROM       = Tag("BANKACCTFROM", aggregate=True)
BANKID             = Tag("BANKID")
BANKMSGSRQV1       = Tag("BANKMSGSRQV1", aggregate=True)
BANKMSGSRSV1       = Tag("BANKMSGSRSV1", aggregate=True)
BANKTRANLIST       = Tag("BANKTRANLIST", aggregate=True)
BROKERID           = Tag("BROKERID")
CCACCTFROM         = Tag("CCACCTFROM", aggregate=True)
CCSTMTENDRQ        = Tag("CCSTMTENDRQ", aggregate=True)
CCSTMTENDTRNRQ     = Tag("CCSTMTENDTRNRQ", aggregate=True)
CCSTMTRQ           = Tag("CCSTMTRQ", aggregate=True)
CCSTMTRS           = Tag("CCSTMTRS", aggregate=True)
CCSTMTTRNRQ        = Tag("CCSTMTTRNRQ", aggregate=True)
CCSTMTTRNRS        = Tag("CCSTMTTRNRS", aggregate=True)
CHARSET            = Tag("CHARSET", header=True)
CHECKNUM           = Tag("CHECKNUM")
CLIENTROUTING      = Tag("CLIENTROUTING")
CLTCOOKIE          = Tag("CLTCOOKIE")
CODE               = Tag("CODE")
COMPRESSION        = Tag("COMPRESSION", header=True)
CREDITCARDMSGSRQV1 = Tag("CREDITCARDMSGSRQV1", aggregate=True)
CREDITCARDMSGSRSV1 = Tag("CREDITCARDMSGSRSV1", aggregate=True)
CURDEF             = Tag("CURDEF")
DATA               = Tag("DATA", header=True)
DOCUMENT           = Tag("", message_block=True)
DTACCTUP           = Tag("DTACCTUP")
DTASOF             = Tag("DTASOF")
DTCLIENT           = Tag("DTCLIENT")
DTEND              = Tag("DTEND")
DTPOSTED           = Tag("DTPOSTED")
DTPROFUP           = Tag("DTPROFUP")
DTSERVER           = Tag("DTSERVER")
DTSTART            = Tag("DTSTART")
ENCODING           = Tag("ENCODING", header=True)
FI                 = Tag("FI", aggregate=True)
FID                = Tag("FID")
FITID              = Tag("FITID")
HEADER             = Tag("", header_block=True)
INCBAL             = Tag("INCBAL")
INCLUDE            = Tag("INCLUDE")
INCOO              = Tag("INCOO")
INCPOS             = Tag("INCPOS", aggregate=True)
INCTRAN            = Tag("INCTRAN", aggregate=True)
INVACCTFROM        = Tag("INVACCTFROM", aggregate=True)
INVSTMTMSGSRQV1    = Tag("INVSTMTMSGSRQV1", aggregate=True)
INVSTMTRQ          = Tag("INVSTMTRQ", aggregate=True)
INVSTMTTRNRQ       = Tag("INVSTMTTRNRQ", aggregate=True)
LANGUAGE           = Tag("LANGUAGE")
LEDGERBAL          = Tag("LEDGERBAL", aggregate=True)
MEMO               = Tag("MEMO")
MESSAGE            = Tag("MESSAGE")
NAME               = Tag("NAME")
NEWFILEUID         = Tag("NEWFILEUID", header=True)
OFX                = Tag("OFX", payload_block=True)
OFX1               = Tag("", document_type=Tag.ofx1)
OFX2               = Tag("", document_type=Tag.ofx2)
OFXHEADER          = Tag("OFXHEADER", header=True)
OLDFILEUID         = Tag("OLDFILEUID", header=True)
ORG                = Tag("ORG")
PROFMSGSRQV1       = Tag("PROFMSGSRQV1", aggregate=True)
PROFRQ             = Tag("PROFRQ", aggregate=True)
PROFTRNRQ          = Tag("PROFTRNRQ", aggregate=True)
SECURITY           = Tag("SECURITY", header=True)
SEVERITY           = Tag("SEVERITY")
SIGNONMSGSRQV1     = Tag("SIGNONMSGSRQV1", aggregate=True)
SIGNONMSGSRSV1     = Tag("SIGNONMSGSRSV1", aggregate=True)
SIGNUPMSGSRQV1     = Tag("SIGNUPMSGSRQV1", aggregate=True)
SONRQ              = Tag("SONRQ", aggregate=True)
SONRS              = Tag("SONRS", aggregate=True)
STATUS             = Tag("STATUS", aggregate=True)
STMTENDRQ          = Tag("STMTENDRQ", aggregate=True)
STMTENDTRNRQ       = Tag("STMTENDTRNRQ", aggregate=True)
STMTRQ             = Tag("STMTRQ", aggregate=True)
STMTRS             = Tag("STMTRS", aggregate=True)
STMTTRN            = Tag("STMTTRN", aggregate=True)
STMTTRNRQ          = Tag("STMTTRNRQ", aggregate=True)
STMTTRNRS          = Tag("STMTTRNRS", aggregate=True)
TRNAMT             = Tag("TRNAMT")
TRNTYPE            = Tag("TRNTYPE")
TRNUID             = Tag("TRNUID")
USERID             = Tag("USERID")
USERPASS           = Tag("USERPASS")
VERSION            = Tag("VERSION", header=True)
