# PolyDAQ_PlotManager.py


import sys
import time
import glob
import PyQt4.QtCore                         # The Qt4 library, used to make the GUI
import PyQt4.QtGui
import PyQt4.Qwt5
import PolyDAQ_Plotter                      # Module which has plot drawing class
#import new_config as config

class PlotManager(PyQt4.QtGui.QWidget) :   #WHAT DO I PUT IN PARENTHESES?

    

    def __init__ (self, allPlots, theMainGUI):

        # what else goes here?
#        pass

#    def plotPanes(self, allPlots):
      
        self.mainGUI = theMainGUI
        self.readoutBoxWidth = 90
        self.readoutBoxHeight = 17

        self.a_scope_display ={}

        self.allPlots = allPlots   # list of plot groups (and associated channels)
        
        self.xmin = self.allPlots.xmin  # Initial xmin and xmax.  These will
        self.xmax = self.allPlots.xmax  # be updated by the individual plots!
        self.timeScrollingOn = True     # Initially, time scrolling is on.  This will
                                        # be updated by plots!
        self.unitsHaveChanged = False
        self.units_string = 's' #default plotting units is seconds
        self.timeConversionFactor = 1. #seconds by default, so default conversion factor is 1.
        self.oldTimeConversionFactor = 1. #this is to keep track after time units has changed, 
                                          # to convert time limits FROM former unit TO new one!

        self.allPlotsAndReadouts = PyQt4.QtGui.QSplitter (PyQt4.QtCore.Qt.Vertical)

        for a_plot in self.allPlots.plots:

            # Create a plot display and add it to the list of plot displays
            self.a_scope_display[a_plot['name']] = PolyDAQ_Plotter.Plot (  \
                                                    allPlots,  \
                                                    a_plot,    \
                                                    self)

#        self.scope_displays.append (a_scope_display)

            # Set up a plot group for the plot
            a_plot_group = PyQt4.QtGui.QFrame ()
            a_group_layout = PyQt4.QtGui.QHBoxLayout()
            a_group_layout.addWidget (self.a_scope_display[a_plot['name']]) 
#            a_plot_layout.addWidget (self.a_scope_display[a_plot['name']], 0, 0, 4, 6)            
            
            # Create all the readout boxes which will show current data values. First
            # make an empty list of readouts; then create each readout, configure it, 
            # and super-glue it to the end of the list

            a_readouts_layout = PyQt4.QtGui.QVBoxLayout()
#            y_position = 0
            spacer = PyQt4.QtGui.QLabel ()
            spacer.setFixedHeight(2)
            a_readouts_layout.addWidget (spacer)
            for a_channel in a_plot['channels']:
                # First create the readout
                a_readout = PyQt4.QtGui.QLabel ()
                a_readout.setFixedWidth (self.readoutBoxWidth)
                a_readout.setFixedHeight (self.readoutBoxHeight)
                a_readout.setFrameStyle (PyQt4.QtGui.QFrame.StyledPanel)               
                a_readout.setAlignment(PyQt4.QtCore.Qt.AlignRight | PyQt4.QtCore.Qt.AlignVCenter)
                

                # Now add the readout to the plot group and channel's parameter hash
                a_channel['readout'] =  a_readout  # adds new parameter called readout!
                a_readouts_layout.addWidget(a_channel['readout'])
#                y_position += 1

                # Might as well add a place to store minimum and maximum Y for a plot                
                a_plot['ymin'] = 9.9e99
                a_plot['ymax'] = -9.9e99


# places graphic below data readouts on each plot.  Future: perhaps show drawing of mouse with functions  
#            a_plot['helpBox'] = PyQt4.QtGui.QLabel ()
#            pixmap = PyQt4.QtGui.QPixmap('polydaq_icon.png')
#            pixmap.scaled(0.5, 0.5, PyQt4.QtCore.Qt.KeepAspectRatio)
#            a_plot['helpBox'].setPixmap(pixmap)
#            a_group_layout.addWidget (a_plot['helpBox'], y_position, 6)

