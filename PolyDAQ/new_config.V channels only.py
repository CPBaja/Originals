#--------------------------------------------------------------------------------------
# New format PolyDAQ configuration file.
# 
#   The configuration is written in Python rather than as a bunch of oddly formatted 
#   text. It defines every object of class PolyDAQ_config to have the given data; only
#   one such object will ever be created, the main configuration for a given run of the
#   PolyDAQ program. 
#
#   Comments must begin with a # as the first character on a line; one may not put
#   any comments after non-comment items on a line.
#
#   So there.
#
# Revisions
#
#   - 04-21-2014 JRR Original file, based somewhat on PolyDAQ_config.txt by GET
# 
#--------------------------------------------------------------------------------------

from datetime import date                   # Library used to figure out today's date
import time
from PyQt4.QtCore import *

import os

''' Module which contains a PolyDAQ graphical user interface configuration. 

This module contains the configuration for a PolyDAQ graphical user interface 
in a particular configuration. It should be imported by the main GUI program,
PolyDAQ_x.x.py, where the class created in this file will define the parameters
needed to set up the GUI in a particular configuration. 

Color names for reference:
Qt.white 	     3 	White (#ffffff)
Qt.black 	     2 	Black (#000000)
Qt.red 	     7 	Red (#ff0000)
Qt.darkRed      13 	Dark red (#800000)
Qt.green 	     8 	Green (#00ff00)
Qt.darkGreen    14 	Dark green (#008000)
Qt.blue 	     9 	Blue (#0000ff)
Qt.darkBlue     15 	Dark blue (#000080)
Qt.cyan         10 	Cyan (#00ffff)
Qt.darkCyan     16 	Dark cyan (#008080)
Qt.magenta 	11 	Magenta (#ff00ff)
Qt.darkMagenta 	17 	Dark magenta (#800080)
Qt.yellow 	      12 	Yellow (#ffff00)
Qt.darkYellow 	18 	Dark yellow (#808000)
Qt.gray 	      5 	Gray (#a0a0a4)
Qt.darkGray 	4 	Dark gray (#808080)
Qt.lightGray 	6 	Light gray (#c0c0c0)
Qt.transparent 	19 	a transparent black value (i.e., QColor(0, 0, 0, 0))
	
'''

#----------------------------------------------------------------------------------
# The system section has basic setup for communications, file storage, etc.


#----------------------------------------------------------------------------------

# The station referes to the partcular cart in the lab.  It's specified here
# because each PolyDAQ board has been calibrated and has unique calibration 
# constants.  Specifying the station here will (conveniently) assign the calibration
# constants for the particular board.  This is convenient because one SD card is 
# is universal -- the same SD card/image is used on every machine.  Then, the 
# calibration settings are set by simply changing the station number here:

station = 5 # select station 1-5.  The value -1 triggers an error message,
#              to indicate that the PolyDAQ software has not yet been configured 
#              for the particular station!


# The baud rate for communication with the PolyDAQ.  The PolyDAQ 2 talks through a
# USB-serial cable at 115200 baud; the PolyDAQ 1 talks at 9600 baud.
baud_rate = 115200

# Oversampling: the number of measurements to be taken at each channel and averaged
# each time.  A simple filter to reduce some noise.  The number ranges from 0-99
oversampling = 10

# The path to the directory in which data will be saved. 
data_file_path = os.path.expanduser('~') + '/Desktop/PolyDAQ_Data_Files' #'.'
print data_file_path

# Default File Name:
data_file_name = time.strftime("%a_%m.%d.%y_%I.%M%p")

# The extension for the data file name; .csv is most commonly used.
data_file_extension = 'csv'

# The software name is displayed in the main window
software_name = 'PolyDAQ v2.0, 9/6/16 (Python 2.7) ' #+ str (date.today ())

#---------------------------------------------------------------------------------
# Timebase section holds information about timing and the X axis of all graphs. 

# The list of sampling rates from which the user can choose. Code can be written 
# to convert each sample time in seconds into a text label; we could convert times
# over one minute to minutes, under 100ms to milliseconds, etc. when making the 
# strings
rates = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]

