
class TR50protocol:

      includeSession = False   # If True, add sessionId to each message
      mySessionId = None       # SessionId storage

      #------------------------------------------------------------------------------
      #-- Function:  __init__
      #-- Purpose: Initialze the TR50 protocol layer
      #------------------------------------------------------------------------------
      def __init__(self):
          self.includeSession = True
          self.mySessionId = None

      #------------------------------------------------------------------------------
      #-- Function:  initTransport
      #-- Purpose: Initialze the TR50 transport variables
      #-- Arguements: transport ("mqtt" or 'rest")
      #-- Notes: If transport is "rest" we need to include sessionId on the start of 
      #--        every message. (TODO: Implement REST) 
      #------------------------------------------------------------------------------
      def initTransport(self, transport):
          if (transport == "rest"):
              self.includeSession = True
              self.sessionId = None
          elif (transport == "mqtt"):
              self.includeSession = False
              self.sessionId = None  
          else:
              return (-1)

          return (0)

      #------------------------------------------------------------------------------
      #-- Function: createSessionInfo
      #-- Purpose:  Generate JSON Session Info Request
      #------------------------------------------------------------------------------
      def createSessionInfo( self ):
          jsonText = "{ \"cmd\": { \"command\": \"session.info\"}}";
          return jsonText;
          
      #------------------------------------------------------------------------------
      #-- Function: createGetFile
      #-- Purpose:  Generate JSON File Get Request
      #------------------------------------------------------------------------------
      def createGetFile( self, thingkey, filename ):
          jsonText = "{ \"cmd\": { \"command\": \"file.get\", \"params\": { \"fileName\": " + "\"" + filename + "\"" +\
                     ", \"thingKey\":\"" + thingkey + "\" }}}";
          return jsonText;
          
      #------------------------------------------------------------------------------
      #-- Function: createPutFile
      #-- Purpose:  Generate JSON File Put
      #------------------------------------------------------------------------------
      def createPutFile( self, thingkey, filename ):
          jsonText = "{ \"cmd\": { \"command\": \"file.put\", \"params\": { \"fileName\": " + "\"" + filename + "\"" +\
                     ", \"thingKey\":\"" + thingkey + "\", \"public\": false }}}";
          return jsonText;
 
      #------------------------------------------------------------------------------
      #-- Function: createMailboxCheck 
      #-- Purpose:  Generate JSON Mailbox Check Request
      #------------------------------------------------------------------------------
      def createMailboxCheck( self ):
          jsonText = "{ \"cmd\": { \"command\": \"mailbox.check\", \"params\": { \"autoComplete\": true, \"limit\": 1 }}}";
          return jsonText;

      #------------------------------------------------------------------------------
      #-- Function: createMailboxUpdate
      #-- Purpose:  Generate JSON Mailbox Update Request
      #------------------------------------------------------------------------------
      def createMailboxUpdate( self, messageId, updateMsg ):
          jsonText = "{ \"cmd\": { \"command\": \"mailbox.update\", \"params\": {\"id\": \"" + messageId + "\", \"msg\": \"" + updateMsg + "\"}}}";
          return jsonText;

      #------------------------------------------------------------------------------
      #-- Function: createMailboxAck
      #-- Purpose:  Generate JSON Mailbox Ack Request
      #------------------------------------------------------------------------------
      def createMailboxAck( self, messageId, errorCode, errorMsg, compParams ):
      
          if not compParams:
             jsonText = "{ \"cmd\": { \"command\": \"mailbox.ack\", \"params\": {\"id\": \"" + messageId + "\", \"errorCode\": \"" + str(errorCode) + "\", \"errorMessage\": \"" + errorMsg + "\"}}}";
          else:
             jsonText = "{ \"cmd\": { \"command\": \"mailbox.ack\", \"params\": {\"id\": \"" + messageId + "\", \"errorCode\": \"" + str(errorCode) + "\", \"errorMessage\": \"" + errorMsg + "\", \"params\": " + compParams + " }}}";
          
          return jsonText;
   
      #------------------------------------------------------------------------------
      #-- Function: createBindThing 
      #-- Purpose:  Generate JSON Bind Thing Request
      #------------------------------------------------------------------------------
      def createBindThing( self, thingKey ):
          jsonText = "{ \"cmd\": { \"command\": \"thing.bind\", \"params\": { \"key\": \"" + thingKey + "\" } } }";
          return jsonText;
   
      #------------------------------------------------------------------------------
      #-- Function: createUnbindThing 
      #-- Purpose:  Generate JSON Unbind Thing Request
      #------------------------------------------------------------------------------
      def createUnbindThing( self, thingKey ):
          jsonText = "{ \"cmd\": { \"command\": \"thing.unbind\", \"params\": { \"key\": \"" + thingKey + "\" } } }";
          return jsonText;

      #------------------------------------------------------------------------------
      #-- Function: createLogPublish
      #-- Purpose:  Generate JSON Log Publish Request
      #------------------------------------------------------------------------------
      def createLogPublish( self, thingKey, msgText ):
          jsonText = "{ \"cmd\": { \"command\": \"log.publish\", \"params\": {\"thingKey\": \"" + thingKey + "\", \"msg\": \"" + msgText + "\"}}}";
          return jsonText;

      #------------------------------------------------------------------------------
      #-- Function: createPropertyPublish
      #-- Purpose:  Generate JSON Property Publish Request
      #------------------------------------------------------------------------------
      def createPropertyPublish( self, thingKey, propKey, propValue ):
          jsonText = "{ \"cmd\": { \"command\": \"property.publish\", \"params\": {\"thingKey\": \"" + thingKey + "\",\"key\": \"" + propKey + "\",\"value\": " + str(round(propValue,2)) + " }}}";
          return jsonText;

      #------------------------------------------------------------------------------
      #-- Function: createAlarmPublish
      #-- Purpose:  Generate JSON Alarm Publish Request
      #------------------------------------------------------------------------------
      def createAlarmPublish( self, thingKey, alarmKey, alarmState, alarmMsg ):
          jsonText = "{ \"cmd\": { \"command\": \"alarm.publish\", \"params\": {\"thingKey\": \"" + thingKey + "\", \"key\": \"" + alarmKey + "\", \"msg\": \"" + alarmMsg + "\", \"state\": " + str(alarmState) + "}}}";
          return jsonText;
      
      #------------------------------------------------------------------------------
      #-- Function: createLocationPublish
      #-- Purpose:  Generate JSON Location Publish Request
      #------------------------------------------------------------------------------
      def createLocationPublish( self, thingKey, locLatitude, locLongitude, locAltitude, locSpeed, locHeading, locFixType ):
          jsonText = "{ \"cmd\": { \"command\": \"location.publish\", \"params\": {\"thingKey\": \"" + thingKey + "\", \"lat\": \"" + locLatitude + "\", \"lng\": " + locLongitude + ", \"altitude\": " + locAltitude + ", \"speed\": " + locSpeed + ", \"alti\": " + locHeading + ", \"fixType\": \"" + locFixType + "\" }}}";
          return jsonText;
   
      #------------------------------------------------------------------------------
      #-- Function: createSetAttribute
      #-- Purpose:  Generate JSON Set Attribute Request
      #------------------------------------------------------------------------------
      def createSetAttribute( self, thingKey, attribKey, attribValue ):
          jsonText = "{ \"cmd\": { \"command\": \"attribute.publish\", \"params\": {\"thingKey\": \"" + thingKey + "\", \"key\": \"" + attribKey + "\", \"value\": \"" + attribValue + "\", \"republish\": false }}}";
          return jsonText;
      
      #------------------------------------------------------------------------------
      #-- Function: createGetAttribute
      #-- Purpose:  Generate JSON Get Attribute Request
      #------------------------------------------------------------------------------
      def createGetAttribute( self, thingKey, attribKey ):
          jsonText = "{ \"cmd\": { \"command\": \"attribute.current\", \"params\": {\"thingKey\": \"" + thingKey + "\", \"key\": \"" + attribKey + "\"}}}";
          return jsonText;

      #------------------------------------------------------------------------------
      #-- Function: createThingFind
      #-- Purpose:  Generate JSON Thing Find Request
      #------------------------------------------------------------------------------
      def createThingFind( self, thingKey ):
          jsonText = "{ \"cmd\": { \"command\": \"thing.find\", \"params\": {\"thingKey\": \"" + thingKey + "\"}}}";
          return jsonText;

