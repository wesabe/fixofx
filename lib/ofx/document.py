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
#  ofx.document - abstract OFX document.
#

import ofx
import xml.sax.saxutils as sax

class Document:
    def as_xml(self, original_format=None, date_format=None):
        """Formats this document as an OFX 2.0 XML document."""
        xml = ""

        # NOTE: Encoding in OFX, particularly in OFX 1.02,
        # is kind of a mess.  The OFX 1.02 spec talks about "UNICODE"
        # as a supported encoding, which the OFX 2.0 spec has
        # back-rationalized to "UTF-8".  The "US-ASCII" encoding is
        # given as "USASCII".  Yet the 1.02 spec acknowledges that
        # not everyone speaks English nor uses UNICODE, so they let
        # you throw any old encoding in there you'd like.  I'm going
        # with the idea that if the most common encodings are named
        # in an OFX file, they should be translated to "real" XML
        # encodings, and if no encoding is given, UTF-8 (which is a
        # superset of US-ASCII) should be assumed; but if a named
        # encoding other than USASCII or 'UNICODE' is given, that
        # should be preserved.  I'm also adding a get_encoding()
        # method so that we can start to survey what encodings
        # we're actually seeing, and use that to maybe be smarter
        # about this in the future.
        encoding = ""
        if self.parse_dict["header"]["ENCODING"] == "USASCII":
            encoding = "US-ASCII"
        elif self.parse_dict["header"]["ENCODING"] == "UNICODE":
            encoding = "UTF-8"
        elif self.parse_dict["header"]["ENCODING"] == "NONE":
            encoding = "UTF-8"
        else:
            encoding = self.parse_dict["header"]["ENCODING"]

        xml += """<?xml version="1.0" encoding="%s"?>\n""" % encoding
        xml += """<?OFX OFXHEADER="200" VERSION="200" """ + \
               """SECURITY="%s" OLDFILEUID="%s" NEWFILEUID="%s"?>\n""" % \
               (self.parse_dict["header"]["SECURITY"],
                self.parse_dict["header"]["OLDFILEUID"],
                self.parse_dict["header"]["NEWFILEUID"])

        if original_format is not None:
            xml += """<!-- Converted from: %s -->\n""" % original_format
        if date_format is not None:
            xml += """<!-- Date format was: %s -->\n""" % date_format

        taglist = self.parse_dict["body"]["OFX"].asList()
        xml += self._format_xml(taglist)

        return xml

    def _format_xml(self, mylist, indent=0):
        xml = ""
        indentstring = " " * indent
        tag = mylist.pop(0)
        if len(mylist) > 0 and isinstance(mylist[0], list):
            xml += "%s<%s>\n" % (indentstring, tag)
            for value in mylist:
                xml += self._format_xml(value, indent=indent + 2)
            xml += "%s</%s>\n" % (indentstring, tag)
        elif len(mylist) > 0:
            # Unescape then reescape so we don't wind up with '&amp;lt;', oy.
            value = sax.escape(sax.unescape(mylist[0]))
            xml += "%s<%s>%s</%s>\n" % (indentstring, tag, value, tag)
        return xml

