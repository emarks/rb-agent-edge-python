#!/usr/bin/python
#==============================================================================
#== Title: dwPY_OpenMQTT.py
#== Description:  Simple MQTT/JSON Python Edge Device Client (Python - Paho MQTT Library)
#==
#== Copyright (c)2015 Telit
#== http://www.ilstechnology.com
#== http://www.devicewise.com
#==
#== To Execute:
#== python dwPY_OpenMQTT.py
#==
#== Legal Disclaimer:
#==
#== THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#== INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#== PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#== HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#== OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#== SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#==============================================================================

# Load Python Import Libraries
import config
import sys
import os
import time
import threading
import dwopenmqtt
import random
import threading
import requests
import argparse
import json
import zipfile
import tempfile
import subprocess
import logging

# dwM2M Developer Community Assigned Tokens...
dwApiURL    = "http://api.devicewise.com/api"
dwApiHost   = "api.devicewise.com"

# dwOpen Member/Thing Assigned Tokens...
# dwAppToken  = "8qlbtIxXAQv6LVGy"
dwAppToken =  "4uIXhHGFkiyi4xJV"
# dwThingKey  = "ubuntuthing"

verString = "PoC 0.2.0"
baseDir = ""
c2dDir = ""
d2cDir = ""
logDir = ""

debugFlg = False

telemetry_enable = 0
processing = False