# The xlabel is the label for the time axis under the lowest graph on the page.
xlabel = 'Time (s)'

# This will be the starting/default time range (s) for all the graphs.
xmin = 0.0
xmax = 60.0

#----------------------------------------------------------------------------------
# The plots section. Each plot is created, then added to the list of plots. We 
# begin with an empty list of plots and add stuff to it
plots = []

##----------------------------------------------------------------------------------
## The first plot section. It sets overall plot parameters, then creates one or
## more channels, each of which is appended to the graph's channel list. The first
## line creates an empty dictionary (hash table); we'll add stuff to it next.
#newplot = {}
#
## The name of the plot. This name is shown in the 'Channels to Record' area
#newplot['name'] = 'Thermocouples (Type K)'
#
## The label below the x (time) axis on the plot. If this is the lowest plot or we
## need separate time axis labels, put a string here; if not, just put None here
#newplot['xlabel'] = None
#
## The label for the y axis, which shows the measured quantity and units
#newplot['ylabel'] = 'Temperature (<sup>o</sup>C)'
#
## The range for the y axis, as a list, for example [-10.0 10.0]
#newplot['ymin'] = 0.0 
#newplot['ymax'] = 100.
#
## Create an empty list for channels, then add channels to it
#newplot['channels'] = []
#
## Create each channel, giving channel command, name, slope, and offset. The command
## is one character sent to the PolyDAQ board to request that channel's data; the
## name is shown in the channel list; the slope and offset scale the raw A/D data.
#newplot['channels'].append ({'command' : '9',
##							 'name'    : 'Thermocouple 1',
##							 'abbrev'  : 'T1',
##							 'slope'   : (3.3)/4095/.005,
##							 'offset'  : -1.24974/.005,
#                                        'color'   : Qt.yellow})
#newplot['channels'].append ({'command' : '8',
#							 'name'    : 'Thermocouple 2',
#							 'abbrev'  : 'T2',
##							 'slope'   : (3.3)/4095./0.005,
##							 'offset'  : (-1.2522)/.005,
#                                        'color'   : Qt.green})
#newplot['channels'].append ({'command' : '7',
#							 'name'    : 'Thermocouple 3',
#							 'abbrev'  : 'T3',
##							 'slope'   : (3.3)/4095/.005,
##							 'offset'  : (-1.25)/.005,
#                                        'color'   : Qt.red})
#newplot['channels'].append ({'command' : '6',
#							 'name'    : 'Thermocouple 4',
#							 'abbrev'  : 'T4',
##							 'slope'   : (3.3)/4095/.005,
##							 'offset'  : (-1.24775)/.005,
#                                       'color'   : Qt.cyan})
#
# Append the plot data in newplot to the array of plots in variable plots.
#plots.append (newplot)


#----------------------------------------------------------------------------------
# The first plot section. It sets overall plot parameters, then creates one or
# more channels, each of which is appended to the graph's channel list. The first
# line creates an empty dictionary (hash table); we'll add stuff to it next.
newplot = {}

# The name of the plot. This name is shown in the 'Channels to Record' area
newplot['name'] = 'Voltages (-8 to +8V)'
# The label below the x (time) axis on the plot. If this is the lowest plot or we
# need separate time axis labels, put a string here; if not, just put None here
newplot['xlabel'] = 'Time (s)'

# The label for the y axis, which shows the measured quantity and units
newplot['ylabel'] = 'Voltage (V)'

# The range for the y axis, as a list, for example [-10.0 10.0]
newplot['ymin'] = -10. 
newplot['ymax'] = +10.

# Create an empty list for channels, then add channels to it
newplot['channels'] = []

# Create each channel, giving channel command, name, slope, and offset. The command
# is one character sent to the PolyDAQ board to request that channel's data; the
# name is shown in the channel list; the slope and offset scale the raw A/D data.
newplot['channels'].append ({'command' : 'A',
							 'name'    : 'Voltage 1',
							 'abbrev'  : 'V1',
#							 'slope'   : 0.00513,
#							 'offset'  : -8.8537,
                                        'color'   : Qt.darkYellow})
