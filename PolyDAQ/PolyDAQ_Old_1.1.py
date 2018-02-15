
#======================================================================================
# PolyDAQ_1.1.py 
# by Glen Thorncroft as taught to him by John Ridgely
#
# 
#======================================================================================

import os                       # For checking whether data filename exists 
import sys                      # Mainly for function to exit GUIs
import time                     # For getting the current time 
import glob                     # Find files matching a name pattern
import functools                # For functions to be passed as arguments

import PyQt4.QtCore             # The Qt4 library, used to make the GUI
import PyQt4.QtGui              # Same reason!
import PyQt4.Qwt5               # Qwt graphing library

import platform                 # For identifying Linux, Mac, or Windows
import serial                   # For scanning for serial ports

# Custom Modules:
import new_config as config     # The GUI configuration file; customizable for
                                # Different experiments, different hardware configurations 
                                            
import PolyDAQ_A2D_thread       # Module for getting data from the board


import PolyDAQ_PlotManager \
               as plotManager   # Module that sets up the plots/data outputs to the GUI
                                # and manages each and every one.  
                                # talks to PolyDAQ_Plotter.py, which has plot drawing class


#--------------------------------------------------------------------------------------
# This function scans for serial ports and returns a list of the ports found.  On a
# Linux system, it looks for USB serial ports named /dev/ttyUSB* and Bluetooth serial  
# ports named /dev/rfcomm*. 

def scan_system_and_serial_ports ():

    system_name = platform.system ()

    if system_name == "Windows":
        # Scan for available ports.
        available = []
        for i in range (256):
            try:
                s = serial.Serial (i)
                available.append (s.name)
                s.close ()
            except serial.SerialException:
                pass
        return ['Choose Port'] + available

    elif system_name == "Darwin":
        # Mac
        return ['Choose Port'] + glob.glob ('/dev/tty*') + glob.glob ('/dev/cu*')

    else:
        # Assume Linux or something else
        return ['Choose Port'] + glob.glob ('/dev/ttyUSB*') #+ glob.glob ('/dev/ttyS?') 


#--------------------------------------------------------------------------------------

class Window (PyQt4.QtGui.QMainWindow): 
    def __init__ (self, parent = None):

        super (Window, self).__init__ (parent)
        

        self.main_widget = PyQt4.QtGui.QWidget (self)

        # -----------------------------------------------------------------------------
        # Configure Hardware/Software/Some Initial Settings
        # This calls the first function, which imports settings from new_config.py
        # and sets other initial values and constants
        #self.Configure ()

        self.file_path = config.data_file_path
        self.file_name = config.data_file_name + '.' + config.data_file_extension

        # -----------------------------------------------------------------------------
        # Construct Menu Bar
        # This is the menu bar at the top of the window.

        # add a menu called 'File' with submenus 'Change Date Filename' and 'Exit'
        menu = self.menuBar ()

        fileMenu = menu.addMenu ('&File')

        exitAction = PyQt4.QtGui.QAction (PyQt4.QtGui.QIcon ('exit.png'), 
                                          '&Exit', self)        
        exitAction.setShortcut ('Ctrl+Q')
        exitAction.setStatusTip ('Exit application')
        exitAction.triggered.connect (self.closeEvent)
        
        fileMenu_changeDataFile = fileMenu.addAction ('Change Data Filename')
        fileMenu_changeDataFile.triggered.connect (self.change_file_name)
        fileMenu.addAction (exitAction)

        # add a menu named 'Tools' with submenus 'Auto-Balance Strain Bridge', 'Flag data...' and 
        # 'Calibrate A/D Board' (NOT IMPLEMENTED YET).
        toolsMenu = menu.addMenu ('Tools') 

        balanceBridge = toolsMenu.addAction ('Auto-Balance Strain Bridge')
        balanceBridge.triggered.connect (self.balance_bridges)
#        calibrate = hardwareMenu.addAction ('Calibrate A/D Board')
#        calibrate.triggered.connect (self.calibrateBoard)

        self.addNote = toolsMenu.addAction ('Earmark data...')
        self.addNote.triggered.connect (self.earmark_data)
    
        # add menu called 'Help' with submenus 'Plot Navigation Guide' and 'About'
        helpMenu = menu.addMenu ('Help')        

        self.nav = helpMenu.addAction ('Plot Navigation Guide')
        self.nav.triggered.connect (self.plotNavigation)

        about = helpMenu.addAction ('About')
        about.triggered.connect (self.aboutScreen)

        # Set up Splitter Frames--------------------------------------------------------

        mainBox = PyQt4.QtGui.QVBoxLayout ()
        
        # LEFT COLUMN of Groups (Left side of splitter)
        left_supergroup = PyQt4.QtGui.QFrame ()  
        left_vbox = PyQt4.QtGui.QVBoxLayout ()       

        # add plots and other widgets to left column
        left_vbox.addWidget (self.createInitialSettingsGroup ()) 
        left_vbox.addWidget (self.createChooseSignalsGroup ())
        left_vbox.addWidget (self.createChooseTimeGroup ())
        left_vbox.addWidget (self.createStartStopGroup ())

        # Set up the statusBox status box... that we created earlier
        self.statusBox = PyQt4.QtGui.QTextEdit ()
        self.statusBox.append (config.init_text ())
        self.statusBox.append ('STATUS: Not connected.\nClick CHOOSE PORT to begin.\n')
        self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)
        self.statusBox.setReadOnly (True)
        self.statusBox.setLineWrapMode (1)        # wrap to widget width
        left_vbox.addWidget (self.statusBox)

        left_supergroup.setLayout (left_vbox)

        splitter_horiz = PyQt4.QtGui.QSplitter (PyQt4.QtCore.Qt.Horizontal)
        splitter_horiz.addWidget (left_supergroup)

        # Go to plot manager and set up plot panes

        self.myManager = plotManager.PlotManager (config, self)
        
        # Create the plot panes for all plots and data readouts
        splitter_vert = self.myManager.allPlotsAndReadouts 

        splitter_horiz.addWidget (splitter_vert)
        splitter_horiz.setStretchFactor (0,0)
        splitter_horiz.setStretchFactor (1,1)

        mainBox.addWidget (splitter_horiz)

        # Complete look of window: title, icon, size, location
        self.setWindowIcon (PyQt4.QtGui.QIcon ('polydaq_icon.png'))
        self.setWindowTitle (config.software_name)
        
        self.main_widget.setLayout (mainBox)
        self.setCentralWidget (self.main_widget)
        PyQt4.QtGui.QApplication.setStyle (PyQt4.QtGui.QStyleFactory.create \
                                                                        ('Plastique'))
        PyQt4.QtGui.QApplication.setFont (PyQt4.QtGui.QFont ('SansSerif', 9.8))
        self.resize (1000, 700)
        self.move (100, 75)

        # Set up timers and threads ----------------------------------------------------

        # There's some kind of timer that's needed...oh, there's one on that shelf
        self.update_timer = PyQt4.QtCore.QTimer ()
        
        # Connect the idle process timer to fire when there's nothing else going on
        self.connect (self.update_timer,
                      PyQt4.QtCore.SIGNAL ("timeout()"),
                      self.idleProcess)

        # The timer has been set up to fire a timeout() whenever there aren't any
        # other events going on. Start it now.
        self.update_timer.start ()

        # Create a thread for data acquisition. The thread is a daemon, meaning that
        # when the GUI thread exits, the daemon thread will not keep Python running
        self.my_acq_thread = PolyDAQ_A2D_thread.data_acq_thread \
                             (0.1)   
