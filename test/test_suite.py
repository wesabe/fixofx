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
#  test/suite - controller for all fixofx tests.
#

import sys
sys.path.insert(0, '../3rdparty')
sys.path.insert(0, '../lib')

import unittest

def suite():
    modules_to_test = ['ofxtools_qif_converter', 'mock_ofx_server', 
                       'ofx_account', 'ofx_builder', 'ofx_client', 
                       'ofx_document', 'ofx_error', 'ofx_parser', 
                       'ofx_request', 'ofx_response', 'ofx_validators']
    alltests = unittest.TestSuite()
    
    for module in map(__import__, modules_to_test):
        alltests.addTest(unittest.findTestCases(module))
    
    return alltests

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
