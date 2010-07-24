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
#  ofx.FileTyper - figures out the type of a data file.
#

import csv
import re

class FileTyper:
    def __init__(self, text):
        self.text = text
    
    def trust(self):
        if re.search("OFXHEADER:", self.text, re.IGNORECASE) != None:
            match = re.search("VERSION:(\d)(\d+)", self.text)
            if match == None:
                return "OFX/1"
            else:
                major = match.group(1)
                minor = match.group(2)
                return "OFX/%s.%s" % (major, minor)
        
        elif re.search('<?OFX OFXHEADER="200"', self.text, re.IGNORECASE) != None:
            match = re.search('VERSION="(\d)(\d+)"', self.text)
            if match == None:
                return "OFX/2"
            else:
                major = match.group(1)
                minor = match.group(2)
                return "OFX/%s.%s" % (major, minor)
        
        elif self.text[0:100].find("MSISAM Database") != -1:
            return "MSMONEY-DB"
        
        elif self.text.find('<OFC>') != -1:
            return "OFC"
        
        elif re.search("^:20:", self.text, re.MULTILINE) != None and \
        re.search("^\:60F\:", self.text, re.MULTILINE) != None and \
        re.search("^-$", self.text, re.MULTILINE) != None:
            return "MT940"
        
        elif self.text.startswith('%PDF-'):
            return "PDF"
        
        elif self.text.find('<HTML') != -1 or self.text.find('<html') != -1:
            return "HTML"
        
        elif self.text.startswith("\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1\x00"):
            return "EXCEL"
            
        elif self.text.startswith("\xAC\x9E\xBD\x8F\x00\x00"):
            return "QUICKEN-DATA"
        
        elif self.text.startswith("\x4D\x5A"):
            return "EXE"
        
        elif self.text.find('Unix eFxTool 1.1') != -1:
            return "EFAX"
        
        elif re.compile("^\^(EUR)*\s*$", re.MULTILINE).search(self.text) != None or \
        re.compile("^!Type:", re.MULTILINE).search(self.text) != None:
            # A carat on a line by itself (ignoring whitespace) is a record
            # delimiter in QIF -- the only seemingly consistent marker in a
            # QIF file. (You can't rely on the "!Type" header since some banks
            # omit it.)
            return "QIF"
        
        else:
            # If more than 80% of the lines in the file have the same number of fields,
            # as determined by the CSV parser, and if there are more than 2 fields in
            # each of those lines, assume that it's CSV.
            dialect = csv.Sniffer().sniff(self.text, ",\t")
            if dialect is None:
                return "UNKNOWN"
            
            try:
                lines = self.text.splitlines()
                rows  = 0
                frequencies = {}
                for row in csv.reader(lines, dialect=dialect):
                    fields = len(row)
                    if fields > 0:
                        frequencies[fields] = frequencies.get(fields, 0) + 1
                        rows = rows + 1
            
                for fieldcount, frequency in frequencies.items():
                    percentage = (float(frequency) / float(rows)) * float(100)
                    if fieldcount > 2 and percentage > 80:
                        if dialect.delimiter == ",":
                            return "CSV"
                        elif dialect.delimiter == "\t":
                            return "TSV"
            except StandardError:
                pass
            
            # If we get all the way down here, we don't know what the file type is.
            return "UNKNOWN"