#                            (config.rates[self.timebase_box.currentIndex ()])

        self.my_acq_thread.daemon = True
        self.my_acq_thread.start ()

        # Set initial values -----------------------------------------------------------

        # Gray out most of the buttons
#        self.addNote.setEnabled (False)
        self.note = ''
        self.choose_signals_grp.setEnabled (False)            
        self.time_settings_grp.setEnabled (False)
        self.start_stop_grp.setEnabled (False)

        self.serial_port_ready = False      # The serial port isn't yet ready to use
        self.running = False                # Not taking and displaying data now
        self.serial_string = ""             # String holds characters from serial port

        self.tbase_index = self.timebase_box.currentIndex ()

        self.time_per_point = 0.1 #config.rates[self.tbase_index]
        self.timeConversionFactor = 1. # for default units of seconds (for plotting only)    
        self.units_string='s' 
        self.unitsHaveChanged = False


        self.auto_stop = False
        
        for a_plot in config.plots:
            # This inner loop iterates through the channels belonging to a plot
            a_plot['numberOfCurves'] = 0


        if (config.station == -1): # The value -1 will trigger an error dialog to tell the user 
#                         to configure PolyDAQ for that particular station/board.
        
            PyQt4.QtGui.QMessageBox.critical (self, 'Error', \
               'The PolyDAQ software has not yet been configured\n'+\
                'for this board/station.  Each PolyDAQ board is calibrated\n'+\
                'individually, and thus has its own unique set of calibration\n'+\
                'equations. \n\n'+\
                'The cause?  You must have replaced the microSD card recently!\n'+\
                '\nTo fix this problem, you have two options: \n\n'+\
                '1.  Have your instructor log in as Thermoadmin.  \n\n   Have them:\n\n'+\
                '    a. Open Spyder from the quick launch panel.\n'+\
                '    b. Edit line 68 of new_config.py, to change the station\n'+\
                '       number from "-1" to your station number.\n'+\
                '    c. Save the file, close spyder, and logout.\n'+\
                '    d. Log back in as "student" and start PolyDAQ again.\n'+\
                '\nor\n\n'+\
                '2.  Call Thorncroft immediately and have him do it, because\n'+\
                '    he ROCKS.\n'+\
                '\nNow, memorize these steps and click OK. \n\n'+\
                'The program will now self-destruct...Live long and prosper. ',
                PyQt4.QtGui.QMessageBox.Ok)
 
            sys.exit (0)




        
    #----------------------------------------------------------------------------------

    def set_serial_port (self, port_text):
        ''' This method is used to set the serial port to which we're connecting.  It 
        opens (or attempts to open) the port; if successful, the port's ready; if not, 
        an error indication is given.  If the port is successfully opened, the other 
        buttons will be activated.
        '''

        # If the index is 0 or less, no valid port was chosen
        if self.serial_port_box.currentIndex () <= 0:
            return

        # Get the port name from the button and update the status message
        port_name = self.ser_port_list[self.serial_port_box.currentIndex ()]

        # Ask the data acquisition thread to attempt to open the serial port. The
        # thread will return a text string indicating if things went well
        [result_string, self.serial_port_ready] = \
                            self.my_acq_thread.set_serial_port (port_name, config.baud_rate)

        self.statusBox.append (result_string)
        self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)
        self.statusBox.append ('')
        self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)

#        self.status_label.update ()

        # Activate buttons which can be used with an open port
        if (self.serial_port_ready == True):

            self.choose_signals_grp.setEnabled (True)
            self.time_settings_grp.setEnabled (True)
            self.start_stop_grp.setEnabled (True)