# places help text below data readouts on each plot.   
#            a_plot['helpBox'] = PyQt4.QtGui.QLabel ('\n\n\nMouse\nfunctions\n\nleft click:\n   zoom window\nwheel click:\n   pan\nwheel roll:\n   zoom\nright click:\n   zoom back/\n   options')
#            a_group_layout.addWidget (a_plot['helpBox'], y_position, 6)    

            a_readouts_layout.addStretch(1)
            a_group_layout.addLayout(a_readouts_layout)     
            
#            a_group_layout.setColumnStretch (0, 1)
#            a_group_layout.setColumnStretch (1, 0)
            a_plot_group.setLayout (a_group_layout)
            self.allPlotsAndReadouts.addWidget(a_plot_group)


#-----------------------------------------------------------------------------------------------------------

    def time_units_condition(self):
        
        return self.unitsHaveChanged, self.units_string,  self.timeConversionFactor
        
# ----------------------------------------------------------------------------------------------------------           
            

    def updateDisplays(self, isDAQrunning, timePerPoint, timeArray, dataArray):


        self.timePerPoint = timePerPoint


        # Did the user change the plot units?  If so, change the appropriate
        # axis title, conversion factor, and recalculate the time axis limits!

        if self.unitsHaveChanged:
            
            # Now, convert x-axis limits:    
            self.xmin = self.xmin*self.timeConversionFactor/self.oldTimeConversionFactor
            self.xmax = self.xmax*self.timeConversionFactor/self.oldTimeConversionFactor

            # The combo of the previous and current conversion factor allows us to convert
            # from any unit to any unit.  This line remembers the "previous" conversion
            # factor for next time.
            self.oldTimeConversionFactor = self.timeConversionFactor

            # Change the units in the Axis name:    
            for a_plot in self.allPlots.plots:

#                self.a_scope_display[a_plot['name']].setAxisScale(PolyDAQ_Plotter.Plot.xBottom, self.xmin, self.xmax)
                if a_plot['xlabel'] != None:
                        
                    new_x_title = 'Time ('+ self.units_string + ')'
                    
                    self.a_scope_display[a_plot['name']].setAxisTitle (PolyDAQ_Plotter.Plot.xBottom, new_x_title)
