#!/usr/bin/python
# Load Python Import Libraries
import os
# import random
import json

class Config:

    configData = {}		# Dictionary with current confoguration date



    #----------------------------------------------------------------------------- 
    # -- Function: getConfig
    # -- Arguments: Key for the Value to return
    # -- Returns: Value 
    # --          None if key is not in dictionary
    #-----------------------------------------------------------------------------
    def getConfig(self, key):

        value = None

        if (key in self.configData.keys()):
            value = self.configData[key]

        return value
 

    #----------------------------------------------------------------------------- 
    # -- Function: processConfigFile
    # -- Arguments: Pathname to the configuration file
    # -- Returns:  0 - File processed and dictionary created
    # --          -1 - Any error
    #-----------------------------------------------------------------------------
    def processConfigFile(self, pathname):

        #----------------------------------------------------------------------------- 
        # -- Locate and read the configuration  file
        #-----------------------------------------------------------------------------
        cfgFilePath = os.path.abspath( str(pathname) )
        try:
             cfgFile = open(cfgFilePath, 'rb')
             config = json.loads(cfgFile.read())
             cfgFile.close()
        except IOError, arg:
             print "Could not find or read configuration file " + str(arg)
             return -1
        except JSONDecodeError, arg:
            print "Could not decode configuration file " + str(arg)
            return -1

        self.configData['cfg_file_path'] = cfgFilePath

        #----------------------------------------------------------------------------- 
        # -- Parse the configuration file standard attributes and stash then away
        #----------------------------------------------------------------------------- 
        stdAttributes = ['cloud_host', 'cloud_token', 'certificate', 
                         'device_id', 'serial_number', 'model_name', 
                         'vendor_id', 'fw_version', 'base_dir', 
                         'upload_base_path', 'dnload_base_path', 'log_dir'
                        ]
        for attribute in stdAttributes:
            if (attribute in config.keys()):
                self.configData[attribute] = str(config[attribute])
            else:
                self.configData[attribute] = None

        # If there is proxy info in the config file, pull it out 
        self.configData['has_proxy'] = False
        if ('proxy' in config.keys()):
            proxy = config['proxy']
            for p in ['url', 'port', 'type', 'username', 'password']:
                key = 'proxy_' + p
                self.configData[key] = None
                if (p in proxy.keys()):
                    if (str(proxy[p]) != ""):
                        self.configData[key] = proxy[p]

        if (self.configData['proxy_type'] != None and 
            self.configData['proxy_url'] != None):
            self.configData['has_proxy'] = True

        #----------------------------------------------------------------------------- 
        # -- Figure out what the base runtime directory is.  Algorithm is:
        # -- Use the base_dir value in the configuration file
        # -- Else use the basename of the configuration file
        #-----------------------------------------------------------------------------
        baseDir = self.configData['base_dir']
        if (baseDir == None):
            baseDir = os.path.dirname(cfgFilePath)

        if ( os.path.isabs(baseDir) == False or os.path.isdir(baseDir) == False ):
            print "Base Direcrory must be an an absolute pathname to a directory"
            return -1
        else:
            self.configData['base_dir'] = baseDir 

        #----------------------------------------------------------------------------- 
        # -- Check and adjust (as necessary) the required pathnames
        #----------------------------------------------------------------------------- 
        d2cDir = self.configData['upload_base_path']
        # Find the user specified  d->c directory
        if (d2cDir == None):
            d2cDir = "upload"

        # If it is an absolute path, use it, else assume d2cDir is under base dir
        if os.path.isabs(d2cDir) == False:
            d2cDir = os.path.join(baseDir, d2cDir)

        self.configData['upload_base_path'] =  d2cDir

        # Find the user specified  c->d directory
        c2dDir = self.configData['dnload_base_path'] 
        if (c2dDir == None):
            c2dDir = "download"
   
        # If it is an absolute path, use it, else assume c2dDir is under base dir 
        if os.path.isabs(c2dDir) == False:
            c2dDir = os.path.join(baseDir, c2dDir)

        self.configData['dnload_base_path'] = c2dDir

        # Find the user specified log directory
        logDir = self.configData['log_dir']
        if (logDir == None):
            logDir = 'logs'

        # If it is an absolute path, use it, else assume it is under base dir 
        if os.path.isabs(logDir) == False:
            logDir = os.path.join(baseDir, logDir)

        self.configData['log_dir'] = logDir

        #----------------------------------------------------------------------------- 
        # -- Check that we are not missing any required configuration items
        #----------------------------------------------------------------------------- 
        if ( self.configData['base_dir'] == None or
             self.configData['upload_base_path'] == None or
             self.configData['dnload_base_path'] == None or
             self.configData['log_dir'] == None or
             self.configData['device_id'] == None or
             self.configData['cloud_host'] == None or
             self.configData['cloud_token'] == None ):
            print "Missing required configuration item(s)"
            return -1

        return 0


# =============================================================================
# == Test code
# =============================================================================

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument ("--cfg", dest="cfgFile", help="Path to configuration file")
    args = parser.parse_args()

    cfg = Config()

    ret = cfg.processConfigFile(args.cfgFile);

    print ( "Base Dir:    " + cfg.getConfig('base_dir') )
    print ( "C2D Dir:     " + cfg.getConfig('upload_base_path') )
    print ( "D2C Dir:     " + cfg.getConfig('dnload_base_path') )
    print ( "Log Dir:     " + cfg.getConfig('log_dir') )
    print ( "Config File: " + cfg.getConfig('cfg_file_path') )
    print ( "Device ID:   " + cfg.getConfig('device_id') )
    print ( "ApiHost:     " + cfg.getConfig('cloud_host') )
    print ( "AppToken:    " + cfg.getConfig('cloud_token') )
    print ( "Cert File:   " + cfg.getConfig('certificate') )
    if cfg.getConfig('has_proxy') == True:
        print ( "Proxy URL:   " + cfg.getConfig('proxy_url') )
        print ( "Proxy Port:  " + str(cfg.getConfig('proxy_port')) )
        print ( "Proxy Type:  " + cfg.getConfig('proxy_type') )
        print ( "Proxy User:  " + cfg.getConfig('proxy_username') )
        print ( "Proxy Pass:  " + cfg.getConfig('proxy_password') )

    exit(0) 
