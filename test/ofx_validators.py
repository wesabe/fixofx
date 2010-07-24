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

import sys
sys.path.insert(0, '../3rdparty')
sys.path.insert(0, '../lib')

import ofx
import unittest

class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.good_aba = ofx.RoutingNumber("314074269")
        self.bad_aba  = ofx.RoutingNumber("123456789")
    
    def test_not_a_number(self):
        nan = ofx.RoutingNumber("123abd")
        self.assertEqual(nan.is_valid(), False)
        self.assertEqual(nan.get_type(), None)
        self.assertEqual(nan.get_region(), None)
        self.assertEqual(str(nan),
                         "123abd (valid: False; type: None; region: None)")
    
    def test_valid_aba(self):
        self.assertEqual(self.good_aba.is_valid(), True)
        self.assertEqual(self.bad_aba.is_valid(), False)
    
    def test_aba_types(self):
        self.assertEqual(ofx.RoutingNumber("001234567").get_type(), 
                         "United States Government")
        self.assertEqual(ofx.RoutingNumber("011234567").get_type(), 
                         "Primary")
        self.assertEqual(ofx.RoutingNumber("071234567").get_type(), 
                         "Primary")
        self.assertEqual(ofx.RoutingNumber("121234567").get_type(), 
                         "Primary")
        self.assertEqual(ofx.RoutingNumber("131234567").get_type(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("201234567").get_type(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("211234567").get_type(), 
                         "Thrift")
        self.assertEqual(ofx.RoutingNumber("251234567").get_type(), 
                         "Thrift")
        self.assertEqual(ofx.RoutingNumber("321234567").get_type(), 
                         "Thrift")
        self.assertEqual(ofx.RoutingNumber("331234567").get_type(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("601234567").get_type(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("611234567").get_type(), 
                         "Electronic")
        self.assertEqual(ofx.RoutingNumber("641234567").get_type(), 
                         "Electronic")
        self.assertEqual(ofx.RoutingNumber("721234567").get_type(), 
                         "Electronic")
        self.assertEqual(ofx.RoutingNumber("731234567").get_type(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("791234567").get_type(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("801234567").get_type(), 
                         "Traveller's Cheque")
        self.assertEqual(ofx.RoutingNumber("811234567").get_type(), 
                         None)
    
    def test_aba_regions(self):
        self.assertEqual(ofx.RoutingNumber("001234567").get_region(), 
                         "United States Government")
        self.assertEqual(ofx.RoutingNumber("011234567").get_region(), 
                         "Boston")
        self.assertEqual(ofx.RoutingNumber("071234567").get_region(), 
                         "Chicago")
        self.assertEqual(ofx.RoutingNumber("121234567").get_region(), 
                         "San Francisco")
        self.assertEqual(ofx.RoutingNumber("131234567").get_region(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("201234567").get_region(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("211234567").get_region(), 
                         "Boston")
        self.assertEqual(ofx.RoutingNumber("251234567").get_region(), 
                         "Richmond")
        self.assertEqual(ofx.RoutingNumber("321234567").get_region(), 
                         "San Francisco")
        self.assertEqual(ofx.RoutingNumber("331234567").get_region(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("601234567").get_region(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("611234567").get_region(), 
                         "Boston")
        self.assertEqual(ofx.RoutingNumber("641234567").get_region(), 
                         "Cleveland")
        self.assertEqual(ofx.RoutingNumber("721234567").get_region(), 
                         "San Francisco")
        self.assertEqual(ofx.RoutingNumber("731234567").get_region(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("791234567").get_region(), 
                         None)
        self.assertEqual(ofx.RoutingNumber("801234567").get_region(), 
                         "Traveller's Cheque")
        self.assertEqual(ofx.RoutingNumber("811234567").get_region(), 
                         None)
    
    def test_aba_string(self):
        self.assertEqual(str(self.good_aba), 
                         "314074269 (valid: True; type: Thrift; region: Dallas)")
    

if __name__ == '__main__':
    unittest.main()
