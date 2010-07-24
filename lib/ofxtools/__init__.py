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

# This code allows you to say in your scripts:
#
#   import ofxtools
#
# and have access to all of the classes in the OFX tools library.  Refer to
# them with the prefix 'ofxtools.' and the class name.  For instance, to
# use the QIF converter, use the name 'ofxtools.QifConverter'.

import sys

def _ofxtoolsStartDebugAction( instring, loc, expr ):
    sys.stderr.write("Match %s at loc %s (%d,%d)" % 
                    (expr, loc, 
                    instring.count("\n", 0, loc) + 1, 
                    loc - instring.rfind("\n", 0, loc)))

def _ofxtoolsSuccessDebugAction( instring, startloc, endloc, expr, toks ):
    sys.stderr.write("Matched %s -> %s" % (expr, str(toks.asList())))
    
def _ofxtoolsExceptionDebugAction( instring, loc, expr, exc ):
    sys.stderr.write("Exception raised: %s" % exc)

from ofxtools.ofc_converter import *
from ofxtools.ofc_parser import *
from ofxtools.qif_converter import *
from ofxtools.qif_parser import *