# =============================================================================
# == Function: actionCallBack
# == Purpose:  Handles Method (aka Action) Callbacks
# =============================================================================
def actionCallBack( MsgID, MethodName, ParamText ):

    global telemetry_enable
    global processing
    
    # -------------------------------------------------------------------------      
    # File transfer from cloud to device
    #  - Get the cloud file and device path paramaters
    #  - Send command to cloud to "get" the file.  It will return a URL to GET
    #  - Use requests to issue a GET on the URL returned in previous step
    #  - Save the file to the device_path
    #  - Send a log message to the cloud indicating completion status
    #
    # Note:  Really need to add error checking in a lot of places   
    # -------------------------------------------------------------------------
        
    if( MethodName == "c2dfilexfer" ):

        # Get the pathname to where file should reside on the device 
        device_path = dwopen.getFramedText(ParamText, '\"devicepath\":', ',')
        
        # Strip off and leading/trailing quotation marks
        if device_path.startswith('"') and device_path.endswith('"'):
            device_path = device_path[1:-1]
        
        # If the user specified an absolute pathname then use it,
        # else assume it in the specified file store
        if device_path[0] != '/':
            device_path = os.path.join(config.getConfig('dnload_base_path'), device_path)
      
        # Get the name of the file on the cloud
        cloud_file = dwopen.getFramedText(ParamText, '\"cloudfile\":', ',')

        # Strip off any leading/trailing quotation marks 
        if cloud_file.startswith('"') and cloud_file.endswith('"'):
            cloud_file = cloud_file[1:-1]

        # Get the overwrite flag
        overWrite = dwopen.getFramedText(ParamText, '\"overwrite\":', '}')

        logging.info ("[ACTION] C2DFILEXFER: %s to %s Overwrite: %s", cloud_file, device_path, str(overWrite))

        # Check if this will cause an overwrite error on the device before going any further
        if overWrite == "false":
            if os.path.exists(device_path):
                msg = "C2D File Transfer failed. File already exists"
                logging.info ("[ACTION] C2DFILEXFER:  %s", msg)
                dwopen.dwMailboxAck( MsgID, 0, msg, '' )
                return
            
        # Send a request to the cloud to get URL and other info needed to GET the file
        rc,crc,fileId,fileSize = dwopen.dwGetFile(config.getConfig('device_id'), cloud_file)
        if rc != 0:
            errmsg = fileId
            errnum = fileSize
            msg = "C2D File Transfer failed " + errmsg + " " + errnum
            logging.info ("[ACTION] C2DFILEXFER:  %s", msg)
            dwopen.dwMailboxAck( MsgID, 0, msg, '' )
            return
   
        # Pull the file from the cloud and store it at the specified path on the device
        # This is done in 1K chunks so as not to consume lots of memory when a large file
        # is being transferered.
        msg = "C2D File Transfer " + cloud_file + " to " + device_path + " "
        with open(device_path, 'wb') as file_handle:
            r = requests.get("http://api.devicewise.com/file/" + fileId)
            if not r.ok:
                msg = msg + "failed (" + r.status_code + ")"
                file_handle.close()
                os.remove(device_path) 
            else:
                for chunk in r.iter_content(chunk_size = 1024):
                    file_handle.write(chunk)
                msg = msg + "complete"
                file_handle.close()
            
        # Ack the method request
        logging.info ("[ACTION] C2DFILEXFER:  %s", msg)
        dwopen.dwMailboxAck( MsgID, 0, msg, '' )  
            
        # Create a log entry on cloud that the file was transferred    
        dwopen.dwLogPublish( config.getConfig('device_id'), msg )
                 
        return
    
    # -------------------------------------------------------------------------         
    # File transfer from device to cloud
    #  - Get the cloud file and device path paramaters
    #  - Send command to cloud to "put" the file.  It will return a URL to POST
    #  - Use requests to issue a POST on the URL returned in previous step
    #  - Stream the file to the requests module
    #  - Send a log message to the cloud indicating completion status
    #
    # Note:  Really need to add error checking in a lot of places
    # -------------------------------------------------------------------------
            
    if ( MethodName == "d2cfilexfer" ):

        # Get the name of the file on the cloud
        cloud_file = dwopen.getFramedText(ParamText, '\"cloudfile\":', ',')

        # Strip off any leading/trailing quotation marks
        if cloud_file.startswith('"') and cloud_file.endswith('"'):
            cloud_file = cloud_file[1:-1]

        # Get the name of the file on the device
        device_path = dwopen.getFramedText(ParamText, '\"devicepath\":', '}')
        
        # Strip off any leading/trailing quotation marks    
        if device_path.startswith('"') and device_path.endswith('"'):
            device_path = device_path[1:-1]
        
        # If the user specified an absolute pathname then use it,
        # else assume it in the specified file store
        if device_path[0] != '/':
             device_path = os.path.join(config.getConfig('upload_base_path'), device_path)
        
        logging.info ("[ACTION] D2CFILEXFER: %s to %s", device_path, cloud_file)

        # Check that the file exists before we go any further
        if os.path.exists(device_path) == False:
            msg = "D2C File Transfer failed. Can not find file: " + device_path
            logging.info ("[ACTION] D2CFILEXFER: %s", msg)
            dwopen.dwMailboxAck( MsgID, 0, msg, '' )
            return

        # Send request to the cloud to get the URL to POST the file to
        rc,fileId = dwopen.dwPutFile(config.getConfig('device_id'), cloud_file)
        post_url = "http://api.devicewise.com/file/" + fileId
            
        # Stream the file to the cloud
        msg = "D2C File Transfer " + device_path + " to " + cloud_file + " "
        with open(device_path, 'rb') as file_handle:
            r = requests.post(post_url, data=file_handle)
            if not r.ok:
                msg = msg + "failed (" + r.status_code + ")"
            else:
                msg = msg + "complete"
            file_handle.close()
        
        logging.info ("[ACTION] D2CFILEXFER: %s", msg)
      
        # Ack the method
        dwopen.dwMailboxAck( MsgID, 0, msg, '' )            
             
        # Create a log entry on cloud that the file was transferred     
        dwopen.dwLogPublish( config.getConfig('device_id'), msg )
                   
        return
        
    # SW Update Operation
    #  - Get the path to the archive to process
    #  - Unwind the archive
    #  - Get the manifest
    #  - Process the manifest
    #  - Send a log message to the cloud indicating completion status
    #
    # Note:  Really need to add error checking in a lot of places
            
    if ( MethodName == "swupdate" ):
        device_path = dwopen.getFramedText(ParamText, '\"devicepath\":', '}')
            
        if device_path.startswith('"') and device_path.endswith('"'):
            device_path = device_path[1:-1]
        
        # If the user specified an absolute pathname then use it,
        # else assume it in the specified file store
        if device_path[0] != '/':
            device_path = os.path.join(config.getConfig('base_dir'), device_path)
        
        logging.info ("[ACTION] SWUPDATE: %s", device_path)

        # Unwind the archive and read the manifest
        if (zipfile.is_zipfile(device_path) == False):
            msg = "Software Update failed. Improperly formatted file: " + device_path 
            logging.info ("[ACTION] SWUPDATE: %s", msg)
            dwopen.dwMailboxAck( MsgID, 0, msg, '' )
            dwopen.dwLogPublish( config.getConfig('device_id'), msg )
            return 

        # Create a place to store the contents of the Update Package
        tmpDir = tempfile.mkdtemp(dir=baseDir, prefix='swupdate-')
        logging.info( "[ACTION] SWUPDATE: Create temp dir: %s", tmpDir)
       
        # Extract the Update Package into the temprary directory 
        z = zipfile.ZipFile(device_path, 'r')
        z.extractall(tmpDir)
        z.close()
        logging.info ("[ACTION] SWUPDATE: Extract conplete")
        
        try:
           metafile = open( os.path.join(tmpDir, 'update.json'), 'rb')
           manifest = metafile.read();
           update = json.loads(manifest);
           metafile.close()
        except:
           msg = "Error processing update.json"
           logging.info ("[ACTION] SWUPDATE: %s", msg)
           dwopen.dwMailboxAck( MsgID, 0, msg, '' )
           dwopen.dwLogPublish( config.getConfig('device_id'), msg )
           return
               
        # Execute the contents of the manifest
        name = str(update['name'])
        description = str(update['description'])
        pre_install = "sh " + os.path.join(tmpDir, str(update['pre_install']))
        install = "sh " + os.path.join(tmpDir, str(update['install']))
        post_install =  "sh " + os.path.join(tmpDir, str(update['post_install'])) + " " + logDir

        logging.info ("[ACTION] SWUPDATE: Processing: %s", str(update['name']))
        logging.info ("[ACTION] SWUPDATE: Description: %s", str(update['description']))
        logging.info ("[ACTION] SWUPDATE: Taking the following actions:")
        logging.info ("[ACTION] SWUPDATE:    Running Pre-Install:  %s", pre_install)
        subprocess.check_call(pre_install, shell=True)
        logging.info ("[ACTION] SWUPDATE:    Running  Install:     %s", install)
        subprocess.check_call(install, shell=True)
        logging.info ("[ACTION] SWUPDATE:    Running Post-Install: %s",  post_install)
        subprocess.check_call(post_install, shell=True)


        # Ack the method
        msg = "Software Update " + str(update['name']) +  " complete"
        logging.info ("[ACTION] SWUPDATE: %s", msg)

        dwopen.dwMailboxAck( MsgID, 0, msg, '' )            
             
        # Create a log entry on cloud that the file was transferred     
        dwopen.dwLogPublish( config.getConfig('device_id'), msg )
                   
        return
               
    # Toggle telemetry
    #  - Get the desired telemetry state (on/off)
    #  - Set a global used elsewhere to enable/disable telemtry
    #
    # Note:  Really need to add error checking in a lot of places        
    if( MethodName == "toggletelemetry" ):
        value = dwopen.getFramedText(ParamText, '\"vartelemetry\":', '}')
            
        if (value == "true"):
            telemetry_enable = 1
            logging.info ("[ACTION] TELEMETRY: ON")
            dwopen.dwMailboxAck( MsgID, 0, 'Telemetry Enabled', '' )
        else:
            telemetry_enable = 0
            logging.info ("[ACTION] TELEMETRY: OFF")
            dwopen.dwMailboxAck( MsgID, 0, 'Telemetry Disabled', '' )
                
        return
     
     
    # Stop the agent
    #  - Get the desired telemetry state (on/off)
    #  - Set a global used elsewhere to enable/disable telemtry
    #
    # Note:  Really need to add error checking in a lot of places        
    if( MethodName == "stopagent" ):
        logging.info ("[ACTION] AGENT STOP")
        dwopen.dwMailboxAck( MsgID, 0, "User requested Agent stop", '' )
        dwopen.dwMailboxAck( MsgID, 0, 'Agent Stopping', '' )
        time.sleep( 3 )
        processing = False
        
        return
         

    # Set the Agent debug level
    #  - Find he level requested
    #  - Set the logging module to the level requested
    #
    # Note:  Really need to add error checking in a lot of places        
    if( MethodName == "debuglvl"):
        logging.info ("[ACTION] SET AGENT DEBUG LEVEL")

        level = dwopen.getFramedText(ParamText, '[\"', '\"]')
        logging.info ("[ACTION] AGENTDBG %s", level)
        # logger = logging.getLogger()
 
        if (level == "debug"):
            logger.setLevel(logging.DEBUG)
        elif (level == "info"):
            logger.setLevel(logging.INFO)
        elif (level == "none"):
            logger.setLevel(logging.ERROR)

        dwopen.dwMailboxAck( MsgID, 0, "Agent Debug Level " + str(level), '')
        
        return
            
    # Get  here if we didn't find the requested method (BAD)       
    logging.info ("[ACTION] Unimplemeted method !")
    dwopen.dwMailboxAck( MsgID, -1, 'Unimplemented method', '' )
            
    return
  
