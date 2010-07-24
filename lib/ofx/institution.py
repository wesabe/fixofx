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
# ofx.institution - container for financial insitution configuration data.
#

# REVIEW: Well, this certainly doesn't do much.
# At this point it works fine as a data structure.  Later on
# it would be nice if it actually, you know, did something.

import ofx

class Institution:
    def __init__(self, name="", ofx_org="", ofx_url="", ofx_fid=""):
        self.name    = name
        self.ofx_org = ofx_org
        self.ofx_url = ofx_url
        self.ofx_fid = ofx_fid

    def to_s(self):
        return ("Name: %s; Org: %s; OFX URL: %s; FID: %s") % \
               (self.name, self.ofx_org, self.ofx_url, self.ofx_fid)

    def __repr__(self):
        return self.to_s()

    def as_dict(self):
        return { 'name' : self.name,
                 'ofx_org' : self.ofx_org,
                 'ofx_url' : self.ofx_url,
                 'ofx_fid' : self.ofx_fid }

    def load_from_dict(fi_dict):
        return ofx.Institution(name=fi_dict.get('name'),
                               ofx_org=fi_dict.get('ofx_org'),
                               ofx_url=fi_dict.get('ofx_url'),
                               ofx_fid=fi_dict.get('ofx_fid'))
    load_from_dict = staticmethod(load_from_dict)

