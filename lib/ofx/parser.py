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
#  ofx.parser - parser class for reading OFX documents.
#

import re
import sys
from pyparsing import alphanums, alphas, CharsNotIn, Dict, Forward, Group, \
Literal, OneOrMore, Optional, SkipTo, White, Word, ZeroOrMore

def _ofxStartDebugAction( instring, loc, expr ):
    sys.stderr.write("Match %s at loc %s (%d,%d)" % 
                    (expr, loc, 
                    instring.count("\n", 0, loc) + 1, 
                    loc - instring.rfind("\n", 0, loc)))

def _ofxSuccessDebugAction( instring, startloc, endloc, expr, toks ):
    sys.stderr.write("Matched %s -> %s" % (expr, str(toks.asList())))
    
def _ofxExceptionDebugAction( instring, loc, expr, exc ):
    sys.stderr.write("Exception raised: %s" % exc)
    
class Parser:
    """Dirt-simple OFX parser for interpreting server results (primarily for
    errors at this point).  Currently parses OFX 1.02."""
    def __init__(self, debug=False):
        # Parser definition for headers
        header = Group(Word(alphas) + Literal(":").suppress() +
            Optional(CharsNotIn("\r\n")))
        headers = Dict(OneOrMore(header)).setResultsName("header")
        
        # Parser definition for OFX body
        aggregate = Forward().setResultsName("OFX")
        aggregate_open_tag, aggregate_close_tag = self._tag()
        content_open_tag = self._tag(closed=False)
        content = Group(content_open_tag + CharsNotIn("<\r\n"))
        aggregate << Group(aggregate_open_tag \
            + Dict(ZeroOrMore(aggregate | content)) \
            + aggregate_close_tag)
        body = Group(aggregate).setResultsName("body")
        
        # The parser as a whole
        self.parser = headers + body
        if (debug):
            self.parser.setDebugActions(_ofxStartDebugAction, _ofxSuccessDebugAction, _ofxExceptionDebugAction)
    
    def _tag(self, closed=True):
        """Generate parser definitions for OFX tags."""
        openTag = Literal("<").suppress() + Word(alphanums + ".") \
            + Literal(">").suppress()
        if (closed):
            closeTag = Group("</" + Word(alphanums + ".") + ">" + ZeroOrMore(White())).suppress()
            return openTag, closeTag
        else:
            return openTag
    
    def parse(self, ofx):
        """Parse a string argument and return a tree structure representing
        the parsed document."""
        ofx = self.strip_empty_tags(ofx)
        ofx = self.strip_close_tags(ofx)
        ofx = self.strip_blank_dtasof(ofx)
        ofx = self.strip_junk_ascii(ofx)
        ofx = self.fix_unknown_account_type(ofx)
        return self.parser.parseString(ofx).asDict()
    
    def strip_empty_tags(self, ofx):
        """Strips open/close tags that have no content."""
        strip_search = '<(?P<tag>[^>]+)>\s*</(?P=tag)>'
        return re.sub(strip_search, '', ofx)

    def strip_close_tags(self, ofx):
        """Strips close tags on non-aggregate nodes.  Close tags seem to be
        valid OFX/1.x, but they screw up our parser definition and are optional.
        This allows me to keep using the same parser without having to re-write
        it from scratch just yet."""
        strip_search = '<(?P<tag>[^>]+)>\s*(?P<value>[^<\n\r]+)(?:\s*</(?P=tag)>)?(?P<lineend>[\n\r]*)'
        return re.sub(strip_search, '<\g<tag>>\g<value>\g<lineend>', ofx)
    
    def strip_blank_dtasof(self, ofx):
        """Strips empty dtasof tags from wells fargo/wachovia downloads.  Again, it would
        be better to just rewrite the parser, but for now this is a workaround."""
        blank_search = '<(DTASOF|BALAMT|BANKID|CATEGORY|NAME)>[\n\r]+'
        return re.sub(blank_search, '', ofx)
    
    def strip_junk_ascii(self, ofx):
        """Strips high ascii gibberish characters from Schwab statements. They seem to 
        contains strings of EF BF BD EF BF BD 0A 08 EF BF BD 64 EF BF BD in the <NAME> field, 
        and the newline is screwing up the parser."""
        return re.sub('[\xBD-\xFF\x64\x0A\x08]{4,}', '', ofx)

    def fix_unknown_account_type(self, ofx):
        """Sets the content of <ACCTTYPE> nodes without content to be UNKNOWN so that the
        parser is able to parse it. This isn't really the best solution, but it's a decent workaround."""
        return re.sub('<ACCTTYPE>(?P<contentend>[<\n\r])', '<ACCTTYPE>UNKNOWN\g<contentend>', ofx)