newplot['channels'].append ({'command' : 'B',
							 'name'    : 'Voltage 2',
							 'abbrev'  : 'V2',
#							 'slope'   : 0.00513,
#							 'offset'  : -8.8537,
                                        'color'   : Qt.magenta})
#newplot['channels'].append ({'command' : 'E',
#							 'name'    : 'Strain Bridge 3',
#							 'abbrev'  : 'S3',
#							 'slope'   : 1.0,
#							 'offset'  : 0.0})
#newplot['channels'].append ({'command' : 'F',
#							 'name'    : 'Strain Bridge 4',
#							 'abbrev'  : 'S4',
#							 'slope'   : 1.0,
#							 'offset'  : 0.0})

# Append the plot data in newplot to the array of plots in variable plots.
plots.append (newplot)
#
#
#
##----------------------------------------------------------------------------------
## The first plot section. It sets overall plot parameters, then creates one or
## more channels, each of which is appended to the graph's channel list. The first
## line creates an empty dictionary (hash table); we'll add stuff to it next.
#newplot = {}
#
## The name of the plot. This name is shown in the 'Channels to Record' area
#newplot['name'] = 'Millivoltages (0 to +30mV)  POSITIVE V ONLY'
#
#
## The label below the x (time) axis on the plot. If this is the lowest plot or we
## need separate time axis labels, put a string here; if not, just put None here
#newplot['xlabel'] = 'Time (s)'

## The label for the y axis, which shows the measured quantity and units
#newplot['ylabel'] = 'Voltage (mV)'
#
## The range for the y axis, as a list, for example [-10.0 10.0]
#newplot['ymin'] = 0.
#newplot['ymax'] = 30.
#
## Create an empty list for channels, then add channels to it
#newplot['channels'] = []
#
## Create each channel, giving channel command, name, slope, and offset. The command
## is one character sent to the PolyDAQ board to request that channel's data; the
## name is shown in the channel list; the slope and offset scale the raw A/D data.
#newplot['channels'].append ({'command' : 'E',
#							 'name'    : 'Millivoltage 1',
#							 'abbrev'  : 'M1',
##							 'slope'   : 1.0, #0.00803358, # 3.3/4095./105.*1000.*4095,
##							 'offset'  : 0.0, #0.05869222,
#                                        'color'  : Qt.red})
#newplot['channels'].append ({'command' : 'F',
#							 'name'    : 'Millivoltage 2',
#							 'abbrev'  : 'M2',
##							 'slope'   : 1.0, #0.00803358, #3.3/4095./105*1000.,
##							 'offset'  : 0.0, #0.05869222,
#                                        'color'   : Qt.cyan})
##newplot['channels'].append ({'command' : '9',
##							 'name'    : 'Strain Bridge 3',
##							 'abbrev'  : 'S3',
##							 'slope'   : 1.0,
##							 'offset'  : 0.0})
##newplot['channels'].append ({'command' : '8',
##							 'name'    : 'Strain Bridge 4',
##							 'abbrev'  : 'S4',
##							 'slope'   : 1.0,
##							 'offset'  : 0.0})
#
## Append the plot data in newplot to the array of plots in variable plots.
#plots.append (newplot)


#----------------------------------------------------------------------------------
# A second plot section. Please see the comments in the first plot section. We
# re-initialize the variable newplot, then add new data to it. 
#newplot = {}
#newplot['name'] = 'Accelerometers'
#newplot['xlabel'] = xlabel

#newplot['ylabel'] = 'Acceleration (g)'
#newplot['ymin'] = -2.5
#newplot['ymax'] = 2.5
#newplot['channels'] = []
#
#newplot['channels'].append ({'command' : 'X',
#							 'name'    : 'X Acceleration',
#							 'abbrev'  : 'aX',
#							 'slope'   : 0.000061,
#							 'offset'  : 0.0})
#newplot['channels'].append ({'command' : 'Y',
#							 'name'    : 'Y Acceleration',
#							 'abbrev'  : 'aY',
#							 'slope'   : 0.000061,
#							 'offset'  : 0.0})
#newplot['channels'].append ({'command' : 'Z',
#							 'name'    : 'Z Acceleration',
#							 'abbrev'  : 'aZ',
#							 'slope'   : 0.000061,
#							 'offset'  : 0.0})
#
# Append the plot data in newplot to the array of plots in variable plots.
#plots.append (newplot)


