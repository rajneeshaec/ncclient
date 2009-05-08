# Copyright 2009 Shikhar Bhushan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'Boilerplate'

from ncclient import OperationError

from . import MissingCapabilityError

def one_of(*args):
    'Verifies that only one of the arguments is not None'
    for i, arg in enumerate(args):
        if arg is not None:
            for argh in args[i+1:]:
                if argh is not None:
                    raise OperationError('Too many parameters')
            else:
                return
    raise OperationError('Insufficient parameters')

def store_or_url(store, url):
    one_of(store, url)
    node = {}
    if store is not None:
        node['tag'] = store
    else:
        node['tag'] = 'url'
        node['text'] = url
    return node

def build_filter(type, criteria):
    filter = {
        'tag': 'filter',
        'attributes': {'type': type}
    }
    if type == 'xpath':
        filter['attributes']['select'] = criteria
    else:
        filter['subtree'] = [criteria]
    return filter