#            self.histogram_btn.setEnabled (True)

        # Make sure the port list is updated in case somebody plugged in a USB port
        # or turned on a Bluetooth device or something like that
        self.serial_port_list = scan_system_and_serial_ports ()


    #----------------------------------------------------------------------------------

    def change_file_name (self):

        self.old_name = self.file_name
        old_path = self.file_path
        new_path_plus_name = PyQt4.QtGui.QFileDialog.getSaveFileName \
                                            (self, "Change Data Filename",
                                             old_path + '/', "Data files (*.txt *.csv)")

        # separate filename into path and name: +old_name
        for i in range (len (new_path_plus_name) - 1, 0, -1):
            if new_path_plus_name[i] == '/':
                self.file_name =  new_path_plus_name [i + 1:]
                self.file_path =  new_path_plus_name [:i]
                break

		# does filename have .csv extension?  if not, add it!
        if self.file_name[-4:] != '.csv':
            self.file_name += '.csv'

        self.FileName_txt.setText (self.file_name)
        self.statusBox.append ('Data Filename changed to ' + self.file_name)

        # check if you already saved to this file!  If so, go to self.file_exists...
        if os.path.isfile (self.file_path + '/' + self.file_name) \
                and os.path.getsize (self.file_path + '/' + self.file_name) > 0:

            reply = PyQt4.QtGui.QMessageBox.question (self, 'File Exists',
                        "File Exists! Overwrite?", PyQt4.QtGui.QMessageBox.Yes |
                        PyQt4.QtGui.QMessageBox.No | PyQt4.QtGui.QMessageBox.Cancel)

            if reply == PyQt4.QtGui.QMessageBox.No:
                self.change_file_name ()

            if reply == PyQt4.QtGui.QMessageBox.Cancel:
                self.cancelClicked = True


    #----------------------------------------------------------------------------------

    def file_exists (self):

        reply = PyQt4.QtGui.QMessageBox.question (self, 'File Exists',
                            "File Exists! Overwrite?", PyQt4.QtGui.QMessageBox.Yes |
                            PyQt4.QtGui.QMessageBox.No | PyQt4.QtGui.QMessageBox.Cancel)

        if reply == PyQt4.QtGui.QMessageBox.No:
                self.change_file_name ()
                
        if reply == PyQt4.QtGui.QMessageBox.Cancel:
            self.cancelClicked = True
            
        return

    #----------------------------------------------------------------------------------

    def createInitialSettingsGroup (self):
        ''' Create Initial Settings group (set up DAQ Port, FileName)
        '''

        self.init_settings_grp = PyQt4.QtGui.QGroupBox ("Initial Settings")

        # This combo box chooses a serial port with which to connect
        DAQPortLabel = PyQt4.QtGui.QLabel ("DAQ Port:")
        self.serial_port_box = PyQt4.QtGui.QComboBox ()
        self.connect (self.serial_port_box,
                      PyQt4.QtCore.SIGNAL ("currentIndexChanged(QString)"),
                      self.set_serial_port)
        self.ser_port_list = scan_system_and_serial_ports ()
        self.serial_port_box.setInsertPolicy (PyQt4.QtGui.QComboBox.InsertAtTop)
        for index in range (0, len (self.ser_port_list)):   
            self.serial_port_box.addItem (self.ser_port_list[index])

        # Show Data Filename (and path, though commented out now)
        self.FileName_lbl = PyQt4.QtGui.QLabel ("Data File:")  
        self.FileName_txt = PyQt4.QtGui.QLineEdit (self.file_name)
        self.FileName_txt.setFixedWidth (190)
        self.FileName_txt.setEnabled (False)
        self.changeFile_btn = PyQt4.QtGui.QPushButton ('...')
        PyQt4.QtGui.QToolTip.setFont (PyQt4.QtGui.QFont ('SansSerif', 9.8))
        self.changeFile_btn.setToolTip ("Change Data File")
        self.changeFile_btn.setFixedWidth (20)
        self.changeFile_btn.setFixedHeight (18)

        self.connect (self.changeFile_btn,
                      PyQt4.QtCore.SIGNAL ("clicked()"),
                      self.change_file_name)

        layout = PyQt4.QtGui.QGridLayout ()
        layout.addWidget (DAQPortLabel,         0, 0)
        layout.addWidget (self.serial_port_box, 0, 1, 1, 3)
        layout.addWidget (self.FileName_lbl,    2, 0) 
        layout.addWidget (self.FileName_txt,    2, 1, 1, 2)
        layout.addWidget (self.changeFile_btn,  2, 3)

        self.init_settings_grp.setLayout (layout)

        return self.init_settings_grp


    #----------------------------------------------------------------------------------

    def createChooseSignalsGroup (self):
        ''' This is where the user selects the channels to be measured/observed.
        '''

        self.choose_signals_grp = PyQt4.QtGui.QGroupBox ("Choose Channels to Record")
        boxWidth = 210
        boxHeight = 20
        indentSpace = PyQt4.QtGui.QLabel ("")
        signal_grp_layout = PyQt4.QtGui.QVBoxLayout ()

        # We'll need a list of all the channel name inputs to enable and disable them

        # This outer loop iterates through the plots (sets of measurements)
        for a_plot in config.plots:

            a_label = PyQt4.QtGui.QLabel (a_plot['name'])
            signal_grp_layout.addWidget (a_label)
            channel_chkbox_layout = PyQt4.QtGui.QGridLayout ()
            ch_num = 0

            # This inner loop iterates through the channels belonging to a plot
            for a_channel in a_plot['channels']:

                a_checkbox = PyQt4.QtGui.QCheckBox (a_channel['abbrev'])
                a_channel['cbox'] = a_checkbox # just added a new parameter to channel!!!!!!!
                a_channel['cbox'].clicked.connect (functools.partial (self.on_clicky, a_channel))
                #self.connect (a_checkbox, PyQt4.QtCore.SIGNAL ("clicked()"),
                              #self.set_measurands)
                a_input = PyQt4.QtGui.QLineEdit (a_channel['name'])
                a_channel['edit'] = a_input # just added another parameter!!!!
                a_channel['edit'].editingFinished.connect (functools.partial \
                                                 (self.ch_name_edit_finished, a_channel))
                #a_input.editingFinished.connect (self.ch_name_edit_finished)

                a_input.setFixedWidth (boxWidth)
                a_input.setFixedHeight (boxHeight)
                a_input.setEnabled (False)

                channel_chkbox_layout.addWidget (indentSpace, ch_num, 0, 1, 1)
                channel_chkbox_layout.addWidget (a_checkbox,  ch_num, 1, 1, 1)        
                channel_chkbox_layout.addWidget (a_input,     ch_num, 2, 1, 2)

                ch_num +=1

            # Add this plot's tools layout to the main application layout
            signal_grp_layout.addLayout (channel_chkbox_layout)

        self.choose_signals_grp.setLayout (signal_grp_layout)

        return self.choose_signals_grp


    #----------------------------------------------------------------------------------

    def on_clicky (self, a_channel):
            
        if a_channel['cbox'].isChecked ():
            a_channel['edit'].setEnabled (True)
        else:
            a_channel['edit'].setEnabled (False)

        self.set_measurands ()
            

    def ch_name_edit_finished (self, a_channel):
        ''' Method which changes a channel's name when editing the channel is done.
        '''

        if a_channel['edit'].text () == '':
            self.statusBox.append ('WARNING! Blank names not allowed.')
            self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)
            a_channel['edit'].setText (a_channel['name'])
        else:
            self.statusBox.append (a_channel['name']+' renamed to ' \
                                   + a_channel['edit'].text ())
            a_channel['name'] = a_channel['edit'].text ()
            self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)


    #----------------------------------------------------------------------------------

    def set_measurands (self):
        ''' This method sets the channel lists -- both in real-world definitions 
        (like T1) and teh equivalent DAQ code (hexadecimal, like A) 
        '''

        measurands = []       # measurand list to be sent to board, PolyDAQ_A2D_thread