#--------------------------------------------------------------------------------------
####################################
def calibrationEquation (a2d_reading, measurand):


   

    if (measurand == '9'): #Thermocouple 1
        if station == 1: value = a2d_reading*(3.3)/4095/.005 - 1.24974/.005  # station 1
        if station == 2: value = a2d_reading*(3.3)/4095/.005 - 1.2539/.005   # station 2
        if station == 3: value = a2d_reading*(3.3)/4095/.005 - 1.25475/.005  # station 3
        if station == 4: value = a2d_reading*(3.3)/4095/.005 - 1.25475/.005  # station 4 
        if station == 5: value = a2d_reading*(3.3)/4095/.005 - 1.25375/.005  # station 5
    elif (measurand == '8'): # Thermocouple 2
        if station == 1: value = a2d_reading*(3.3)/4095./0.005 - 1.2522/.005 # station 1
        if station == 2: value = a2d_reading*(3.3)/4095/.005 - 1.24965/.005  # station 2
        if station == 3: value = a2d_reading*(3.3)/4095/.005 - 1.249/.005    # station 3
        if station == 4: value = a2d_reading*(3.3)/4095/.005 - 1.25397/.005  # station 4
        if station == 5: value = a2d_reading*(3.3)/4095/.005 - 1.249/.005  # station 5
    elif (measurand == '7'): # Thermocouple 3
        if station == 1: value = a2d_reading*(3.3)/4095./0.005 - 1.25/.005   # station 1
        if station == 2: value = a2d_reading*(3.3)/4095/.005 - 1.25015/.005  # station 2
        if station == 3: value = a2d_reading*(3.3)/4095/.005 - 1.246/.005    # station 3
        if station == 4: value = a2d_reading*(3.3)/4095/.005 - 1.250615/.005  # station 4
        if station == 5: value = a2d_reading*(3.3)/4095/.005 - 1.24885/.005  # station 5
    elif (measurand == '6'): # Thermocouple 4
        if station == 1: value = a2d_reading*(3.3)/4095./0.005- 1.24775/.005 # station 1
        if station == 2: value = a2d_reading*(3.3)/4095/.005 - 1.2534/.005   # station 2
        if station == 3: value = a2d_reading*(3.3)/4095/.005 - 1.25125/.005  # station 3
        if station == 4: value = a2d_reading*(3.3)/4095/.005 - 1.252265/.005  # station 4
        if station == 5: value = a2d_reading*(3.3)/4095/.005 - 1.252/.005  # station 5 
        
    elif (measurand == 'A'): # Voltage 1
        value = a2d_reading*0.00513 - 8.8537
    elif (measurand == 'B'): # Voltage 2
        value = a2d_reading*0.00513 - 8.8537

    elif (measurand == 'E'): # Millivoltage 1
    
        if (a2d_reading <= 150): 
            if station == 1: value = (-1.71396e-5)*a2d_reading ** 2 + 0.01136*a2d_reading - 0.1793 #station 1
            if station == 2: value = (-1.80897e-5)*a2d_reading ** 2 + 0.011422*a2d_reading - 0.1881 #station 2
            if station == 3: value = (-9.0919e-6)*a2d_reading ** 2 + 0.010041*a2d_reading - 0.20884 #station 3
            if station == 4: value = (-1.42525e-5)*a2d_reading ** 2 + 0.010877*a2d_reading - 0.1957 #station 4
            if station == 5: value = (-6.5858e-6)*a2d_reading ** 2 + 0.009567*a2d_reading - 0.25476 #station 5
            
        else:  
            if station == 1: value = (-4.5337e-9)*a2d_reading ** 2 + 0.008051*a2d_reading - 0.04801 #station 1
            if station == 2: value = (2.0686e-9)*a2d_reading ** 2 + 0.0080179*a2d_reading - 0.030353 #station 2    
            if station == 3: value = (1.6738e-9)*a2d_reading ** 2 + 0.0080214*a2d_reading - 0.09074 #station 3
            if station == 4: value = (1.791559e-9)*a2d_reading ** 2 + 0.0080229*a2d_reading - 0.05407 #station 4
            if station == 5: value = (1.9942e-9)*a2d_reading ** 2 + 0.0080173*a2d_reading - 0.15493 #station 5

    elif (measurand == 'F'): # Millivoltage 2
 
        if (a2d_reading <= 150): 
            if station == 1: value = (-1.03404e-5)*a2d_reading ** 2 + 0.010282*a2d_reading - 0.21979 #station 1
            if station == 2: value = (-1.95506e-5)*a2d_reading ** 2 + 0.011726*a2d_reading - 0.18104 #station 2
            if station == 3: value = (-1.2052e-5)*a2d_reading ** 2 + 0.01053*a2d_reading - 0.19212 #station 3
            if station == 4: value = (-1.75013e-5)*a2d_reading ** 2 + 0.011398*a2d_reading - 0.17914 #station 4
            if station == 5: value = (-2.37306e-5)*a2d_reading ** 2 + 0.012318*a2d_reading - 0.16209 #station 5
            
        else:  
            if station == 1: value = (-3.72858e-9)*a2d_reading ** 2 + 0.008067*a2d_reading - 0.13588   # station 1   
            if station == 2: value = (5.69066e-10)*a2d_reading ** 2 + 0.008031*a2d_reading - 0.02149 #station 2
            if station == 3: value = (1.57139e-9)*a2d_reading ** 2 + 0.008028*a2d_reading - 0.06840 #station 3            
            if station == 4: value = (1.24726e-9)*a2d_reading ** 2 + 0.008034*a2d_reading - 0.03039 #station 4
            if station == 5: value = (1.39109e-9)*a2d_reading ** 2 + 0.008028*a2d_reading + 0.02078 #station 5

    return value

