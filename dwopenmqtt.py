#!/usr/bin/python
#==============================================================================
#== Title: dwopenmqtt.py
#== Description:  dwOpen MQTT/JSON Public API Library (Telit Python Library)
#==
#== Copyright (c)2014. ILS Technology, LLC.
#== http://www.ilstechnology.com
#== http://www.devicewise.com
#==
#== To Execute:
#== python dwPY_OpenMQTT.py 
#==
#==============================================================================
#Legal Disclaimer:
#
#Copyright 2014, ILS Technology
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions
#are met:
#
#Redistributions of source code must retain the above copyright notice,
#this list of conditions and the following disclaimer.
#
#Redistributions in binary form must reproduce the above copyright
#notice, this list of conditions and the following disclaimer in
#the documentation and/or other materials provided with the distribution.
#
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS``AS
#IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
#TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR
#CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#==============================================================================

##------------------------------------------------------------------------------------------------------------------
## Release Information:
##  V1.0    (JEK, 06/18/2014)   :   Initial release (deviceWISE Open HTTP/JSON Public API - Python)
##  V1.1    (JEK, 11/15/2014)   :   Initial release (deviceWISE Open MQTT/JSON Public API - Python)
##------------------------------------------------------------------------------------------------------------------

import time
import random
import string
import paho.mqtt.client as mqtt
import ssl
import threading
import json
import os
from Queue import Queue
import tr50protocol
import logging