#        slopes = []           # calibration slopes
#        offsets = []          # calibration offsets (y-intercepts)

        #  This method sets organizes the list of DAQ channels read by the DAQ,
        #  called measurands.  The first 'ON' channel will be first on the 
        #  list.  The list will therefore look like ['8', 'A', 'C', etc.], in order.

        # Iterate through each plot and list of channels to check all the channels
        for a_plot in config.plots:
            # This inner loop iterates through the channels belonging to a plot
            a_plot['numberOfCurves'] =0
            for a_channel in a_plot['channels']:
                # If this channel's checkbox is checked, add the channel to the list
                if (a_channel['cbox'].isChecked ()):
                    measurands.append (a_channel['command'])
#                    slopes.append (a_channel['slope'])
#                    offsets.append (a_channel['offset'])
                    a_channel['edit'].setEnabled (True)
                    a_plot['numberOfCurves'] +=1
                else:
                    a_channel['edit'].setEnabled (False)

        #self.statusBox.append ('Channels ' + str (self.measurandsByAbbrev)+ ' ON')
        self.statusBox.append ('(DAQ Channels ' + str (measurands) + ')')
        self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)

        # Tell the data taking thread what the measurands are
        self.my_acq_thread.set_measurands (measurands) #, slopes, offsets)


    #----------------------------------------------------------------------------------

    def createChooseTimeGroup (self):
        ''' This is where users can select the scan rate, auto or manual stop, and the
        time units (default: seconds)
        '''

        self.time_settings_grp = PyQt4.QtGui.QGroupBox ('Set Time Parameters')

        # A combo box which is used to select a time base
        self.scan_rate_lbl = PyQt4.QtGui.QLabel ('Sample every')
        self.timebase_box = PyQt4.QtGui.QComboBox ()
        self.timebase_box.setInsertPolicy (PyQt4.QtGui.QComboBox.NoInsert)
        self.scan_rate_unit_lbl = PyQt4.QtGui.QLabel ('s')
        self.scan_rate_info_btn = PyQt4.QtGui.QPushButton ('?')
#        self.scan_rate_info_btn.icon()
#        self.scan_rate_info_btn.setIcon(PyQt4.QtGui.QIcon('warning.png'))
        self.scan_rate_info_btn.setFixedWidth(18)
        self.scan_rate_info_btn.setFixedHeight(18)
#        self.scan_rate_info_btn.setStyleSheet("background-color: #eedd82") #yellowish
        self.scan_rate_info_btn.setStyleSheet("background-color: #007cc3; color: white;") #blue
        self.scan_rate_info_btn.setFont(PyQt4.QtGui.QFont ('Courier', 12 , 
#                                                           PyQt4.QtGui.QFont.Cursive, 
                                                            PyQt4.QtGui.QFont.Bold 
                                                            ))
        self.scan_rate_info_btn.setToolTip('How fast can I sample?')

        self.connect (self.scan_rate_info_btn,
                      PyQt4.QtCore.SIGNAL ('clicked()'),
                      self.scan_rate_info)
        
        for index, a_time in enumerate (config.rates):
            self.timebase_box.insertItem (index, str (config.rates[index]))

        # This sets the initial timebase to BLANK
        self.timebase_box.setCurrentIndex (-1)
        
        self.connect (self.timebase_box,
                      PyQt4.QtCore.SIGNAL ('currentIndexChanged(QString)'),
                      self.set_timebase)

        # DAQ is stopped manually by the user by default.
        # These buttons allow for manual or auto stop.
#        self.manual_stop_btn = PyQt4.QtGui.QRadioButton ('Manual stop')
#        self.manual_stop_btn.setChecked (True)
        self.auto_stop_cbox = PyQt4.QtGui.QCheckBox ('Auto-stop/save at')

        self.stop_time_box = PyQt4.QtGui.QSpinBox ()
        self.stop_time_box.setRange (0, 360000)
        self.units_lbl = PyQt4.QtGui.QLabel ('s')

        # Initially, auto stop is disabled
        self.stop_time_box.setEnabled (False)
        self.units_lbl.setEnabled (False)

