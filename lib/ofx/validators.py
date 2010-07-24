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
# ofx.validators - Classes to validate certain financial data types.
#

class RoutingNumber:
    def __init__(self, number):
        self.number = number
        # FIXME: need to make sure we're really getting a number and not any non-number characters.
        try:
            self.digits = [int(digit) for digit in str(self.number).strip()]
            self.region_code = int(str(self.digits[0]) + str(self.digits[1]))
            self.converted = True
        except ValueError:
            # Not a number, failed to convert
            self.digits = None
            self.region_code = None
            self.converted = False
    
    def is_valid(self):
        if self.converted is False or len(self.digits) != 9:
            return False
        
        checksum = ((self.digits[0] * 3) +
                    (self.digits[1] * 7) +
                     self.digits[2]      +
                    (self.digits[3] * 3) +
                    (self.digits[4] * 7) +
                     self.digits[5]      +
                    (self.digits[6] * 3) +
                    (self.digits[7] * 7) +
                     self.digits[8]       )
        return (checksum % 10 == 0)
    
    def get_type(self):
        # Remember that range() stops one short of the second argument.
        # In other words, "x in range(1, 13)" means "x >= 1 and x < 13".
        if self.region_code == 0:
            return "United States Government"
        elif self.region_code in range(1, 13):
            return "Primary"
        elif self.region_code in range(21, 33):
            return "Thrift"
        elif self.region_code in range(61, 73):
            return "Electronic"
        elif self.region_code == 80:
            return "Traveller's Cheque"
        else:
            return None
    
    def get_region(self):
        if self.region_code == 0:
            return "United States Government"
        elif self.region_code in [1, 21, 61]:
            return "Boston"
        elif self.region_code in [2, 22, 62]:
            return "New York"
        elif self.region_code in [3, 23, 63]:
            return "Philadelphia"
        elif self.region_code in [4, 24, 64]:
            return "Cleveland"
        elif self.region_code in [5, 25, 65]:
            return "Richmond"
        elif self.region_code in [6, 26, 66]:
            return "Atlanta"
        elif self.region_code in [7, 27, 67]:
            return "Chicago"
        elif self.region_code in [8, 28, 68]:
            return "St. Louis"
        elif self.region_code in [9, 29, 69]:
            return "Minneapolis"
        elif self.region_code in [10, 30, 70]:
            return "Kansas City"
        elif self.region_code in [11, 31, 71]:
            return "Dallas"
        elif self.region_code in [12, 32, 72]:
            return "San Francisco"
        elif self.region_code == 80:
            return "Traveller's Cheque"
        else:
            return None
    
    def to_s(self):
        return str(self.number) + " (valid: %s; type: %s; region: %s)" % \
            (self.is_valid(), self.get_type(), self.get_region())
    
    def __repr__(self):
        return self.to_s()
    
