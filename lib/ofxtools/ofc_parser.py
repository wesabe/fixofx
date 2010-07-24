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
#  ofxtools.ofc_parser - parser class for reading OFC documents.
#

import ofxtools
from pyparsing import alphanums, CharsNotIn, Dict, Forward, Group, \
Literal, OneOrMore, White, Word, ZeroOrMore

class OfcParser:
    """Dirt-simple OFC parser for interpreting OFC documents."""
    def __init__(self, debug=False):
        aggregate = Forward().setResultsName("OFC")
        aggregate_open_tag, aggregate_close_tag = self._tag()
        content_open_tag = self._tag(closed=False)
        content = Group(content_open_tag + CharsNotIn("<\r\n"))
        aggregate << Group(aggregate_open_tag \
            + Dict(OneOrMore(aggregate | content)) \
            + aggregate_close_tag)
        
        self.parser = Group(aggregate).setResultsName("document")
        if (debug):
            self.parser.setDebugActions(ofxtools._ofxtoolsStartDebugAction, 
                                        ofxtools._ofxtoolsSuccessDebugAction, 
                                        ofxtools._ofxtoolsExceptionDebugAction)
    
    def _tag(self, closed=True):
        """Generate parser definitions for OFX tags."""
        openTag = Literal("<").suppress() + Word(alphanums + ".") \
            + Literal(">").suppress()
        if (closed):
            closeTag = Group("</" + Word(alphanums + ".") + ">" + ZeroOrMore(White())).suppress()
            return openTag, closeTag
        else:
            return openTag
    
    def parse(self, ofc):
        """Parse a string argument and return a tree structure representing
        the parsed document."""
        return self.parser.parseString(ofc).asDict()
    