#        self.connect (self.manual_stop_btn,
#                      PyQt4.QtCore.SIGNAL ('clicked()'),
#                      self.auto_or_manual_stop)

        self.connect (self.auto_stop_cbox,
                      PyQt4.QtCore.SIGNAL ('clicked()'),
                      self.auto_or_manual_stop)
        
        self.connect (self.stop_time_box,
                      PyQt4.QtCore.SIGNAL ('valueChanged(int)'),
                      self.auto_or_manual_stop)


        layout = PyQt4.QtGui.QGridLayout ()

        layout.addWidget (self.scan_rate_lbl,   0, 0)
        layout.addWidget (self.timebase_box,    0, 1)
        
        layout.addWidget (self.scan_rate_unit_lbl, 0, 2)
        layout.addWidget (self.scan_rate_info_btn, 0, 3, 1, 5)
        
        layout.addWidget (self.auto_stop_cbox,   3, 0) 
        layout.addWidget (self.stop_time_box,   3, 1)  
        layout.addWidget (self.units_lbl,     3, 2)    

        self.time_settings_grp.setLayout (layout)

        return self.time_settings_grp


    #----------------------------------------------------------------------------------

    def set_timebase (self):
        ''' This method chooses a timebase -- how quickly data will be recorded.
        '''

        self.tbase_index = self.timebase_box.currentIndex ()

        self.my_acq_thread.set_interval (config.rates[self.tbase_index])
        self.statusBox.append ('New time base: ' 
                                    + str (config.rates[self.tbase_index])+ ' s')
        self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)

        self.time_per_point = config.rates[self.tbase_index]  #### THIS IS FOR DAQ THREAD



    #----------------------------------------------------------------------------------

    def auto_or_manual_stop (self):

        # If auto stop has been de-checked, turn auto off.
        if not self.auto_stop_cbox.isChecked ():  
            self.auto_stop_cbox.setChecked (False)
            self.stop_time_box.setEnabled (False)
            self.units_lbl.setEnabled (False)
            self.statusBox.append ('Auto-stop turned off.')
            self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)
            self.auto_stop = False

        # If auto-stop has veen checked, turn autostop on.
        else:                               
            self.stop_time_box.setEnabled (True)
            self.auto_stop = True
            self.units_lbl.setEnabled (True)
            self.stop_time = self.stop_time_box.value ()     
            self.statusBox.append ('Auto-stop time: '+ str (self.stop_time) + ' s')
            self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)


    #----------------------------------------------------------------------------------

    def createStartStopGroup (self):
        self.start_stop_grp = PyQt4.QtGui.QGroupBox ('Start/Stop (Data saves automatically to file)')

        self.start_btn = PyQt4.QtGui.QPushButton ('START')
        self.start_btn.setFixedWidth (70)
        self.start_btn.setFixedHeight (40)
        self.start_btn.setFont (PyQt4.QtGui.QFont ('SansSerif', 14))
        self.start_btn.setToolTip('Start recording & saving data')

        self.stop_btn = PyQt4.QtGui.QPushButton ('STOP')
        self.stop_btn.setFont (PyQt4.QtGui.QFont ('SansSerif', 14))
        self.stop_btn.setToolTip('Stop & close data file')
        self.stop_btn.setEnabled (False)
        
        self.stop_btn.setFixedWidth (70)
        self.stop_btn.setFixedHeight (40)

        self.connect (self.start_btn,
                      PyQt4.QtCore.SIGNAL ('clicked()'),
                      self.start_or_stop)

        self.connect (self.stop_btn,
                      PyQt4.QtCore.SIGNAL ('clicked()'),
                      self.start_or_stop)

        layout = PyQt4.QtGui.QGridLayout ()
        layout.addWidget (self.start_btn, 1, 0)
        layout.addWidget (self.stop_btn,  1, 1)
        self.start_stop_grp.setLayout (layout)

        return self.start_stop_grp


    #----------------------------------------------------------------------------------

    def start_or_stop (self):
        ''' This method responds to a press of the run/stop button, which does 
        different things depending on whether it says 'Run' or 'Stop' at the time it 
        is pressed.
        '''

        # Make sure there is at least one channel selected
        num_channels_on = 0
        for a_plot in config.plots:
            for a_channel in a_plot['channels']:
                if (a_channel['cbox'].isChecked ()):
                    num_channels_on += 1

        if num_channels_on == 0:
            PyQt4.QtGui.QMessageBox.critical (self, 'Error',
                                              'No channels selected!', 
                                              PyQt4.QtGui.QMessageBox.Ok)
            return
            
        if self.timebase_box.currentIndex () == -1:
            PyQt4.QtGui.QMessageBox.critical (self, 'Error',
                                              'No sample rate selected!', 
                                              PyQt4.QtGui.QMessageBox.Ok)
            return

        if self.auto_stop and (self.stop_time < 0.001):
            PyQt4.QtGui.QMessageBox.critical (self, 'Error',
                                              'Auto Stop time cannot be zero!', 
                                              PyQt4.QtGui.QMessageBox.Ok)
            return

        # If not running, get running right away
        if (self.running == False):

            # If port is ready, tell the data acquisition thread to get to work
            if (self.serial_port_ready):

                # open file and initial text
                # Check if you already saved to this file!
                if os.path.isfile (self.file_path + '/' + self.file_name) and \
                        os.path.getsize (self.file_path + '/' + self.file_name) > 0:
                    self.cancelClicked = False
                    self.file_exists ()
                    if self.cancelClicked:
                        return

                self.running = True

                # Tells 'idle' method that initial data array is empty; variable used
                # as a way to see if array has been added to
                self.previous_length = 0

                self.data_file = open (self.file_path + '/' + self.file_name, 'w', 1024)

                self.data_file.write ('PolyDAQ data collection began:' + ',' 
                                      + time.strftime ("%m/%d/%y at %I:%M%p") + '\n')

                self.data_file.write ('Data Acquired at Station ' + str(config.station) + '.\n')

#                self.data_file.write ('Calibration Constants...')
#                for a_plot in config.plots:
#                    for a_channel in a_plot['channels']:
#                        if a_channel['cbox'].isChecked (): self.data_file.write \
#                                                              (',' + a_channel['name'])
#                self.data_file.write ('\nSlopes:')
#                for a_plot in config.plots:
#                    for a_channel in a_plot['channels']:
#                        if a_channel['cbox'].isChecked (): self.data_file.write \
#                                                       (',' + str (a_channel['slope']))
#                self.data_file.write ('\nOffsets:')
#                for a_plot in config.plots:
#                    for a_channel in a_plot['channels']:
#                        if a_channel['cbox'].isChecked (): self.data_file.write \
#                                                      (',' + str (a_channel['offset']))
                self.data_file.write ('\nData...\n')
                self.data_file.write ('Time ('+ self.units_lbl.text () + ')')
                for a_plot in config.plots:
                    for a_channel in a_plot['channels']:
                        if a_channel['cbox'].isChecked (): self.data_file.write \
                                                              (',' + a_channel['name'])
                self.data_file.write (',Notes\n')  


