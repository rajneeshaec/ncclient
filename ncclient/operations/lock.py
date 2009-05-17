# Copyright 2h009 Shikhar Bhushan
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

'Locking-related NETCONF operations'

from rpc import RPC

class Lock(RPC):

    "*<lock>* RPC"

    SPEC = {
        'tag': 'lock',
        'subtree': {
            'tag': 'target',
            'subtree': {'tag': None }
        }
    }

    def request(self, target):
        """
        :arg target: see :ref:`source_target`
        :type target: string

        :rtype: :ref:`return`
        """
        spec = Lock.SPEC.copy()
        spec['subtree']['subtree']['tag'] = target
        return self._request(spec)


class Unlock(RPC):

    "*<unlock>* RPC"

    SPEC = {
        'tag': 'unlock',
        'subtree': {
            'tag': 'target',
            'subtree': {'tag': None }
        }
    }

    def request(self, target):
        """
        :arg target: see :ref:`source_target`
        :type target: string

        :rtype: :ref:`return`
        """
        spec = Unlock.SPEC.copy()
        spec['subtree']['subtree']['tag'] = target
        return self._request(spec)


class LockContext:

    """
    A context manager for the :class:`Lock` / :class:`Unlock` pair of RPC's.

    Initialise with session instance (:class:`Session
    <ncclient.transport.Session>`) and lock target (:ref:`source_target`)
    """

    def __init__(self, session, target):
        self.session = session
        self.target = target

    def __enter__(self):
        reply = Lock(self.session).request(self.target)
        if not reply.ok:
            raise reply.error
        else:
            return self

    def __exit__(self, *args):
        reply = Unlock(session).request(self.target)
        if not reply.ok:
            raise reply.error
        return False
