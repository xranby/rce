#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Factory.py
#       
#       This file is part of the RoboEarth Cloud Engine framework.
#       
#       This file was originally created for RoboEearth - http://www.roboearth.org/
#       The research leading to these results has received funding from the European Union 
#       Seventh Framework Programme FP7/2007-2013 under grant agreement no248942 RoboEarth.
#       
#       Copyright 2012 RoboEarth
#       
#       Licensed under the Apache License, Version 2.0 (the "License");
#       you may not use this file except in compliance with the License.
#       You may obtain a copy of the License at
#       
#       http://www.apache.org/licenses/LICENSE-2.0
#       
#       Unless required by applicable law or agreed to in writing, software
#       distributed under the License is distributed on an "AS IS" BASIS,
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#       See the License for the specific language governing permissions and
#       limitations under the License.
#       
#       \author/s: Dominique Hunziker <dominique.hunziker@gmail.com> 
#       
#       

# zope specific imports
from zope.interface import implements
from zope.interface.verify import verifyObject
from zope.interface.exceptions import Invalid

# twisted specific imports
from twisted.python import log
from twisted.internet.protocol import ServerFactory, ReconnectingClientFactory

# Custom imports
from Exceptions import InternalError, SerializationError
from Protocol import RCEProtocol
from Message import MsgDef
from Message import MsgTypes
from Message.Base import Message
from Message.Handler import _Sender
from Interfaces import IPostInitTrigger

class EmptyTrigger(object):
    """ PostInitTrigger which implements the necessary methods, but does nothing.
    """
    implements(IPostInitTrigger)
    
    def trigger(self, origin, ip):
        pass

class RCEFactory(object):
    """ Base class which implements base methods for all RCEFactories.
    """
    def __init__(self, commMngr, trigger=None):
        """ Initialize the RCEFactory.
            
            @param commMngr:    CommManager instance which should be used with this
                                factory and its build protocols.
            @type  commMngr:    CommManager
            
            @param trigger:     Instance which should be used as PostInitTrigger.
                                If argument is omitted the PostInitTrigger does nothing.
            @type  trigger:     IPostInitTrigger
            
            @raise:     InternalError if the trigger does not implement the "IPostInitTrigger"
                        interface.
        """
        if not trigger:
            trigger = EmptyTrigger()
        
        self._commManager = commMngr
        self._filter = set([MsgTypes.INIT_REQUEST])
        
        try:
            verifyObject(IPostInitTrigger, trigger)
        except Invalid as e:
            raise InternalError(
                'Verification of the class "{0}" for the Interface "IPostInitTrigger" failed: {1}'.format(
                    trigger.__class__.__name__,
                    e
                )
            )
        
        self._trigger = trigger
    
    @property
    def commManager(self):
        """ CommManager instance used with this factory. """
        return self._commManager
    
    def addApprovedMessageTypes(self, msgTypes):
        """ Method which is used to add a MessageTypes to the list of approved types.
            
            If the message type is not in the list of approved types the message will
            not be processed in this node.
                                
            @param msgTypes:    List of the approved message types. Valid types are available
                                in MsgTypes.
            @type  msgTypes:    list
        """
        for msgType in msgTypes:
            self._filter.add(msgType)
    
    def filterMessage(self, msgType):
        """ Method which is called by the protocol to filter the incoming messages.
                                
            @param msgType:     String identifier of the message type.
            @type  msgType:     str
            
            @return:        If the message should be filtered out True is returned and
                            False otherwise.
            @rtype:         str
        """
        return msgType not in self._filter
    
    def startInit(self, conn):
        """ Method which is called when the connection has been made.
            
            @param conn:    Protocol instance which just has been made.
            @type  conn:    RCEProtocol
        """
    
    def processInitMessage(self, msg, conn):
        """ Method which is used to when a message is received and the initialized
            flag of the protocol instance is not yet set.

            @param msg:     Received message which should contain a InitRequest.
            @type  msg:     Message
            
            @param conn:    Protocol instance who received the initialization message.
            @type  conn:    RCEProtocol
        """
    
    def unregisterConnection(self, conn):
        """ This method should be called to remove any references to the given connection.
            
            @param conn:    Protocol instance who should be unregistered.
            @type  conn:    RCEProtocol
        """
        self._commManager.router.unregisterConnection(conn)