# =============================================================================
# == Function: processLoop
# == Purpose:  Telemetry Processing Loop
# =============================================================================  
def processLoop():

    global processing
    
    logging.info ("[LOOP] Starting Main Loop")

    processing = True
    LastSensorValue = -1

    while (processing): 
                       
        # Wait here for about 5 seconds for cloud methods before proceeding
        for i in range(0,5):
            time.sleep( 1 )

        # Read some sensor, process the data, send stuff to the cloud
      
        if (telemetry_enable == 1):
            # Read sensor value from potentiometer
            sensor_value = random.randint(0,100)

            # Did the potentiometer value change?
            if sensor_value <> LastSensorValue:
                logging.info ("[LOOP] Sending Metric \"CPU Load\"=%s", str(sensor_value))
                rc = dwopen.dwPropertyPublish( config.getConfig('device_id'), "cpuload", sensor_value )
            
                if sensor_value <= 20:
                    alarmState = 0;
                    alarmMsg = "Load - Normal"
                else:
                    if (sensor_value <= 60):
                        alarmState = 1
                        alarmMsg = "Load - Warning"
                    else:
                        alarmState = 2
                        alarmMsg = "Load - HIGH"
               
                logging.info ("[LOOP] Sending Alarm: %s", alarmMsg)     
                rc = dwopen.dwAlarmPublish( config.getConfig('device_id'), "cpuload", alarmState, alarmMsg )
        
                LastSensorValue = sensor_value

    print "[LOOP] Exiting Main Loop"
    return
    
  
