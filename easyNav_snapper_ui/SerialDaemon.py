#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of easyNav-snapper-ui.
# https://github.com/easyNav/easyNav-snapper-ui

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2014 Joel Tong me@joeltong.org


import serial
from serial import SerialException
import time
import math
import logging
import threading

import smokesignal


class SerialDaemon:
    """ Daemon to retrieve sensor values from phone. 
    """

    def __init__(self):
        self._ser = None
        self._active = False
        self.x, self.y, self.z, self.intensity = 0,0,0,0




    def configure(self, port='/dev/rfcomm0', sensorToUse='phone'):
        """Sets configuration parameters
        """
        if (sensorToUse == 'phone'):
            self._config = {
                'sensor': 'phone',
                'port': port,
                'baudrate': 115200
            }
        elif (sensorToUse == 'shoe'):
            self._config = {
                'sensor': 'shoe',
                'port': port,
                'baudrate': 57600
            }

        print self._config


    def start(self):
        self._ser = None
        logging.info("PORT: %s" % self._config['port'])
        try:
            self._ser = serial.Serial(self._config['port'], self._config['baudrate'])
        except SerialException as e:
            logging.error('Cannot open Serial port for B Field. Running without it.')
        self._active = True

        ## Run tick thread
        def runThread():
            while(self._active):
                self._tick()
                if (self._ser == None):
                    time.sleep(1) # To prevent overheating due to loop re-entry

        self._threadListen = threading.Thread(target=runThread)
        self._threadListen.start()
        print 'Serial Daemon: Thread started.'


    def stop(self):
        self._active = False
        self._threadListen.join()
        if (self._ser != None):
            self._ser.close()
        logging.info('Serial Daemon: Thread stopped.')


    def _tick(self):
        raw = '0,0,0,0,0'
        if (self._ser != None):
            try:
                raw = self._ser.readline()
            except SerialException as e:
                logging.error('Serial - unable to read data')
                pass
        parsed = raw.split(',')

        x,y,z = 0,0,0
        if (self._config['sensor'] == 'phone'):
            x = self.x = float(parsed[2])
            y = self.y = float(parsed[3])
            z = self.z = float(parsed[4])
        else: #shoe
            #YPRMfssT=,1.67,-53.00,12.33,1.08,0.01,0.11,-0.99,8.00,0,1,
            x = self.x = float(parsed[1])
            y = self.y = float(parsed[2])
            z = self.z = float(parsed[3])

        # logging.info(x,y,z)

        self.intensity = (x**2  +y**2 + z**2)**0.5
        smokesignal.emit('onData', self.x, self.y, self.z, self.intensity)



######################################################
## This is the main function, to show example code.
######################################################

if __name__ == '__main__':
    def configLogging():
        logging.getLogger('').handlers = []

        logging.basicConfig(
            # filename = "a.log",
            # filemode="w",
            level = logging.DEBUG)


    @smokesignal.on('onData')
    def onDataHandler(x,y,z,intensity):
        """ Event callback for serial data 
        """
        logging.info('Serial Daemon: New Data!')
        print (x,y,z,intensity)


    configLogging()
    sd = SerialDaemon()
    sd.start()
    time.sleep(5)
    sd.stop()