####################################


def init_text ():
    ''' Function which puts the configuration just read from this file into a string.
    '''

    astring = 'Station:    ' + str(station) + '\n'    \
                + 'Baud rate:    ' + str (baud_rate) + '\n'                                     \
                + 'Oversampling: ' + str(oversampling) + '\n'                                \
			+ 'File path:    ' + data_file_path + '\n'                                \
			+ 'Extension:    ' + data_file_extension + '\n'                           \
			+ 'Data rates:   ' + str (rates) + '\n'                                   \
			+ 'X axis label: ' + str(xlabel) + '\n'                                    \
			+ 'Time range:   ' + str(xmin) + ' to '+str(xmax)                                 \
			+ '\nPlots:\n'
    for plot in plots:
        astring += '    ' + plot['name'] + ':\n'                                      \
				+  '        X label:  ' + str (plot['xlabel']) + '\n'                 \
				+  '        Y label:  ' + plot['ylabel'] + '\n'                       \
				+  '        Y range:  ' + str (plot['ymin']) + ' to '                 \
				+  str (plot['ymax']) + '\n' + '        Channels:\n'
        for channel in plot['channels']:
            astring += '            ' + channel['name'] + ' (' + channel['abbrev']    \
					+ '):' +  '   Command: ' + channel['command'] + '\n' #\
#					+  '                Slope:   ' + str (channel['slope']) + '\n'    \
#					+  '                Offset:  ' + str (channel['offset']) + '\n'

    astring += '\nCalibrated for PolyDAQ Station ' + str(station)  + '.\n' + \
               'If this is not your station, call your instructor!\n'    
 
    return astring

#======================================================================================
# This is test code which only runs if this file is called as a program on the command
# line. Usually this file is called from within the PolyDAQ program and the lines below
# are ignored. 

if __name__ == '__main__':

	# Print the configuration so the user can check that it's correct
	a_string = init_text ()
	print (a_string)


