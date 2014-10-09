#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of easyNav-snapper-ui.
# https://github.com/easyNav/easyNav-snapper-ui

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2014 Joel Tong me@joeltong.org


from gi.repository import Gtk, GObject
import logging
import smokesignal

from easyNav_snapper import Snapper
from SerialDaemon import SerialDaemon


GObject.threads_init()


class SnapperWidget(Gtk.Window):
    def __init__(self):

        filename = "snapTemplate.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(filename)
        self.builder.connect_signals(self)
        self.builder.get_object('window1').show_all() 

        ## For Snapper stuff 
        self.snapper = Snapper()
        self.saveFilepath = None

        ## For SerialDaemon stuff
        sd = self.sd = SerialDaemon()
        self._attachHandlers()
        sd.start()



    def _attachHandlers(self):
        """Event listeners 
        """
        ## TODO: Does not trigger when GTK starts.  Maybe try fork?
        @smokesignal.on('onData')
        def onDataHandler(x,y,z,intensity):
            """ Event callback for serial data 
            """
            logging.info('Serial Daemon: New Data!')
            self.builder.get_object('bField_x').set_text(str(x))
            self.builder.get_object('bField_y').set_text(str(y))
            self.builder.get_object('bField_z').set_text(str(z))
            self.builder.get_object('bField_norm').set_text(str(intensity))

            print (x,y,z,intensity)



    def buttonWriteNameToFile_clicked(self, widget):
        print("File write code...")


    def on_window1_destroy(self, *args):
        """ Closes the main program
        """
        self.sd.stop()
        Gtk.main_quit()


    def on_imagemenuitem2_activate(self, args):
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

            self.builder.get_object('statusbar1').push(0, 'File %s loaded.' % filename)
            print chooser_dialog.get_filename(), 'selected'
        elif response == Gtk.ResponseType.CANCEL:
            print 'Closed, no files selected'
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
            print chooser_dialog.get_filename(), 'selected'

        elif response == Gtk.ResponseType.CANCEL:
            print 'Closed, no files selected'
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

            self.builder.get_object('statusbar1').push(0, 'File %s loaded.' % filename)
            print chooser_dialog.get_filename(), 'selected'

        elif response == Gtk.ResponseType.CANCEL:
            print 'Closed, no files selected'
        chooser_dialog.destroy()




    def on_btnAdd_clicked(self, args):
        """ Add a new Entry
        """
        bFieldX = float(self.builder.get_object('bField_x').get_text())
        bFieldY = float(self.builder.get_object('bField_y').get_text())
        bFieldZ = float(self.builder.get_object('bField_z').get_text())
        bFieldMagnitude = float(self.builder.get_object('bField_norm').get_text())
        locId = int(self.builder.get_object('locId').get_text())

        print bFieldMagnitude, locId


        self.snapper.append({
            'target': locId,
            'data': {
                'bField': bFieldMagnitude
            }
        })

        self.builder.get_object('statusbar1').push(0, 'Added [%s]@%s: B Field=%s' % 
                                                        (len(self.snapper.data), 
                                                        locId,
                                                        bFieldMagnitude))



    def on_btnTrain_clicked(self, args):
        """ Train button 
        """
        neighbors = int(self.builder.get_object('entryNeighbors').get_text())
        self.snapper.train(neighbors)
        self.builder.get_object('statusbar1').push(0, 'Trained model.')


    def on_btnPredict_clicked(self, args):
        """ Predict button 
        """
        bFieldMagnitude = float(self.builder.get_object('bField_norm').get_text())
        prediction = self.snapper.predict({
            'bField': bFieldMagnitude
        })
        self.builder.get_object('statusbar1').push(0, 'The prediction is: %s' % prediction)




if __name__ == "__main__":
    def configLogging():
        logging.getLogger('').handlers = []

        logging.basicConfig(
            # filename = "a.log",
            # filemode="w",
            level = logging.DEBUG)

    configLogging()
    app = SnapperWidget()
    Gtk.main()
