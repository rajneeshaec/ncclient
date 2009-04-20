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

import logging
from xml.etree import cElementTree as ElementTree

logging.getLogger('ncclient.content.hello')

from . import NETCONF_NS
from .util import qualify as _
from ..capability import Capabilities

def make(capabilities):
    return '<hello xmlns="%s">%s</hello>' % (NETCONF_NS, capabilities)

def parse(raw):
    id, capabilities = 0, Capabilities()
    root = ElementTree.fromstring(raw)
    if root.tag == _('hello'):
        for child in hello.getchildren():
            if child.tag == _('session-id'):
                id = int(child.text)
            elif child.tag == _('capabilities'):
                for cap in child.getiterator(_('capability')):
                    capabilities.add(cap.text)
    return id, capabilities