# =============================================================================
# == Main Program Starts (and Ends) Here
# =============================================================================

if __name__ == '__main__':

    # Display Banner Information...
    print "HDC NG Python Agent  (TR50/MQTT)"
    print "Version " + verString

    #-----------------------------------------------------------------------------
    # -- Parse the command line arguements
    #-----------------------------------------------------------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument ("--cfg",     dest="cfgFile", help="Path to configuration file")
    parser.add_argument ("--basedir", dest="baseDir", help="Specify base path to operate from")
    parser.add_argument ("--debug",   dest="dbgLevel", help="Emit debug/logging information (info | debug)")
    args = parser.parse_args()

    # Deal with debug flag (This can go away when we add trace)
    if (args.dbgLevel == "info"):
        # logging.setLevel (logging.INFO)
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    elif (args.dbgLevel == "verbose"):
        # logging.setLevel (logging.DEBUG)
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.ERROR)

    logger = logging.getLogger(__name__)


 
    #----------------------------------------------------------------------------- 
    # -- Locate and read the iot.cfg file
    #-----------------------------------------------------------------------------
    config = config.Config()

    ret = config.processConfigFile(args.cfgFile)
    if (ret != 0):
        print "Could not find or read configuration file " + str(arg)
        exit (1)

    #-----------------------------------------------------------------------------
    #-- Load the low level communication library
    #-----------------------------------------------------------------------------
    logging.debug("Loading Protocol Library...")
    dwopen = dwopenmqtt.dwOpen()
    logging.debug("Protocol Library Loaded...")

    #-----------------------------------------------------------------------------
    #-- Connect to the Cloud Server
    #-----------------------------------------------------------------------------
    logging.debug("Connecting to Cloud Server...")
    # rc = dwopen.mqttConnect( config.getConfig('cloud_host'),
    #                          config.getConfig('device_id'),
    #                          config.getConfig('cloud_token'),
    #                          config.getConfig('certificate'),
    #                          actionCallBack )
    rc = dwopen.mqttConnect( config, actionCallBack )
    logging.debug("Connect Returned... rc = %s", str(rc))
    if (rc != 0):
        logging.debug("Failed to connect");
        os._exit(0) 

    #-----------------------------------------------------------------------------
    #-- Do something to prove we're connected
    #--  TODO: Change this to do a diag.ping
    #-----------------------------------------------------------------------------
    logging.debug("Getting Session info")
    rc = dwopen.dwGetSessionInfo()
    logging.debug("Session Info Returned... rc = %s", str(rc))

    #-----------------------------------------------------------------------------
    #-- Set the device attributes
    #-----------------------------------------------------------------------------
    attrList = {
        "public-hostname" : "http://169.254.169.254/latest/meta-data/public-hostname",
        "local-hostname" : "http://169.254.169.254/latest/meta-data/local-hostname",
        "public-ipv4": "http://169.254.169.254/latest/meta-data/public-ipv4",
        "local-ipv4" : "http://169.254.169.254/latest/meta-data/local-ipv4",
        "mac-addr" : "http://169.254.169.254/latest/meta-data/network/interfaces/macs",
        "instance-id" : "http://169.254.169.254/latest/meta-data/instance-id"
        }

    # Start with the EC2 instance attributes
    for key in attrList:
        try:
            attribKey   = key
            attrUrl = attrList[key]
            r = requests.get(attrUrl)
            if not r.ok:
                logging.info("Could not read " + attrList[key])
                raise Exception('Getting EC2 instance data')
            if attribKey != 'mac-addr':
                attribValue = r.text
            else:
                attribValue = r.text.rstrip('/')
            print "Setting " + attribKey + " to " + attribValue
            rc = dwopen.dwSetAttribute( config.getConfig('device_id'), attribKey, attribValue )
            if rc != 0:
                raise Exception('Sending standard device  attributes')
        except Exception as issue:
            print str(type(issue)) + " " +  str(issue.args)
      
   # Then the standard attributes from the configuration file
    attributes = ['serial_number', 'model_name', 'vendor_id', 'fw_version']
    for attribute in attributes:
        try:
            attribKey   = attribute
            attribValue = config.getConfig(attribute)
            print "Setting " + attribKey + " to " + attribValue
            rc = dwopen.dwSetAttribute( config.getConfig('device_id'), attribKey, attribValue )
            if rc != 0:
                raise Exception('Sending standard device  attributes')
        except Exception as issue:
            print str(type(issue)) + " " +  str(issue.args)
 
    #-----------------------------------------------------------------------------
    #-- Call the main processing loop. Will not return until user terminates agent
    #-----------------------------------------------------------------------------
    processLoop ()
    
    #-----------------------------------------------------------------------------
    #-- Disconnect from the  Cloud Server
    #-----------------------------------------------------------------------------
    logging.debug("Disconnecting from Cloud Server...")
    dwopen.mqttDisconnect()

    # Exiting the Application...
    print( "Exiting... Good Bye!" )
    
    os._exit(0)  # Its a hammer but it kills threads too
 