#New from Plot Manager:

                self.myManager.resetDisplays ()

                self.my_acq_thread.start_taking_data ()

                self.start_time = time.time ()
                self.start_btn.setEnabled (False)
                self.addNote.setEnabled (True)
                self.start_btn.update ()
                self.stop_btn.setEnabled (True)
                self.statusBox.append ('\nAcquiring data.')
                self.statusBox.append ('Recording started ' + time.strftime \
                                                ('%a, %m/%d/%y at %I:%M%p') + '.\n')
                self.statusBox.append ('\n')
                self.eraseThisManyCharacters = 0
                self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)

                self.init_settings_grp.setEnabled (False)
                self.choose_signals_grp.setEnabled (False)
                self.time_settings_grp.setEnabled (False)

        # If we were running, stop running
        else:
                        
            self.my_acq_thread.stop_taking_data ()


            # close the data file
            self.data_file.close ()

            # Reset the Start button 
            self.start_btn.setStyleSheet ("background-color: lightgray")
            self.start_btn.setEnabled (True)
            self.start_btn.update ()
            self.stop_btn.setEnabled (False)
            self.stop_btn.update ()
            self.statusBox.append ('\nRecording stopped ' 
                                    + time.strftime ("%a, %m/%d/%y at %I:%M%p")+'.')
	    self.statusBox.append ('\nData saved to file ' + '"'+self.file_name+'"' )
                                    	
            self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)

            self.init_settings_grp.setEnabled (True)
            self.choose_signals_grp.setEnabled (True)
            self.time_settings_grp.setEnabled (True)

            


#New from Plot Manager
            self.myManager.reattachAllDataToAllPlots (self.my_acq_thread.time_array, \
                                           self.my_acq_thread.data_array, self.running)
            self.running = False
                 


    #----------------------------------------------------------------------------------
    # This function can only exist for a PolyDAQ 2 with its D/A converter based strain
    # gauge bridge balancers. It asks the PolyDAQ 2 to run an auto-balance on each 
    # bridge.

    def balance_bridges (self):
        
            messagebox = PyQt4.QtGui.QMessageBox

            reply = messagebox.warning (self, 'Caution!',
                "You are about to balance the strain bridges! \n\nThis action will change the zero-voltage reading \nfor both channels M1 and M2.\n\nAre you sure you want to do this? \n",
                PyQt4.QtGui.QMessageBox.Ok 
                | PyQt4.QtGui.QMessageBox.Cancel, PyQt4.QtGui.QMessageBox.Cancel)

            if reply == PyQt4.QtGui.QMessageBox.Ok:

                # balance the bridges
                


                response_string = self.my_acq_thread.balance_bridge ('L');
                self.statusBox.append (response_string)
                self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)

                time.sleep (1)

                response_string = self.my_acq_thread.balance_bridge ('M');
                self.statusBox.append (response_string)
                self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)                
                


#                return
#                sys.exit (0)     # this command works, whether it is an event or not
            else:
                return
#                sys.exit (0)
#                # if exit is called from the menu, it didn't come from an EVENT!
#                if event == False: 
#                    return  
#                else:
#                    event.ignore ()

        


    #----------------------------------------------------------------------------------
    # This function opens a dialog that allows users to add a memo to the data file at any time.  The note 
    # will appear to the right of the last column, at the moment in time the user clicks "add note."

    def earmark_data (self, event):
        

        self.addNote.setEnabled(False)   # disable the menu item, or else the Qdialog can be opened again!
        self.earmarkScreen = PyQt4.QtGui.QDialog (self)
        earmarkScreenLayout = PyQt4.QtGui.QVBoxLayout ()
        earmarkScreenText = PyQt4.QtGui.QLabel ('Earmarking Data:\n\n\
        This feature allows you to add notes (earmarks) \n\
        to the file as data are being collected.  Simply \n\
        type a note below and click ADD.  The note will \n\
        appear in the right-most column of the data file.\n\n')

        self.earmarkLabel = PyQt4.QtGui.QLabel ('Note:')        
        self.earmark =  PyQt4.QtGui.QLineEdit ('')
        
        self.addEarmark_btn = PyQt4.QtGui.QPushButton ("Add")
        
        self.addEarmark_btn.clicked.connect (self.add_earmark)
        
        editLineLayout = PyQt4.QtGui.QHBoxLayout ()
        editLineLayout.addWidget (self.earmarkLabel)        
        editLineLayout.addWidget (self.earmark)
        editLineLayout.addWidget (self.addEarmark_btn)
        
        earmarkScreenLayout.addWidget (earmarkScreenText)        
        earmarkScreenLayout.addLayout (editLineLayout)
        
        blankLine = PyQt4.QtGui.QLabel (' ')
        self.earmarkStatus = PyQt4.QtGui.QLabel (' ')
        okButton = PyQt4.QtGui.QPushButton ("Close")
        earmarkScreenLayout.addWidget (self.earmarkStatus)
        earmarkScreenLayout.addWidget (blankLine)
        earmarkScreenLayout.addWidget (okButton)
        okButton.clicked.connect (self.earmarkScreenClose)
        self.earmarkScreen.setLayout (earmarkScreenLayout)

        self.earmarkScreen.setWindowTitle ('Earmark Data')
        self.earmarkScreen.setWindowIcon (PyQt4.QtGui.QIcon ('polydaq_icon.png'))

        self.earmarkScreen.show ()


    #----------------------------------------------------------------------------------
    
    def add_earmark (self):

        self.note = self.earmark.text ()
        self.earmark.setText ('')
        self.earmarkStatus.setText('')
        
        return
    #----------------------------------------------------------------------------------

    def earmarkScreenClose (self):
        self.earmarkScreen.close ()
        self.addNote.setEnabled(True)   # disable the menu item, or else the Qdialog can be opened again!
        
        return


    #==================================================================================

    def idleProcess (self):
        ''' This method is called by the timer whenever there's no other event that 
        needs to run. It grabs data from the serial port if data is available and saves
        the data in the plot buffer; if it's time to update the plot it does that too.
        '''

        #Ping plot manager to see if time units have changed on the plots...
        self.unitsHaveChanged, self.units_string, self.timeConversionFactor \
                                   = self.myManager.time_units_condition()

        if self.running: 

            # Lock the data acquisition task for a moment and check array sizes
            self.my_acq_thread.data_lock.acquire ()
            self.current_length = len (self.my_acq_thread.time_array)
            self.my_acq_thread.data_lock.release ()

            

            # Check if the data arrays have changed size; if so, update the plots and 
            # file.  In other words, if array has grown...
            
            if (self.current_length > self.previous_length):
                               
                time_copy = []              # Holds a copy of each row's time reading
                data_copy = []              # Holds copies of each row's channel data
                row_index = 0               # Which row is being worked with now

