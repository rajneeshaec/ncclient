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

from Queue import Queue
from threading import Thread, Lock, Event

from ncclient import content
from ncclient.capabilities import Capabilities

import logging
logger = logging.getLogger('ncclient.transport.session')

class Session(Thread):
    "This is a base class for use by protocol implementations"
    
    def __init__(self, capabilities):
        Thread.__init__(self)
        self.set_daemon(True)
        self._listeners = set() # 3.0's weakset ideal
        self._lock = Lock()
        self.set_name('session')
        self._q = Queue()
        self._client_capabilities = capabilities
        self._server_capabilities = None # yet
        self._id = None # session-id
        self._connected = False # to be set/cleared by subclass implementation
        logger.debug('%r created: client_capabilities=%r' %
                     (self, self._client_capabilities))
    
    def _dispatch_message(self, raw):
        try:
            root = content.parse_root(raw)
        except Exception as e:
            logger.error('error parsing dispatch message: %s' % e)
            return
        with self._lock:
            listeners = list(self._listeners)
        for l in listeners:
            logger.debug('dispatching message to %r' % l)
            try:
                l.callback(root, raw)
            except Exception as e:
                logger.warning('[error] %r' % e)
    
    def _dispatch_error(self, err):
        with self._lock:
            listeners = list(self._listeners)
        for l in listeners:
            logger.debug('dispatching error to %r' % l)
            try:
                l.errback(err)
            except Exception as e:
                logger.warning('error %r' % e)
    
    def _post_connect(self):
        "Greeting stuff"
        init_event = Event()
        error = [None] # so that err_cb can bind error[0]. just how it is.
        # callbacks
        def ok_cb(id, capabilities):
            self._id = id
            self._server_capabilities = capabilities
            init_event.set()
        def err_cb(err):
            error[0] = err
            init_event.set()
        listener = HelloHandler(ok_cb, err_cb)
        self.add_listener(listener)
        self.send(HelloHandler.build(self._client_capabilities))
        logger.debug('starting main loop')
        self.start()
        # we expect server's hello message
        init_event.wait()
        # received hello message or an error happened
        self.remove_listener(listener)
        if error[0]:
            raise error[0]
        logger.info('initialized: session-id=%s | server_capabilities=%s' % (self._id, self._server_capabilities))
    
    def add_listener(self, listener):
        """Register a listener that will be notified of incoming messages and errors.
        
        :type listener: :class:`SessionListener`
        """
        logger.debug('installing listener %r' % listener)
        if not isinstance(listener, SessionListener):
            raise SessionError("Listener must be a SessionListener type")
        with self._lock:
            self._listeners.add(listener)
    
    def remove_listener(self, listener):
        "Unregister some listener; ignoring if the listener was never registered."
        logger.debug('discarding listener %r' % listener)
        with self._lock:
            self._listeners.discard(listener)
    
    def get_listener_instance(self, cls):
        """If a listener of the specified type is registered, returns it. This is useful when it is desirable to have only one instance of a particular type per session, i.e. a multiton.
        
        :type cls: :class:`type`
        :rtype: :class:`SessionListener` or :const:`None`
        """
        with self._lock:
            for listener in self._listeners:
                if isinstance(listener, cls):
                    return listener
    
    def connect(self, *args, **kwds): # subclass implements
        raise NotImplementedError

    def run(self): # subclass implements
        raise NotImplementedError
    
    def send(self, message):
        """
        :param message: XML document
        :type message: string
        """
        logger.debug('queueing %s' % message)
        self._q.put(message)
    
    ### Properties

    @property
    def connected(self):
        ":rtype: bool"
        return self._connected

    @property
    def client_capabilities(self):
        ":rtype: :class:`Capabilities`"
        return self._client_capabilities
    
    @property
    def server_capabilities(self):
        ":rtype: :class:`Capabilities` or :const:`None`"
        return self._server_capabilities
    
    @property
    def id(self):
        ":rtype: :obj:`string` or :const:`None`"
        return self._id
    
    @property
    def can_pipeline(self):
        ":rtype: :obj:`bool`"
        return True


class SessionListener(object):
    
    """'Listen' to incoming messages on a NETCONF :class:`Session`
    
    .. note::
        Avoid computationally intensive tasks in the callbacks.
    """
    
    def callback(self, root, raw):
        """Called when a new XML document is received. The `root` argument allows the callback to determine whether it wants to further process the document.
        
        :param root: tuple of (tag, attrs) where tag is the qualified name of the root element and attrs is a dictionary of its attributes (also qualified names)
        :param raw: XML document
        :type raw: string
        """
        raise NotImplementedError
    
    def errback(self, ex):
        """Called when an error occurs.
        
        :type ex: :class:`Exception`
        """
        raise NotImplementedError


class HelloHandler(SessionListener):
    
    def __init__(self, init_cb, error_cb):
        self._init_cb = init_cb
        self._error_cb = error_cb
    
    def callback(self, root, raw):
        if content.unqualify(root[0]) == 'hello':
            try:
                id, capabilities = HelloHandler.parse(raw)
            except Exception as e:
                self._error_cb(e)
            else:
                self._init_cb(id, capabilities)
    
    def errback(self, err):
        self._error_cb(err)
    
    @staticmethod
    def build(capabilities):
        "Given a list of capability URI's returns <hello> message XML string"
        spec = {
            'tag': content.qualify('hello'),
            'subtree': [{
                'tag': 'capabilities',
                'subtree': # this is fun :-)
                    [{'tag': 'capability', 'text': uri} for uri in capabilities]
                }]
            }
        return content.dtree2xml(spec)
    
    @staticmethod
    def parse(raw):
        "Returns tuple of (session-id (str), capabilities (Capabilities)"
        sid, capabilities = 0, []
        root = content.xml2ele(raw)
        for child in root.getchildren():
            tag = content.unqualify(child.tag)
            if tag == 'session-id':
                sid = child.text
            elif tag == 'capabilities':
                for cap in child.getchildren():
                    if content.unqualify(cap.tag) == 'capability':
                        capabilities.append(cap.text)
        return sid, Capabilities(capabilities)