class dwOpen:

      dwApiURL    = "http://api.devicewise.com/api";
      dwApiHost   = "api.devicewise.com";

      myAppToken  = None;
      myThingKey  = None;
      mySessionId = None;
      myCallback = None;
      
      msgId = 0;
      msgResp = "replyText";

      _is_connected = False
      
      mbox_event = threading.Event()
      action_queue = Queue()
            
      client = mqtt.Client();

      tr50 = tr50protocol.TR50protocol()
      tr50.initTransport( "mqtt")


      #------------------------------------------------------------------------------
      #-- Function: _generate_id
      #-- Purpose: Generate a random 64 character string
      #------------------------------------------------------------------------------
      def _generate_id(self):
          str = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64))
          return str

      #------------------------------------------------------------------------------
      #-- Function: _getClientId
      #-- Purpose:  Get a random ID used to identify this client.  
      #-- Arguments: pathname - Path to a file that contains a previously generated id
      #-- Algorithm: If a file exists with the ID, just read and return it, else 
      #              generate a random ID, stash it in the file, and return it.
      #
      #              Used to generate the ClientID for a "Thing".  Once a "Thing" 
      #              connects once, it has to always use the same string as ClientID
      #------------------------------------------------------------------------------
      def _getClientId(self, pathname):

        id = None

        if (os.path.isfile(pathname)):
             f  = open(pathname, 'rb')
             id  = f.read()
             f.close()
        else:
             id = self._generate_id()
             f = open(pathname, 'wb')
             f.write(id)
             f.close()

        return id
      
      #------------------------------------------------------------------------------
      #-- Function: getElementCount 
      #-- Purpose:  Get Element Count from Raw Response
      #------------------------------------------------------------------------------
      def getElementCount(haystack, needle):
          if( len( needle ) > len ( haystack ) and needle == "" ):
              return 0
          
          count = ( len(haystack) - len( haystack.replace(needle,"")) ) / len( needle )
          return count;

      #------------------------------------------------------------------------------
      #-- Function: getFramedText 
      #-- Purpose:  Get Text Conten Between Two Frame Markers
      #------------------------------------------------------------------------------
      def getFramedText(self, line, string_start, string_end):
          temp = line.split(string_start)[1]

          return temp.split(string_end)[0]
          
      #------------------------------------------------------------------------------
      #-- Function: getElementArray
      #-- Purpose:  Get Element Array from Raw Response
      #------------------------------------------------------------------------------
      def getElementArray(haystack, needle):
          index   = 0
          subsLoc = -1
          lastLoc = -1
          entry   = 0
          final   = []
      
          count = ( len(haystack) - len( haystack.replace(needle,"")) ) / len( needle )
      
          # substring -> string[start:start+length]
      
          while( index < len(haystack) ):
                 subsLoc = haystack.find(needle, index)

          if( subsLoc != -1 and subsLoc != lastLoc ):
              lastLoc  = subsLoc
              strstart = lastLoc + len(needle) + 1
              subStack = haystack[strstart:]
              firstQuote = subStack.find('"')
              subPart    = subStack[0:firstQuote]
                  
              final.append( subPart )

              index = index + 1
    
          return final
  

      #------------------------------------------------------------------------------
      #-- Function: dwCheck
      #-- Purpose:  Check/Service Incoming Messages
      #------------------------------------------------------------------------------
      def dwCheck( self ):

          self.client.loop();

          return 0;

      #------------------------------------------------------------------------------
      #-- Function: dwMailboxCheck
      #-- Purpose:  Execute Mailbox Check Request
      #------------------------------------------------------------------------------
      def dwMailboxCheck( self ):
          rc = -1 
      
          logging.debug("[dwOpen] Sending MailboxCheck Request...")
          postRequest = self.tr50.createMailboxCheck();
          logging.debug("[dwOpen] MailboxCheck JSON Created: %s", postRequest)
      
          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] MailboxCheck Response Received: %s", postResponse)
          
          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;
              
          return rc;

      #------------------------------------------------------------------------------
      #-- Function: dwMailboxUpdate
      #-- Purpose:  Execute Mailbox Update Request
      #------------------------------------------------------------------------------
      def dwMailboxUpdate( self, messageId, updateMsg ):
          rc = -1 
      
          logging.debug("[dwOpen] Sending MailboxUpdate Request...")
          postRequest = self.tr50.createMailboxUpdate( messageId, updateMsg );
          logging.debug("[dwOpen] MailboxUpdate JSON Created: %s", postRequest)
      
          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] MailboxUpdate Response Received: %s", postResponse)
          
          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;
      
          return rc;

      #------------------------------------------------------------------------------
      #-- Function: dwMailboxAck
      #-- Purpose:  Execute Mailbox Ack Request
      #------------------------------------------------------------------------------
      def dwMailboxAck( self, messageId, errorCode, errorMsg, compParams ):
          rc = -1 
      
          logging.debug("[dwOpen] Sending MailboxAck Request...")
          postRequest = self.tr50.createMailboxAck( messageId, errorCode, errorMsg, compParams );
          logging.debug("[dwOpen] MailboxAck JSON Created: %s", postRequest)
      
          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] MailboxAck Response Received: %s", postResponse)
          
          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;
      
          return rc;
         
      #------------------------------------------------------------------------------
      #-- Function: dwMethodExecThread
      #-- Purpose:  Runs as a background thread. Waits for a message to get posted
      #             to the acton_queue, decodes it, and calls application to process it
      #------------------------------------------------------------------------------
      def dwMethodExecThread ( self ):
      
          tid = threading.currentThread()
          logging.debug("[dwOpen] MethodExec Thread Started, TID=%s", tid.name)
          
          while (True):
              execRequest =self.action_queue.get()
              
              messageId = self.getFramedText(execRequest, '{\"id\":\"', '\",\"thing')

              # rc = self.dwMailboxUpdate( messageId, "Processing..." );

              MethodName = self.getFramedText(execRequest, '{\"method\":\"', '\",\"')

              execMethod = execRequest[ execRequest.find('\"method\":'): ]
              # print "Method.Exec - execMethod = " + execMethod                  

              ParamText = ''
              if( execMethod.find("\"params\":") > 0 ):
                  ParamText = self.getFramedText(execMethod, '\"params\":', ',\"thingDef')

              logging.debug("[dwOpen] MethodExec Message ID=%s Method=%s Params=%s", 
                      messageId, MethodName, ParamText)

              # Handle Method Processing... Use Global Counter (gCounter)
          
              self.myCallback(messageId, MethodName, ParamText)

          logging.debug("[dwOpen] Unexpected MethodExec Thread Exit")    
          return
       
       
      #------------------------------------------------------------------------------
      #-- Function: dwMailboxThread
      #-- Purpose:  Runs as a background thread. Waits for mailbox event and causes
      #             the method.exec messages to come in
      #------------------------------------------------------------------------------
      def dwMailboxThread( self):
      
          tid = threading.currentThread()
          logging.debug("[dwOpen] Mailbox Thread Started, TID=%s", tid.name)
          
          while (True):
              flag = self.mbox_event.wait()
              logging.debug ("Mailbox event received: %s ", str(flag))
              self.mbox_event.clear()
              self.dwMailboxCheck( )
              
          logging.debug("[dwOpen] Unexpected Mailbox Thread Exit")
          return
              
      #------------------------------------------------------------------------------
      #-- Function: dwBindThing
      #-- Purpose:  Execute Bind Thing Request
      #------------------------------------------------------------------------------
      def dwBindThing( self, thingKey ):
          rc = -1 
      
          logging.debug("[dwOpen] Sending BindThing Request...")
          postRequest = self.tr50.createBindThing( thingKey );
          logging.debug("[dwOpen] BindThing JSON Created: %s", postRequest)
      
          # Execute MQTT Send/Receivee
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] BindThing Response Received: %s", postResponse)
          
          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;
      
          return rc;
          
      #------------------------------------------------------------------------------
      #-- Function: dwUnbindThing
      #-- Purpose:  Execute Unbind Thing Request
      #------------------------------------------------------------------------------
      def dwUnbindThing( self, thingKey ):
          rc = -1 

          logging.debug("[dwOpen] Sending UnBindThing Request...")
          postRequest = self.tr50.createUnbindThing( thingKey );
          logging.debug("[dwOpen] UnBindThing JSON Created: %s", postRequest)
 
          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] UnBindThing Response Received: %s", postResponse)

          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;

          return rc;

      #------------------------------------------------------------------------------
      #-- Function: dwLogPublish
      #-- Purpose:  Execute Log Publish Request
      #------------------------------------------------------------------------------
      def dwLogPublish( self, thingKey, msgText ):
          rc = -1 

          logging.debug("[dwOpen] Sending LogPublish Request...")
          postRequest = self.tr50.createLogPublish( thingKey, msgText );
          logging.debug("[dwOpen] LogPublish JSON Created: %s", postRequest)

          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] LogPublish Response Received: %s", postResponse)

          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;

          return rc;

      #------------------------------------------------------------------------------
      #-- Function: dwGetFile
      #-- Purpose:  Execute Get File  Request
      #------------------------------------------------------------------------------
      def dwGetFile( self, thingKey, filename ):
          rc = -1

          logging.debug("[dwOpen] Sending GetFile Request...") 
          postRequest = self.tr50.createGetFile( thingKey, filename );
          logging.debug("[dwOpen] GetFile JSON Created: %s", postRequest)

          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] GetFile Response Received: %s", postResponse)

          cmdId = self.getFramedText(postResponse, '{', ':{')
          temp = postResponse.replace(cmdId,'\"cmd\":')
          fileObj = json.loads(temp)
         
          if( postResponse.find("success\":true") > 0 ):
              fileObj = fileObj['cmd']['params']
              return 0, fileObj['crc32'], fileObj['fileId'], fileObj['fileSize']
          else:
              fileObj = fileObj['cmd']
              return rc, 0, fileObj['errorMessages'][0], str(fileObj['errorCodes'][0])
              
      #------------------------------------------------------------------------------
      #-- Function: dwPutFile
      #-- Purpose:  Execute Put File  Request
      #------------------------------------------------------------------------------
      def dwPutFile( self, thingKey, filename ):
          rc = -1

          logging.debug("[dwOpen] Sending PutFile Request...")   
          postRequest = self.tr50.createPutFile( thingKey, filename );
          logging.debug("[dwOpen] PutFile JSON Created: %s", postRequest)

          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] PutFile Response Received: %s", postResponse)

          if( postResponse.find("success\":true") > 0 ):
              cmdId = self.getFramedText(postResponse, '{', ':{')
              temp = postResponse.replace(cmdId,'\"cmd\":')
              fileObj = json.loads(temp)
              return 0, fileObj['cmd']['params']['fileId']
          else:
              return rc, None
              

      #------------------------------------------------------------------------------
      #-- Function: dwSessionInfo
      #-- Purpose:  Execute Session Info  Request
      #------------------------------------------------------------------------------
      def dwGetSessionInfo( self ):
          rc = -1

          logging.debug("[dwOpen] Sending SessionInfo Request...")
          postRequest = self.tr50.createSessionInfo( );
          logging.debug("[dwOpen] SessionInfo JSON Created: %s", postRequest)

          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] SessionInfo Response Received: %s", postResponse)

          if( postResponse.find("success\":true") > 0 ):
              rc = 0;


          return rc;

      #------------------------------------------------------------------------------
      #-- Function: dwSetAttribute
      #-- Purpose:  Execute Set Attribute Request
      #------------------------------------------------------------------------------
      def dwSetAttribute( self, thingKey, attribKey, attribValue ):
          rc = -1 

          logging.debug("[dwOpen] Sending SetAttribute Request...")
          postRequest = self.tr50.createSetAttribute( thingKey, attribKey, attribValue );
          logging.debug("[dwOpen] SetAttribute JSON Created: %s", postRequest)

          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] SetAttribute Response Received: %s", postResponse)

          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;

          return rc;

      #------------------------------------------------------------------------------
      #-- Function: dwLocationPublish
      #-- Purpose:  Execute Location Publish Request
      #------------------------------------------------------------------------------
      def dwLocationPublish( self, thingKey, locLatitude, locLongitude, locAltitude, locSpeed, locHeading, locFixType ):
          rc = -1 

          logging.debug("[dwOpen] Sending LocationPublish Request...")
          postRequest = self.tr50.createLocationPublish( thingKey, locLatitude, locLongitude, locAltitude, locSpeed, locHeading, locFixType );
          logging.debug("[dwOpen] LocationPublish JSON Created: %s", postRequest)
 
          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] LocationPublish Response Received: %s", postResponse)

          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;

          return rc;

      #------------------------------------------------------------------------------
      #-- Function: dwAlarmPublish
      #-- Purpose:  Execute Alarm Publish Request
      #------------------------------------------------------------------------------
      def dwAlarmPublish( self, thingKey, alarmKey, alarmState, alarmMsg ):
          rc = -1 

          logging.debug("[dwOpen] Sending AlarmPublish Request...")
          postRequest = self.tr50.createAlarmPublish( thingKey, alarmKey, alarmState, alarmMsg );
          logging.debug("[dwOpen] AlarmPublish JSON Created: %s", postRequest)
 
          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] AlarmPublish Response Received: %s", postResponse)

          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;

          return rc;

      #------------------------------------------------------------------------------
      #-- Function: dwPropertyPublish
      #-- Purpose:  Execute Property Publish Request
      #------------------------------------------------------------------------------
      def dwPropertyPublish( self, thingKey, propKey, propValue ):
          rc = -1 

          logging.debug("[dwOpen] Sending PropertyPublish Request...")
          postRequest = self.tr50.createPropertyPublish( thingKey, propKey, propValue );
          logging.debug("[dwOpen] PropertyPublish JSON Created: %s", postRequest)
 
          # Execute MQTT Send/Receive
          postResponse = self.mqttSendReceive( postRequest );
          logging.debug("[dwOpen] PropertyPublish Response Received: %s", postResponse)

          if( postResponse.find("success\":true") > 0 ):   
              rc = 0;

          return rc;
          
      
      #******************************************************************************
      #**** MQTT Helpers
      #******************************************************************************
          
      #------------------------------------------------------------------------------
      #-- Function: Callback - on_connect
      #------------------------------------------------------------------------------
      # The callback for when the client receives a CONNACK response from the server.
      def on_connect(self, client, userdata, flags, rc):
          logging.debug("[MQTT] Connected, Result Code: %s",str(rc))
          if (rc == 0):
              self._is_connected = True

          # print("---- Subscribing to Topic 'reply'...")
          # Subscribing in on_connect() means that if we lose the connection and
          # reconnect then subscriptions will be renewed.
          # client.subscribe("reply/#")
          # print("---- Subscribe Successful...")

      #------------------------------------------------------------------------------
      #-- Function: Callback - on_message
      #------------------------------------------------------------------------------
      # The callback for when a message is received from the server.
      def on_message(self, client, userdata, msg):
          th = threading.currentThread()
          logging.debug("[MQTT] Rx Message CB: %s on topic %s with QoS %s on Thread %s", str(msg.payload) ,
                  msg.topic,  str(msg.qos),  th.name)
          
          # Save the response. Other entities look for it  
          self.msgResp = str(msg.payload);
                    
           # if this is a mailbox activity, set an event to let others know         
          if( msg.topic == "notify/mailbox_activity" ): 
            self.mbox_event.set() 
           
          # If this is an remote invocation, put it on the action queue         
          if( str(msg.payload).find("\"command\":\"method.exec\"") > 0 ):  
             self.action_queue.put( str(msg.payload) )
              
          return
           
      #------------------------------------------------------------------------------
      #-- Function: Callback - on_subscribe
      #------------------------------------------------------------------------------
      # The callback for when a SUBSCRIBE to the server occurs.
      def on_subscribe(self, client, userdata, mid, granted_qos):
          logging.debug("[MQTT] Subscribe CB: %s with QoS %s", str(mid), str(granted_qos) ); 

      #------------------------------------------------------------------------------
      #-- Function: Callback - on_disconnect
      #------------------------------------------------------------------------------
      # The callback for when a DISCONNECT from the server occurs.
      def on_disconnect(self, client, userdata, rc):
          if rc != 0:
              logging.debug("[MQTT] Disconnect CB: %s", str(rc))
              
      #------------------------------------------------------------------------------
      #-- Function: Callback - on_log
      #------------------------------------------------------------------------------
      # The callback for when a debug LOG message arrives.
      def on_log(self, client, userdata, level, buf):
          logging.debug("[MQTT] Log CB: [%s] %s[", str(level), buf)
              
    
      #------------------------------------------------------------------------------
      #-- Function: mqttConnect
      #-- Purpose:  Connect to MQTT Broker
      #------------------------------------------------------------------------------
      #def mqttConnect( self, hostURL, thingKey, applToken, certFilePath, userCallback ):
      def mqttConnect( self, cfg, userCallback ):
          rc = -1;
          port = 1883

          hostURL = cfg.getConfig('cloud_host')
          thingKey = cfg.getConfig('device_id')
          applToken = cfg.getConfig('cloud_token')
          certFilePath = cfg.getConfig('certificate')
          clientId = self._getClientId(cfg.getConfig('base_dir') + '/clientId')

          print "clientID is " + clientId

          logging.debug("[MQTT] Configuring...")
          self.client.reinitialise(client_id=clientId, clean_session=True, userdata=None)

          self.client.username_pw_set( thingKey, applToken )
          if certFilePath != None:
              self.client.tls_set(certFilePath, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                        tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
              port = 8883
          self.client.on_connect = self.on_connect
          self.client.on_message = self.on_message
          self.client.on_subscribe = self.on_subscribe
          self.client.on_disconnect = self.on_disconnect
          self.client.on_log = self.on_log


          # Clear the mailbox event and start the Mailbox processing thread
          self.mbox_event.clear()
          mbox_thread = threading.Thread(target = self.dwMailboxThread)
          mbox_thread.start()
          logging.debug("[MQTT] mbox thread started. ID = %s", str(mbox_thread.ident))
          
          # Set the application method callback and start the thread to process 
          # method.exec requests
          self.myCallback = userCallback
          action_thread = threading.Thread(target = self.dwMethodExecThread)
          action_thread.start()
          logging.debug("[MQTT] action thread started. ID = %s", str(action_thread.ident))
          
          # Connect to the deviceWise service
          self._is_connected = False
          logging.debug("[MQTT] Attempting connect ...")
          self.client.connect(hostURL, port, 60)

          # Start MQTT processing
          logging.debug("[MQTT] Starting MQTT Processing Loop...")
          self.client.loop_start()

          # Wait for confirmation that the connection worked
          for i in range(0,6):
              time.sleep (1)
              if (self._is_connected == True):
                  break
             
          if (self._is_connected == False):
              return rc
    
          # Start MQTT processing
          # logging.debug("[MQTT] Starting MQTT Processing Loop...")
          # self.client.loop_start()

          # time.sleep( 2 )
 
          # Subscribe to everything under the "reply" topic
          logging.debug("[MQTT} Subscribing to Topic 'reply'...")
          self.client.subscribe("reply/#")
          logging.debug("[MQTT] Subscribe Submitted...")
         
          rc = 0;
          
          self.myAppToken = applToken;
          self.myThingKey = thingKey;
          self.dwApiHost  = hostURL;
          
          return rc;
          
      #------------------------------------------------------------------------------
      #-- Function: mqttDisconnect
      #-- Purpose:  Disconnect from the MQTT Broker
      #------------------------------------------------------------------------------
      def mqttDisconnect( self ):
          rc = -1;

          logging.debug("[MQTT] Shutting Down...")
          self.client.unsubscribe("reply");
          time.sleep( 2 )
          # self.client.loop_stop(force=False)
          self.client.disconnect()
          time.sleep( 2 )
        
          rc = 0;
          
          return rc;

      #------------------------------------------------------------------------------
      #-- Function: mqttCheck
      #-- Purpose:  Check/Service Incoming Messages
      #------------------------------------------------------------------------------
      def mqttCheck( self ):

          logging.debug ("[MQTT] Loop")
          self.client.loop();

          return 0;

      #------------------------------------------------------------------------------
      #-- Function: mqttSendReceive
      #-- Purpose:  Send command to the MQTT Broker (Topic: 'api')
      #------------------------------------------------------------------------------
      def mqttSendReceive( self, jsonText):

          #print jsonText

          self.msgId = self.msgId + 1;
          msgText = "\""+str(self.msgId).zfill(5)+"\":"; 
          jsonText = jsonText.replace("\"cmd\":", msgText);
          
          #print jsonText

          logging.debug("[MQTT] Send Message... (Topic: api) %s", jsonText )
          self.msgResp = ''
          self.client.publish("api", jsonText)

          
          #time.sleep( 0.25 ) 
          
          logging.debug("[MQTT] Message Sent, Awaiting Response...")
          timeloop = 0;
          

          while( timeloop < 100 and len( self.msgResp ) < 12 ):  
              time.sleep( 0.1 )
              timeloop = timeloop + 1    
              
              if (msgText in self.msgResp):
                  msgText = self.msgResp
                  break;

          logging.debug( "[MQTT] Debug: %s", self.msgResp)
          logging.debug( "[MQTT] Returning: %s",  msgText)
          return msgText;