#                # Lock the data acquisition task for a moment and check array sizes
#                self.my_acq_thread.data_lock.acquire ()
#                self.current_length = len (self.my_acq_thread.time_array)

#                self.my_acq_thread.data_lock.release ()

                for num in range (self.previous_length, self.current_length):

                    
                    # channel count in the truncated channel list (only those read)
                    ch_count = 0
                    data_copy.append ([])

                    # Put a lock on the data array so the acquisition task can't write
                    # to the array at the same time as we are trying to read it
                    self.my_acq_thread.data_lock.acquire ()

                    # Get the time for this row
                    time_copy.append (self.my_acq_thread.time_array[num])

                    # For every channel which is active, grab a copy of its data
                    for a_plot in config.plots:
                        for a_channel in a_plot['channels']:
                            if a_channel['cbox'].isChecked ():
                                
                                data_copy[row_index].append \
                                        (self.my_acq_thread.data_array[ch_count][num])
                                ch_count += 1

                    # Release the lock on the data so the acquisition task can work
                    self.my_acq_thread.data_lock.release ()

                    # On to the next row
                    row_index += 1

                # Go through the just-copied data, this time writing the data we have
                # just grabbed to the data file and updating the current data boxes
                row_index = 0
                for num in range (self.previous_length, self.current_length):

                    ch_count = 0
                    # Write the time to the current line in the data file
                    self.data_file.write (str ('{:.3f}'.format (time_copy[row_index])))

                    # For every channel which is active, update readout and write data
                    for a_plot in config.plots:
                        for a_channel in a_plot['channels']:
                            if a_channel['cbox'].isChecked ():
                                data = (data_copy[row_index])[ch_count]
                                a_channel['readout'].setText ('{:.4f}'.format (data))
                                self.data_file.write (',' + str (data))

                                if data < a_plot['ymin']:
                                    a_plot['ymin'] = data     # Also check if we have
                                if data > a_plot['ymax']:        # a new min. or max.
                                    a_plot['ymax'] = data
                                ch_count += 1

                    # Add earmark if there is one!
                    if self.note <> '':
                        self.data_file.write (','+ str (self.note))
                        
                        self.earmarkStatus.setText('          The following note: \n\n              '+ self.note + '\n\n          was added at approx. '+ \
                                                   str ('{:.3f}'.format (time_copy[row_index]*self.timeConversionFactor))+ ' '+self.units_string)
                        self.note = ''                    
                    
                    # Carriage return at the end of the set of data
                    self.data_file.write ('\n')
                    row_index += 1                

                self.previous_length = self.current_length
                


#New from Plot Manager...
                self.myManager.updateDisplays (self.running, self.time_per_point,    \
                        self.my_acq_thread.time_array, self.my_acq_thread.data_array)

# Display elapsed time in status box 
                for indx in range (0, self.eraseThisManyCharacters+1):
                    self.statusBox.textCursor().deletePreviousChar()                      
                self.eraseThisManyCharacters = len('Elapsed time: ' 
                                    +  str('{:.3f}'.format (self.my_acq_thread.time_array[-1]*self.timeConversionFactor)) + ' '+self.units_string)
                self.statusBox.append ('Elapsed time: ' 
                                    +  str('{:.3f}'.format (self.my_acq_thread.time_array[-1]*self.timeConversionFactor)) + ' '+self.units_string)
                if len(self.my_acq_thread.time_array)<2:
                    self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.End)
                

