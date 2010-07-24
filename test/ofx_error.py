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

class ErrorTests(unittest.TestCase):    
    def test_ofx_error_to_str(self):
        error = ofx.Error("test", code=9999, severity="ERROR", message="Test")
        expected = "Test\n(ERROR 9999: Unknown error code)"
        self.assertEqual(expected, error.str())
        self.assertEqual(expected, str(error))
    

if __name__ == '__main__':
    unittest.main()
