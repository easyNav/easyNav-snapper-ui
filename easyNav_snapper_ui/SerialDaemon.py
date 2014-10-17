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


    def start(self):
        self._ser = None
        try:
            self._ser = serial.Serial('/dev/rfcomm0', 115200)
        except SerialException as e:
            logging.error('Cannot open Serial port for B Field. Running without it.')
        self._active = True

        ## Run tick thread
        def runThread():
            while(self._active):
                self._tick()

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
        x = self.x = float(parsed[2])
        y = self.y = float(parsed[3])
        z = self.z = float(parsed[4])
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