#                self.statusBox.moveCursor (PyQt4.QtGui.QTextCursor.StartOf)



                # Check the timebase box to figure out how long to sleep
                self.tbase_index = self.timebase_box.currentIndex () 
                time.sleep (0.1) #(config.rates[self.tbase_index]/20.0)

                # Is it time to auto stop?
                if self.auto_stop and (time.time () > self.start_time + self.stop_time):
                                        
                    self.start_or_stop ()
                                            
            # If it's not time to update, sleep for a little while until it is
            else:
                
                # Update the displays anyway, because you don't want to wait for
                # the next data point (especially if the data rate is slow!)
                self.myManager.updateDisplays (self.running, self.time_per_point,    \
                        self.my_acq_thread.time_array, self.my_acq_thread.data_array)
                time.sleep (0.1)


        # If it's not running, update the plots anyway...to keep graphics features like
        # time axes updating.
        else:   # even when not collecting data, user may want to look at curves or even manipulate blank plots.  This line keeps the plots updated.         
            self.myManager.updateDisplays(self.running, self.time_per_point, \
#                                          [x*self.timeConversionFactor for x in self.my_acq_thread.time_array], self.my_acq_thread.data_array)
                                         self.my_acq_thread.time_array, self.my_acq_thread.data_array)

            if self.unitsHaveChanged: #if so, you need to recalculate the time scale for the plot's curves.  This does that!
                self.myManager.reattachAllDataToAllPlots(self.my_acq_thread.time_array, self.my_acq_thread.data_array, self.running)
                

            time.sleep (0.1)


    #----------------------------------------------------------------------------------

    def calibrateBoard (self, event):

        print ("calibrate board not implemented yet!")


    #----------------------------------------------------------------------------------

    def plotNavigation (self, event):

        self.nav.setEnabled(False)   # disable the menu item, or else the Qdialog can be opened again!
        self.navScreen = PyQt4.QtGui.QDialog (self)
        navScreenLayout = PyQt4.QtGui.QGridLayout ()
        navScreenText = PyQt4.QtGui.QLabel ('        Mouse Controls...\n\n\
        Inside the plot area: \n\n\
                Left button:\tPAN\n\
                Wheel roll:\tZOOM\n\
                Wheel button:\tZOOM WINDOW\n\
                Right button:\tUNDO (back one zoom state)\n\n\
        Axes: \n\n\
                Left button:\tPAN \n\
                Wheel roll:\tZOOM\n\
                Right button:\tOPTIONS MENU\n\n\
        Legend:\n\n\
                Right button:\tOPTIONS MENU\n\n\n\
        Splitter Frames:\n\n\
                Plots are separated from each other (as well\t\t\n\
                as the controls on the left) by "splitters" (the \n\
                light dotted lines).  Click and drag on these to \n\
                adjust the size of the plots.  You can even move  \n\
                unused plots or the controls out of view.\n\n\
        Time Scrolling:\n\n\
                Data will automatically scroll with time when the \n\
                time exceeds the original limit.  Note: scrolling \n\
                will stop if you zoom in to older data.\n\n\
        ') 
        navScreenLayout.addWidget (navScreenText, 0, 0, 1, 3)
        okButton = PyQt4.QtGui.QPushButton ("OK")
        okButton.setFixedWidth(70)
        navScreenLayout.addWidget(okButton, 1, 1)
        okButton.clicked.connect (self.navScreenClose)
        self.navScreen.setLayout (navScreenLayout)

        self.navScreen.setWindowTitle ('Plot Navigation Guide')
        self.navScreen.setWindowIcon (PyQt4.QtGui.QIcon ('polydaq_icon.png'))

        self.navScreen.show ()
        self.navScreen.activateWindow()


    #----------------------------------------------------------------------------------

    def navScreenClose (self):
        self.navScreen.close ()
        self.nav.setEnabled(True) # re-enable the menu item on the GUI
        

    #----------------------------------------------------------------------------------

    def scan_rate_info (self):

        info = PyQt4.QtGui.QMessageBox ()
        info.setWindowIcon (PyQt4.QtGui.QIcon ('polydaq_icon.png'))
        info.information (info, 'Note on Sampling Rates', 'How fast can I sample?\n\n' + \
                                 'It depends on the number of channels you read.\n\n' + \
                                 'The software takes a little less than 0.005 \n' +\
                                 'seconds to read a channe1, so reading N \n' + \
                                 'channels will require about N x 0.005 seconds per \n' + \
                                 'sample, or roughly:  \n\n' + \
                                 '     No. of channels       fastest sample time (s) \n' +\
                                 '     \t1 \t0.005 \n' + \
                                 '     \t2 \t0.010 \n' + \
                                 '     \t3 \t0.015 \n' + \
                                 '     \t4 \t0.020 \n' + \
                                 '     \t5 \t0.025 \n' + \
                                 '     \t6 \t0.030 \n' + \
                                 '     \t7 \t0.035 \n' + \
                                 '     \t8 \t0.040 \n' + \
                                 '     \t9 \t0.045 \n' + \
                                 '     \t10\t0.050 \n\n' + \
                                 'Selecting a faster rate will not cause an error; \n'+ \
                                 'the software will simply collect data as fast as it\n'+ \
                                 'can.  \n\n' +\
                                 'PolyDAQ saves the actual time step in the data \n' + \
                                 'file, so you can check the actual sample rate.' \
                                 , PyQt4.QtGui.QMessageBox.Ok)
            
    #----------------------------------------------------------------------------------

    def aboutScreen (self, event):

        about = PyQt4.QtGui.QMessageBox ()
        about.setWindowIcon (PyQt4.QtGui.QIcon ('polydaq_icon.png'))
        about.information (about, 'About', ' PolyDAQ Hardware'+
             ' by Dr. John Ridgely \n\n Software: ' + config.software_name \
            + ', \n\n by Dr. Glen Thorncroft and Dr. John Ridgely \n\n',
            PyQt4.QtGui.QMessageBox.Ok)


    # 'Sure you want to quit?' Dialog.-------------------------------------------------

    def closeEvent (self, event):

        if self.running == True:

            messagebox = PyQt4.QtGui.QMessageBox

            reply = messagebox.question (self, 'Warning!',
                "Data Aqcuisition still running! \nAre you sure you want to stop? \n(Note: all your data will be saved)",
                PyQt4.QtGui.QMessageBox.Yes 
                | PyQt4.QtGui.QMessageBox.No, PyQt4.QtGui.QMessageBox.No)

            if reply == PyQt4.QtGui.QMessageBox.Yes:
                # close the data file
                self.data_file.close ()
                sys.exit (0)     # this command works, whether it is an event or not
            else:
                # if exit is called from the menu, it didn't come from an EVENT!
                if event == False: 
                    return  
                else:
                    event.ignore ()

        else:
            reply = PyQt4.QtGui.QMessageBox.question (self, 'End Program',
                "Are you sure you want to quit?", PyQt4.QtGui.QMessageBox.Yes |
                PyQt4.QtGui.QMessageBox.No, PyQt4.QtGui.QMessageBox.No)
            if reply == PyQt4.QtGui.QMessageBox.Yes:
                sys.exit (0)
            else:
                # if exit is called from the menu, it didn't come from an EVENT!
                if event == False: 
                    return
                else:
                    event.ignore ()


#======================================================================================
# This is the entry point of the program, the code which runs when one starts the 
# program running. It just sets up the GUI object and makes it go; all the good stuff
# is in the other code. 

if __name__ == '__main__':

    app = PyQt4.QtGui.QApplication (sys.argv)

    # Create and display the splash screen
    sp_pic = PyQt4.QtGui.QPixmap ('polydaq_splash.png')
    splash = PyQt4.QtGui.QSplashScreen (sp_pic, PyQt4.QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask (sp_pic.mask ())
    splash.show ()
    start = time.time()

    # Show the program main window, which is actually useful
    form = Window ()
    while (time.time() - start)<2.0:
        time.sleep (0.01)
        app.processEvents ()
    splash.finish (form)
    
    form.show ()
    sys.exit (app.exec_ ())