class RCEClientFactory(RCEFactory, ReconnectingClientFactory):
    """ Factory which is used for client connections.
    """
    def __init__(self, commMngr, serverID, trigger=None):
        """ Initialize the RCEClientFactory.

            @param commMngr:    CommManager which is responsible for handling the communication
                                in this node.
            @type  commMngr:    CommManager
            
            @param serverID:     CommID of the server node.
            @type  serverID:     str
            
            @param trigger:     Instance which should be used as PostInitTrigger.
                                If argument is omitted the PostInitTrigger does nothing.
            @type  trigger:     IPostInitTrigger
        """
        RCEFactory.__init__(self, commMngr, trigger)
        
        self._serverID = serverID
    
    def buildProtocol(self, addr):
        """ Builds a new protocol instance.

            This method is called when a new connection should be
            established.

            This method should not be overwritten.
        """
        self.resetDelay()
        return RCEProtocol(self, addr)
    
    def startInit(self, conn):
        msg = Message()
        msg.msgType = MsgTypes.INIT_REQUEST
        msg.dest = MsgDef.NEIGHBOR_ADDR
        
        msg.content = { 'remoteID' : self._serverID }
        
        try:
            buf = msg.serialize(self._commManager)
            _Sender(len(buf), self._commManager.commID, msg.dest, buf).send(conn)
        except SerializationError as e:
            log.msg('Could not serialize message: {0}'.format(e))
            conn.transport.loseConnection()
    
    def processInitMessage(self, msg, conn):
        # First some base checks of message header
        if msg.msgType != MsgTypes.INIT_REQUEST:
            log.msg('Received message type different from INIT_REQUEST before initialization of protocol instance has been completed.')
            conn.transport.loseConnection()
            return
        
        origin = msg.origin
        
        if origin != self._serverID:
            log.msg('Received origin ID does not match this node server ID for initialization of protocol instance.')
            conn.transport.loseConnection()
            return
        
        if msg.content['remoteID'] != self._commManager.commID:
            log.msg('Received remote ID does not match this node communication ID for initialization of protocol instance.')
            conn.transport.loseConnection()
            return
        
        # Set protocol to initialized and register connection in manager
        conn.dest = origin
        conn.initialized = True
        self._commManager.router.registerConnection(conn)
        log.msg('Connection established to "{0}".'.format(origin))
        
        # Trigger the post init method
        self._trigger.trigger(origin, conn.ip)

class RCEServerFactory(RCEFactory, ServerFactory):
    """ Factory which is used for server connections.
    """
    def buildProtocol(self, addr):
        """ Builds a new protocol instance.

            This method is called when a new connection should be
            established.

            This method should not be overwritten.
        """
        return RCEProtocol(self, addr)
    
    def processInitMessage(self, msg, conn):
        # First some base checks of message header
        if msg.msgType != MsgTypes.INIT_REQUEST:
            log.msg('Received message type different from INIT_REQUEST before initialization of protocol instance has been completed.')
            conn.transport.loseConnection()
            return
        
        if msg.content['remoteID'] != self._commManager.commID:
            log.msg('Received remote ID does not match this node for initialization of protocol instance.')
            conn.transport.loseConnection()
            return
        
        origin = msg.origin
        
        # Authenticate origin with key
        if not self.authOrigin(origin):
            log.msg('Origin could not be authenticated.')
            conn.transport.loseConnection()
            return
        
        msg = Message()
        msg.msgType = MsgTypes.INIT_REQUEST
        msg.dest = origin
        msg.content = { 'remoteID' : origin }
        
        try:
            buf = msg.serialize(self._commManager)
            _Sender(len(buf), self._commManager.commID, msg.dest, buf).send(conn)
        except SerializationError as e:
            log.msg('Could not serialize message: {0}'.format(e))
            conn.transport.loseConnection()
            return
        
        # Set protocol to initialized and register connection in manager
        conn.dest = origin
        conn.initialized = True
        self._commManager.router.registerConnection(conn)
        log.msg('Connection established to "{0}".'.format(origin))
        
        # Trigger the post init method
        self._trigger.trigger(origin, conn.ip)
    
    def authOrigin(self, origin):
        """ Authenticate the origin of the InitRequest.
            
            @param origin:  CommID of request origin.
            @type  origin:  str
            
            @return:        Return True if the origin was successfully authenticated.
        """
        return True
