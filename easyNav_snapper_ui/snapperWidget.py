#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of easyNav-snapper-ui.
# https://github.com/easyNav/easyNav-snapper-ui

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2014 Joel Tong me@joeltong.org


from gi.repository import Gtk, GObject
import logging
import threading
import smokesignal
import time

from easyNav_snapper import Snapper
from SerialDaemon import SerialDaemon
from easyNav_sensors_wifi import SensorWifiDaemon


GObject.threads_init()


class SnapperWidget(Gtk.Window):
    def __init__(self):
        import os
        print os.getcwd()

        ## File accessed from parent folder.
        filename = "easyNav_snapper_ui/snapTemplate.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(filename)
        self.builder.connect_signals(self)

        ## For Snapper stuff 
        self.snapper = Snapper()
        self.saveFilepath = None

        ## For SerialDaemon stuff
        sd = self.sd = SerialDaemon()

        ## For wifi stuff 
        self.networksLock = threading.Lock() # make wifi data atomic
        swd = self.swd = SensorWifiDaemon(interval=1.0, interface='wlan0')

        ## Attach data handlers
        self._attachHandlers()
        sd.start()
        swd.start()

        ## For collection start / stop button and actions
        self._isCollecting = False


        ## for the store
        self.store = Gtk.ListStore(int, str, str)
        tree = self.builder.get_object('treeview3')
        tree.set_model(self.store)


        ## for B field details.  This is needed to prevent the delay observed on reading
        ## from text field.
        self.bField = {
        'x': 0,
        'y': 0,
        'z': 0,
        'intensity': 0
        }


        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Target", renderer, text=0)
        column.set_sort_column_id(0)
        tree.append_column(column)

        column2 = Gtk.TreeViewColumn("Data", renderer, text=1)
        tree.append_column(column2)

        ## update the builder
        self.builder.get_object('window1').show_all() 


    def clearTreeView(self):
        """ Clears the tree view 
        """
        self.store.clear()


    def populateTreeView(self):
        """ Populates tree with store items.  used for load.
        """
        for item in self.snapper.data:
            treeiter = self.store.append([
                        item.get('target'),
                        str(item.get('data')),
                        str(item.get('uuid')) ])



    def on_treeview3_cursor_changed(self, args):
        pass


    def on_btnDelete_clicked(self, args):
        tree = self.builder.get_object('treeview3')
        model, itr = tree.get_selection().get_selected()
        uuid = model[itr][2]
        model.remove(itr)
        self.snapper.remove(int(uuid))


    def _updateBField(self, x,y,z,intensity):
        self.builder.get_object('bField_x').set_text(str(x))
        self.builder.get_object('bField_y').set_text(str(y))
        self.builder.get_object('bField_z').set_text(str(z))
        self.builder.get_object('bField_norm').set_text(str(intensity))
        


    def _attachHandlers(self):
        """Event listeners 
        """
        ## TODO: Does not trigger when GTK starts.  Maybe try fork?
        @smokesignal.on('onData')
        def onDataHandler(x,y,z,intensity):
            """ Event callback for serial data 
            """
            self.bField = {
            'x': x,
            'y': y,
            'z': z,
            'intensity': intensity
            }
            ## TODO: Remove the display.  might slow down system.
            # GObject.idle_add(self._updateBField, x,y,z,intensity)
            # logging.info('Serial Daemon: New Data!')

            # print (x,y,z,intensity)

        @smokesignal.on('onNetworkData')
        def onNetworkDataHandler(networks):
            """Event callback for wifi data 
            """
            result = {}
            for n in networks:
                essid = str(n['Address']) 
                result[essid] = int(n['Quality'])

            ## Write data to atomic self.networks
            self.networksLock.acquire()
            self.networks = result
            self.networksLock.release()




    def buttonWriteNameToFile_clicked(self, widget):
        print("File write code...")


    def on_window1_destroy(self, *args):
        """ Closes the main program
        """
        self.sd.stop()
        self.swd.stop()
        Gtk.main_quit()


    def on_imagemenuitem2_activate(self, args):
        """ Load file 
        """
        print 'selected menu'
        chooser_dialog = Gtk.FileChooserDialog(title='Load file..'
            , action=Gtk.FileChooserAction.OPEN
            , buttons=["Open", Gtk.ResponseType.OK, "Cancel", Gtk.ResponseType.CANCEL])

        pyFilter = Gtk.FileFilter()
        pyFilter.add_mime_type('text/x-python')
        pyFilter.add_pattern('*.py')
        pyFilter.set_name('Python files')

        response = chooser_dialog.run() 

        if response == Gtk.ResponseType.OK:
            filename = chooser_dialog.get_filename()

            # Load information into snapper 
            self.snapper.load(filename)

            # populate treeview
            self.clearTreeView()
            self.populateTreeView()

            self.builder.get_object('statusbar1').push(0, 'File %s loaded.' % filename)

        elif response == Gtk.ResponseType.CANCEL:
            pass
        chooser_dialog.destroy()


    def on_imagemenuitem4_activate(self, args):
        """ Save as.. 
        """

        print 'selected menu'
        chooser_dialog = Gtk.FileChooserDialog(title='Load file..'
            , action=Gtk.FileChooserAction.SAVE
            , buttons=["Save as..", Gtk.ResponseType.OK, "Cancel", Gtk.ResponseType.CANCEL])

        Gtk.FileChooser.set_do_overwrite_confirmation(chooser_dialog, True)

        pyFilter = Gtk.FileFilter()
        pyFilter.add_mime_type('text/x-python')
        pyFilter.add_pattern('*.py')
        pyFilter.set_name('Python files')


        response = chooser_dialog.run() 

        if response == Gtk.ResponseType.OK:
            filename = chooser_dialog.get_filename()

            # Save information from snapper 
            self.snapper.save(filename)

            self.builder.get_object('statusbar1').push(0, 'File %s loaded.' % filename)

        elif response == Gtk.ResponseType.CANCEL:
            pass
        chooser_dialog.destroy()


    def on_btnExport_activate(self, args):
        """ Export to SVM Light format
        """
        print 'selected menu'
        chooser_dialog = Gtk.FileChooserDialog(title='Load file..'
            , action=Gtk.FileChooserAction.SAVE
            , buttons=["Export to..", Gtk.ResponseType.OK, "Cancel", Gtk.ResponseType.CANCEL])

        Gtk.FileChooser.set_do_overwrite_confirmation(chooser_dialog, True)

        pyFilter = Gtk.FileFilter()
        pyFilter.add_mime_type('text/x-python')
        pyFilter.add_pattern('*.py')
        pyFilter.set_name('Python files')


        response = chooser_dialog.run() 

        if response == Gtk.ResponseType.OK:
            filename = chooser_dialog.get_filename()

            # Save information from snapper 
            self.snapper.export(filename)

            self.builder.get_object('statusbar1').push(0, 'SVMLight File %s exported.' % filename)

        elif response == Gtk.ResponseType.CANCEL:
            pass
        chooser_dialog.destroy()


    def on_btnWifiUpdate_clicked(self, args):
        """ Button to update wifi interval and port 
        """
        wifiInterval = float(self.builder.get_object('wifiInterval').get_text())
        wifiPort = str(self.builder.get_object('wifiPort').get_text())
        self.swd.updateConfig(wifiInterval, wifiPort)
        self.builder.get_object('statusbar1').push(
            0, 'Updated WIFI: port=%s interval=%s' % (wifiPort, wifiInterval))




    def on_btnAdd_clicked(self, args):
        """ Add a new Entry
        """
        ## Run tick thread
        def runThread():
            while(self._isCollecting):
                self.addNewEntry()
                time.sleep(1)
                print 'tick..'
            print 'stopped thread.'

        self._isCollecting = not self._isCollecting

        if (self._isCollecting):
            self.builder.get_object('btnAdd').set_label('Stop')
            ## Start data collection
            self._threadCollect = threading.Thread(target=runThread)
            self._threadCollect.start()
        else:
            self.builder.get_object('btnAdd').set_label('Start')
            ## Stop data collection
            self._threadCollect.join()


    def addNewEntry(self):
        # bFieldX = float(self.builder.get_object('bField_x').get_text())
        # bFieldY = float(self.builder.get_object('bField_y').get_text())
        # bFieldZ = float(self.builder.get_object('bField_z').get_text())
        # bFieldMagnitude = float(self.builder.get_object('bField_norm').get_text())
        ## Use the B field var instead of text boxes to reduce lag
        bFieldX = self.bField['x']
        bFieldY = self.bField['y']
        bFieldZ = self.bField['z']
        bFieldMagnitude = self.bField['intensity']
        
        locId = int(self.builder.get_object('locId').get_text())


        ## Get B Field Data
        bFieldData = {
            'bField': bFieldMagnitude
        }

        ## Get network data
        ## Get data from atomic self.networks
        self.networksLock.acquire()
        networkData = self.networks
        self.networksLock.release()

        ## Get combined data 
        combinedData = dict(bFieldData.items() + networkData.items())


        item = {
            'target': locId,
            'data': combinedData
        }

        itemDict = self.snapper.append(item)
        self.builder.get_object('statusbar1').push(0, 'Added [%s]@%s: B Field=%s' % 
                                                        (len(self.snapper.data), 
                                                        locId,
                                                        bFieldMagnitude))
        # show in table
        idx = len(self.snapper.data) - 1
        self.store.append([item['target'], str(item['data']), str(itemDict['uuid'])])



    def on_btnTrain_clicked(self, args):
        """ Train button 
        """
        neighbors = int(self.builder.get_object('entryNeighbors').get_text())

        # Train using KNN -----
        self.snapper.train(neighbors)
        # Train using SVM -----

        C=int(self.builder.get_object('svmC').get_text())
        cache_size=int(self.builder.get_object('svmCache').get_text())
        class_weight=None
        coef0=0.0
        degree=int(self.builder.get_object('svmDegree').get_text())
        gamma=float(self.builder.get_object('svmGamma').get_text())
        kernel=str(self.builder.get_object('svmKernel').get_text())
        max_iter=-1
        probability=False
        random_state=None
        shrinking=True
        tol=float(self.builder.get_object('svmTol').get_text())
        verbose=False

        # self.snapper.trainSVM(
        #     C=C,
        #     cache_size=cache_size, 
        #     class_weight=class_weight,
        #     coef0=coef0, 
        #     degree=degree, 
        #     gamma=gamma, 
        #     kernel=kernel, 
        #     max_iter=max_iter,
        #     probability=probability, 
        #     random_state=random_state, 
        #     shrinking=shrinking, 
        #     tol=tol, 
        #     verbose=verbose)

        # self.builder.get_object('statusbar1').push(
        #     0, 'Trained model with C=%s cache=%s gamma=%s ker=%s tol=%s' % 
        #     (C, cache_size, gamma, kernel, tol ))


    def on_btnPredict_clicked(self, args):
        """ Predict button 
        """

        ## Populate test item vector with zeroes first
        item = {}
        keys = self.snapper.getKeys()
        for k in keys:
            item[k] = 0

        ## Get B Field Data
        # bFieldMagnitude = float(self.builder.get_object('bField_norm').get_text())
        bFieldMagnitude = self.bField['intensity']
        bFieldData = {
            'bField': bFieldMagnitude
        }

        ## Get network data
        ## Get data from atomic self.networks
        self.networksLock.acquire()
        networkData = self.networks
        self.networksLock.release()
        # print networkData

        ## Get combined data 
        combinedData = dict(bFieldData.items() + networkData.items())

        ## Merge combined data
        for k in keys:
            if k in combinedData:
                item[k] = combinedData[k]

        prediction = self.snapper.predict(item)

        logging.info('Predicted: %s' % item)

        self.builder.get_object('statusbar1').push(0, 'The prediction is: %s' % prediction)


def runMain():
    def configLogging():
        logging.getLogger('').handlers = []
        logging.basicConfig(
            # filename = "a.log",
            # filemode="w",
            level = logging.DEBUG)

    configLogging()
    app = SnapperWidget()
    Gtk.main()


if __name__ == "__main__":
    runMain()