#                self.a_scope_display[a_plot['name']].replot()

            self.unitsHaveChanged = False
            

        # Update the plots and curves.  

        ch_cnt = 0  # Channel count in the data array
                    # This channel count maps the actual data array to each plot.
                    # for example, if there are 2 selected TC channels to read,
                    # 1 selected strain guage to read, and 3 accelerometers to read,
                    # then:
                    #     data array indeces 0-1 go to plot 1
                    #     data array index   2   goes to plot 2
                    #     data array indeces 3-5 go to plot 3
        #**********************************************************************
                        
        for a_plot in self.allPlots.plots:
            

            if len(timeArray)>0:
                latestTime = timeArray[-1]*self.timeConversionFactor
                
            else: 
                latestTime = 0.0
            #print a_plot['name']
            self.a_scope_display[a_plot['name']].updatePlot (
                latestTime,     # Latest time
                timePerPoint*self.timeConversionFactor,
                a_plot['numberOfCurves'],              # Num. of active curves in plot 
                a_plot['ymin'],                        # max y value of this plot's curves
                a_plot['ymax'])                        # min y value
                                                       # method also updates time axis limits
                                                       # (self.xmin, self.xmax are global)

            curve_num = 0   # To the plotter module, each curve is numbered 0, 1, 2, etc.
                        # Recall that every available channel has been assigned to
                        # the plot, but we only update the plots that were chosen to read.
                        # In other words, perhaps the only third strain guage is being read...
                        # This means that the plotter will update only its curve number 2!
                                               
            if latestTime > 0.0 and isDAQrunning: 
                            
                for a_channel in a_plot['channels']:
                
                    if a_channel['cbox'].isChecked ():
                        self.a_scope_display[a_plot['name']].updateCurve (
                                curve_num,           
                                self.timePerPoint*self.timeConversionFactor,
                                [x*self.timeConversionFactor for x in timeArray],
                                dataArray[ch_cnt])
                        ch_cnt += 1
                    curve_num +=1    




            self.a_scope_display[a_plot['name']].replot()

                    


    def resetDisplays(self):

                
        # Reset plots
        for a_plot in self.allPlots.plots:
            self.a_scope_display[a_plot['name']].resetPlotAxes ()
            a_plot['ymin'] = 9.9e99                 #reset ymin and ymax trackers
            a_plot['ymax'] = -9.9e99                # for autoscaling


        # Reset numerical displays
        for a_plot in self.allPlots.plots:
            for a_channel in a_plot['channels']:
                a_channel['readout'].setText ('')   

        # Reset (Erase) curve displays
                
        for a_plot in self.allPlots.plots:
            curve_num = 0            
            for a_channel in a_plot['channels']:
                self.a_scope_display[a_plot['name']].reattachAllData (
                            curve_num,           
                            [-9.9e99],
                            [-9.9e99])
                curve_num +=1
            
                             
       

    def reattachAllDataToAllPlots(self, time_array, data_array, DAQ_wasJustStopped):
        


        # This matrix will be used to track whether [plot number][channel number] is ON or OFF.
        # Yes, the channels "checked" on the GUI is what we usually use; this matrix is a
        # copy made just at the end of data collection.  Why?  Because users may want to
        # navigate the plots after data collection is stopped.  Well, if, while they are doing
        # this, they start clicking different channels, it screws up the plots and causes
        # all sorts of weird errors.  Then and only then we need to have a stable copy of
        # what channels were selected.
        #
        # DAQ_wasJustStopped comes from self.running in the main GUI.  This marker tells us to
        # make a copy of the active channels the first time we run this function.  That was, if
        # users click different channels, it doesn't screw up the already-plotted data. 

        if len(time_array) == 0:
            return
        
        if DAQ_wasJustStopped: # copy channel "on" list
            self.channel_matrix = [['OFF' for x in range (10)] for x in range (10)]
            plot_num = 0
            for a_plot in self.allPlots.plots:
                curve_num = 0
                for a_channel in a_plot['channels']:
                
                    if (a_channel['cbox'].isChecked ()):
                        self.channel_matrix[plot_num][curve_num] = 'ON'
                
                    curve_num +=1
                plot_num +=1
                

        chan_count = 0 # this is the array column position.
        plot_num = 0
        for a_plot in self.allPlots.plots:
            curve_num = 0
            for a_channel in a_plot['channels']:
                
                if self.channel_matrix[plot_num][curve_num] == 'ON':
                    self.a_scope_display[a_plot['name']].reattachAllData (curve_num, [x*self.timeConversionFactor for x in time_array],
                                            data_array[chan_count])
                    chan_count +=1
                curve_num +=1
            plot_num +=1



#
#        chan_count = 0  # column in the array       
#        plot_num = 0    # track the plot number
#        for a_plot in self.allPlots.plots:
#
#            curve_num = 0 # curve number in the given plot
#            for a_channel in a_plot['channels']:
#                temp_channel_checklist[plot_num, curve_num]
#                if (a_channel['cbox'].isChecked ()):
#                
#                    self.a_scope_display[a_plot['name']].reattachAllData (curve_num, [x*self.timeConversionFactor for x in time_array],
#                                            data_array[chan_count])
#                    chan_count +=1
#                curve_num +=1
#            plot_num +=1


            self.a_scope_display[a_plot['name']].replot()
            

#         chan_count = 0       
#        for a_plot in self.allPlots.plots:
#            curve_num = 0 
#            for a_channel in a_plot['channels']:
#                if (a_channel['cbox'].isChecked ()):
#                    self.a_scope_display[a_plot['name']].reattachAllData (curve_num, [x*self.timeConversionFactor for x in time_array],
#                                            data_array[chan_count])
#                    chan_count +=1
#                curve_num +=1
#            self.a_scope_display[a_plot['name']].replot()
                   


