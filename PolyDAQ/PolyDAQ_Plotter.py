#======================================================================================
# File: PolyDAQ_Plotter.py
#    A module which implements data plotting with mouse controlled zooming, scrolling,
#    changing the appearance of data traces, and other fancy stuff. 
#
# Revisions:
#    10-31-2014 GET Original file
#    04-25-2015 JRR Modified to make a bit more modular
#
# Sources:
#   1. qplt (comes with PyQwt) provided basic framework. 
#      (Copyright (C) 2003-2010 Gerard Vermeulen)
#
#   2. DataPlot.py by Dorian Scholz 
#      github.com/DorianScholz/ServoTool/blob/master/src/common/DataPlot.py
#      I used this file for some structure, and the mousewheel zoom function.
#
#   3. QwtImagePlotDemo.py by unknown author
#      pyqwt.sourceforge.net/examples/QwtImagePlotDemo.py.html
#      I borrowed the structure of the mouseclick events: zoom and pan.  I HAD used the
#      built-in functions PQwtPlotZoomer and PlotPanner, but abandoned those because 
#      (1) the zoomstack was faulty (if you panned out or if time scrolled beyond the 
#          original axis limits, and you zoomed outside those limits, the plot axes 
#          failed/blanked out.  
#      (2) panning and mousewheel zooming could not be connected to the normal click-
#          and-drag zoom window "zoom stack," meaning the zoom steps could not be 
#          remembered.  I decided that creating the two functions from scratch would 
#          give me complete control.
#======================================================================================

import sys
import glob
import time

import functools                # For functions to be passed as arguments

from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from PyQt4.Qwt5 import *
#from PyQt4.Qwt5.anynumpy import *
from numpy import *





#======================================================================================

class Plot (QwtPlot):
    ''' This class implements a real-time plot window with dynamic mouse-controlled
    scrolling, panning, and zooming.
    '''

    def __init__ (self, allPlots, a_plot, the_manager):

        ''' Initialize the plotting screen.
        '''

        QwtPlot.__init__(self)

        
        self.allPlots = allPlots
        self.a_plot = a_plot        
        self.manager= the_manager
 
        self.ymin = self.a_plot['ymin']
        self.ymax = self.a_plot['ymax']
        self.ch_names = []
        
        for channel in self.a_plot['channels']:
                        
                        self.ch_names.append(channel['abbrev'])
                    
        y_title = QwtText (self.a_plot['ylabel'])

                # Now, set plot parameters with these INITIAL properties 
        
        self.setAxisScale (QwtPlot.yLeft,   self.ymin, self.ymax)
        self.setAxisScale (QwtPlot.xBottom, self.allPlots.xmin, self.allPlots.xmax)
        # font
        Font = QFont('SansSerif')
        font = QFont (Font)
        font.setPointSize (9.8)
        font.setBold (True)
        
        y_title.setFont (font)

        
        self.setAxisTitle (QwtPlot.yLeft, y_title)

        if self.a_plot['xlabel'] != None:
                        x_title = QwtText (self.a_plot['xlabel'])
                        x_title.setFont (font)
                        self.setAxisTitle (QwtPlot.xBottom, x_title)
                        

        # Set initial line and symbol sizes and colors to be used when multiple curves are shown

        self.ch_pen_colors = []
        for channel in self.a_plot['channels']:
                        
                        self.ch_pen_colors.append(channel['color'])

#        self.ch_pen_colors = [Qt.yellow, Qt.cyan, Qt.red, Qt.green, Qt.blue, \
#                              Qt.white, Qt.magenta, Qt.darkYellow]
        self.ch_line_styles = 8 * [Qt.SolidLine]
        self.ch_line_widths = 8 * [1]

        self.ch_symbol_styles = [QwtSymbol.Ellipse, QwtSymbol.Rect, QwtSymbol.Diamond,
                                 QwtSymbol.Ellipse, QwtSymbol.Rect, QwtSymbol.Diamond,
                                 QwtSymbol.Ellipse, QwtSymbol.Rect]        
        self.ch_symbol_sizes = 8 * [3]

        # Plot size (set by widget in PolyDAQ... I don't know if it's still needed) 
        self.size = None

        # Create an initially empty list of curves for the plot
        self.curves = []

        # look
        self.setCanvasBackground (Qt.black)
        #self.plotLayout ().setMargin(0)
        self.plotLayout ().setAlignCanvasToScales (True)

        
        
        #cr = self.plotLayout ().canvasRect()
        #print cr.left()

        grid = QwtPlotGrid ()
        grid.attach (self)
        grid.setPen (QPen (Qt.darkGreen, 1, Qt.DotLine))
        
        self.legend = QwtLegend ()
        self.insertLegend (self.legend, Qwt.QwtPlot.RightLegend)
#        self.legend.setToolTip ('options...')
#        self.setToolTip('options...')
        

        # initialize curves
        for index, item in enumerate (self.ch_names):
            self.curves += [QwtPlotCurve (self.ch_names[index])]

            self.curves[index].setPen (QPen (self.ch_pen_colors[index],
                                       self.ch_line_widths[index],
                                       self.ch_line_styles[index]))
            self.curves[index].setSymbol (QwtSymbol (self.ch_symbol_styles[index],
                                          QBrush (self.ch_pen_colors[index]),
                                          QPen (self.ch_pen_colors[index]),
                                          QSize (self.ch_symbol_sizes[index], 
                                          self.ch_symbol_sizes[index])))
            self.curves[index].attach (self)

        if self.size:
            self.resize (self.size)

        # Clear zoom stack
        self.zoomStack = []

        # Set plot "time scrolling" on
        self.manager.timeScrollingOn = True
        self.wasTimeScrollingOn = True

        # Set the initial value of autoscaling on the Y axis
        self.autoYScaleOn = False

        # Initially, multiple graphs are not time-synchronized, meaning that, when the user
        # zooms in or out in one of the graphs, the other graphs do not change in time.
#        self.syncTimeOn = True

        self.latestTime = 0
        self.alreadyWheeling = False
        self.axisCursorChanged = False
        self.panIsReal = False

#        self.setMouseTracking(True)


#                print (self.canvas().width(), self.canvas().height())
#        print (self.plotLayout().canvasRect().bottomLeft())

    #----------------------------------------------------------------------------------



    def mousePressEvent (self, event):
        ''' Respond to a press of the mouse.
        '''

        self.alreadyWheeling = False
        self.cursorChanged = False

        # Get cursor position in pixels 
        self.xpix1 = event.pos ().x () 
        self.ypix1 = event.pos ().y ()
        

        # x-pixel adjust (shifts location calculations to account for the axis thickness!)
        self.xpixel_adjust = self.plotLayout().canvasRect().left()
                #self.xpixel_adjust = self.transform(Qwt.QwtPlot.xBottom, self.xmin)
                #print (event.pos().x(), event.pos().y(),self.plotLayout().canvasRect().left())
                       #self.canvas().bottomLeft())
                       #event.globalPos().x())


        # Now convert position to REAL x,y units (and shift the x-reading!)
        self.x1 = self.invTransform (Qwt.QwtPlot.xBottom, \
                                     self.xpix1 - self.xpixel_adjust)
        self.y1 = self.invTransform (Qwt.QwtPlot.yLeft, self.ypix1)

        # Which button got clicked?
        if event.buttons () == Qt.MidButton: 
            self.action = "zoom"
            self.firstCrossHairsExist = False

        elif event.buttons () == Qt.LeftButton:
            self.action = "pan"
            #record zoom state BEFORE PANNING STARTS and add it to stack
            self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)
            self.zoomStack.append (self.zoomState)
            self.autoYScaleOn = False
            if self.x1 <self.manager.xmax:
                QApplication.setOverrideCursor(QCursor(Qt.ClosedHandCursor))
                self.cursorChanged = True

        elif event.buttons () == Qt.RightButton:
            self.action = "rightClick"

#        # Fake a mouse move to establish some initial values for self.x2, etc.
#        self.mouseMoveEvent (event)    


        # establish some initial values for self.x2, etc.

        # get 2nd cursor position in pixels
        self.xpix2 = event.pos ().x ()
        self.ypix2 = event.pos ().y ()

        # now convert position to REAL x,y (and correct the x-reading)
        self.x2 = self.invTransform (Qwt.QwtPlot.xBottom, 
                                     self.xpix2 - self.xpixel_adjust)
        self.y2 = self.invTransform (Qwt.QwtPlot.yLeft, self.ypix2)


    #----------------------------------------------------------------------------------

    def mouseMoveEvent(self, event):
        ''' This method handles cursor position, but ONLY if a button was clicked.
        It doesn't display mouse position on the GUI.
        '''
        # get 2nd cursor position in pixels
        self.xpix2 = event.pos ().x ()
        self.ypix2 = event.pos ().y ()

        # now convert position to REAL x,y (and correct the x-reading)
        self.x2 = self.invTransform (Qwt.QwtPlot.xBottom, 
                                     self.xpix2 - self.xpixel_adjust)
        self.y2 = self.invTransform (Qwt.QwtPlot.yLeft, self.ypix2)

        if self.action == "zoom":   

            # draw first crosshairs, if they don't already exist:
            if self.firstCrossHairsExist == False: 

                # draw crosshairs if and when mouse is inside the plot
                if self.x1 > self.manager.xmin and  self.x1 < self.manager.xmax \
                        and self.y1 > self.ymin and self.y1 < self.ymax:

                    # draw first set of crosshairs of "zoom window"
                    self.vLineStart = QwtPlotMarker ()
                    self.vLineStart.setLineStyle (QwtPlotMarker.VLine)
                    self.vLineStart.setLinePen (QPen (Qt.lightGray,1, Qt.SolidLine))
                    self.vLineStart.setXValue (self.x1)
                    self.vLineStart.attach (self)

                    self.hLineStart = QwtPlotMarker ()
                    self.hLineStart.setLineStyle (QwtPlotMarker.HLine)
                    self.hLineStart.setLinePen (QPen (Qt.lightGray,1))
                    self.hLineStart.setYValue (self.y1)
                    self.hLineStart.attach (self)
                    self.firstCrossHairsExist = True
                    self.secondCrossHairsExist = False
                    self.replot ()

                else:                   # reassign x1, y1 until cursor falls within plot
                    self.x1 = self.x2
                    self.y1 = self.y2

            # Then get 2nd cursor position in pixels
            if self.firstCrossHairsExist == True:  

                # draw second set of crosshairs of "zoom window"

                if self.secondCrossHairsExist == True:  # erase the previous crosshairs
                    self.vLineEnd.detach ()
                    self.hLineEnd.detach ()
                    self.replot ()

                # In case you move outside the graph (which you can),
                # these max/min functions limit the position values
                # to exist within the plot limits 
                self.x2 = max (self.x2, self.manager.xmin)
                self.x2 = min (self.x2, self.manager.xmax)
                self.y2 = max (self.y2, self.ymin)
                self.y2 = min (self.y2, self.ymax)

                self.vLineEnd = QwtPlotMarker ()
                self.vLineEnd.setLineStyle (QwtPlotMarker.VLine)
                self.vLineEnd.setLinePen (QPen (Qt.lightGray, 1))
                self.vLineEnd.setXValue (self.x2)
            
                self.hLineEnd = QwtPlotMarker ()
                self.hLineEnd.setLineStyle (QwtPlotMarker.HLine)
                self.hLineEnd.setLinePen (QPen (Qt.lightGray, 1))
                self.hLineEnd.setYValue (self.y2)
            
                self.vLineEnd.attach (self)
                self.hLineEnd.attach (self)
                self.secondCrossHairsExist = True 

        elif self.action == "pan":

#            self.autoYScaleOn = False 

            if self.x2 <self.manager.xmax and not self.cursorChanged:
                QApplication.setOverrideCursor(QCursor(Qt.ClosedHandCursor))
                self.cursorChanged = True
                
            if self.x2 >self.manager.xmin:
                deltax =  self.x2 - self.x1
            else: deltax = 0.
            
            if self.y2 > self.ymin:            
                deltay =  self.y2 - self.y1 
            else: deltay = 0.
            
            self.manager.xmin -= deltax
            self.manager.xmax -= deltax
            self.ymin -= deltay
            self.ymax -= deltay

            if deltax > 0 or deltay > 0:
                self.panIsReal = True
#                self.autoYScaleOn = False
            else:
                self.panIsReal = False
                # will use this later to test for just a click. 

            self.setAxisScale(QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)
            self.setAxisScale(QwtPlot.yLeft, self.ymin, self.ymax)

            # if new window has "room" for new data, turn on scrolling.
            # otherwise we presume the user wants to focus on an earlier section of data;
            # hence turn scroling off...
            if self.manager.xmax >= self.latestTime:
                self.manager.timeScrollingOn = True
            else:
                self.manager.timeScrollingOn = False

        self.replot()


    #----------------------------------------------------------------------------------

    def mouseReleaseEvent (self, event): 
        ''' This method handles the mouse button release and completes the zoom, pan, 
        or undo action.
        '''

        # which button was released?
        if self.action == "zoom":   # Finish the Zoom Window

            # did you just click and release?  Don't zoom then.
            if (self.x1 == self.x2 or self.y1 == self.y2):
                
                if  self.firstCrossHairsExist == True:
                    self.vLineStart.detach ()
                    self.hLineStart.detach ()
                    self.vLineEnd.detach ()
                    self.hLineEnd.detach ()
                    self.replot ()
                return

            else:                    # update axis limits, zoomstate, and zoomstack

                # calculate PRIOR zoom state and save it to stack                           
                self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)   
                self.zoomStack.append (self.zoomState)

                self.autoYScaleOn = False

                self.manager.xmin = min (self.x1, self.x2)  # max and min here just establishes 
                self.manager.xmax = max (self.x1, self.x2)  # which x position is hi and lo value
                self.ymin = min (self.y1, self.y2)
                self.ymax = max (self.y1, self.y2)

                # Erase zoom window lines
                self.vLineStart.detach ()
                self.hLineStart.detach ()
                self.vLineEnd.detach ()
                self.hLineEnd.detach ()

                self.setAxisScale (QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)
                self.setAxisScale (QwtPlot.yLeft, self.ymin, self.ymax)

        elif self.action == "pan":      # finish the Pan
                QApplication.restoreOverrideCursor()
                # did you just click and release?  Don't save the last zoom state.  "Pop" it out!
                if not self.panIsReal:
                    # Retreive previous zoom state (removes it from stack)
                    if len (self.zoomStack) > 0:  
                        dummy1, dummy2, dummy3, dummy4, dummy5, dummy6 = self.zoomStack.pop ()
                

        elif self.action == "rightClick":

            # Did you click-and-release inside the plot?  Then UNDO (go back to 
            # previous zoom state).
            if self.x2 >= self.manager.xmin and self.x2 <= self.manager.xmax \
                            and self.y2 >= self.ymin and self.y2 <= self.ymax:

                self.action = "previousZoomState"
                # Retreive previous zoom state (removes it from stack)
                if len (self.zoomStack) > 0:
                    self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn = self.zoomStack.pop ()

                    self.setAxisScale(QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)
                    self.setAxisScale(QwtPlot.yLeft, self.ymin, self.ymax)
                    
                    self.wasTimeScrollingOn = self.manager.timeScrollingOn                      
                else:
                    return

            # Did you click on the y axis (which is any x value below zero)? 
            # Then drop down a menu.
            elif self.x2 < self.manager.xmin:

                menu = QMenu()
                sub1 = menu.addAction ('Zoom all y')
                

                if self.autoYScaleOn == True:
                    sub2 = menu.addAction ('Turn Autoscale OFF')
                else:
                    sub2 = menu.addAction ('Turn Autoscale ON')
                sub3 = menu.addAction ('Manually set axis limits...')

                
                if self.latestTime == 0:
                    sub1.setEnabled (False)
                    sub2.setEnabled (False)
                else:
                    sub1.setEnabled (True)
                    sub2.setEnabled (True)

                
                sub1.triggered.connect (self.zoomAll_y)
                sub2.triggered.connect (self.autoYScale)
                sub3.triggered.connect (self.newYAxisLimits)
                menu.exec_ (self.mapToGlobal (QPoint (self.xpix2, self.ypix2)))


            # Did you click on the time axis (any real y value below zero)?  
            # Then drop down menu.
            elif self.y2 < self.ymin:

                menu = QMenu ()
                sub1 = menu.addAction ('Zoom all time')
                sub2 = menu.addAction ('Pan to latest data')
                sub3 = menu.addAction ('Manually set axis limits...')
                unitsSubMenu = menu.addMenu('Change plot time units')
                sub4 = unitsSubMenu.addAction('s')
                sub5 = unitsSubMenu.addAction('min')
                sub6 = unitsSubMenu.addAction('h')
                sub7 = unitsSubMenu.addAction('d')
                sub8 = unitsSubMenu.addAction('fortnights')

#                sub4 = menu.addAction ('Navigation:')
#                sub5 = menu.addAction ('  click wheel: pan time axis')
#                sub6 = menu.addAction ('  roll wheel: zoom time axis')
                if self.manager.timeScrollingOn == True:
                    sub2.setEnabled(False) 
                else:
                    sub2.setEnabled(True)
                    
                if self.manager.units_string == 's':
                    sub4.setEnabled(False)
                else: sub4.setEnabled(True)
                
                if self.manager.units_string == 'min':
                    sub5.setEnabled(False)
                else: sub5.setEnabled(True)
                
                if self.manager.units_string == 'h':
                    sub6.setEnabled(False)
                else: sub6.setEnabled(True)
                
                if self.manager.units_string == 'd':
                    sub7.setEnabled(False)
                else: sub7.setEnabled(True)

                if self.manager.units_string == 'fortnights':
                    sub8.setEnabled(False)
                else: sub8.setEnabled(True)
                    
                sub1.triggered.connect (self.zoomAll_time)
                sub3.triggered.connect (self.newTimeAxisLimits)
                sub2.triggered.connect (self.resumeTimeScrolling)
                sub4.triggered.connect(self.change_units_to_seconds)
                sub5.triggered.connect(self.change_units_to_minutes)
                sub6.triggered.connect(self.change_units_to_hours)
                sub7.triggered.connect(self.change_units_to_days)
                sub8.triggered.connect(self.change_units_to_fortnights)
                
                
                menu.exec_ (self.mapToGlobal (QPoint (self.xpix2, self.ypix2)))

            # Did you click on the first legend item?  The drop down menu.
            elif self.x2 > self.manager.xmax: # area to right of plot.  May be a legend item!

                menu = QMenu()

                # Identify which item got clicked                
                if self.ypix2 < 22:                                                   # First Plot item
                    curveClickedNumber = 0  
                elif self.ypix2 > 22 and self.ypix2 < 44:                             # 2nd Plot item
                    curveClickedNumber = 1  
                elif self.ypix2 > 44 and self.ypix2 < 66 and len (self.curves)>=3:    # 3rd Plot item (if it exists)
                    curveClickedNumber = 2  
                elif self.ypix2 > 66 and self.ypix2 < 88 and len (self.curves)>=4:    # 4th item (if it exists)
                    curveClickedNumber = 3  
                else:
                    return

                # is the item visible?  if yes, give option of invisibility:
                if self.curves[curveClickedNumber].isVisible() == True:
                    sub1 = menu.addAction ('Turn curve '
                        + self.ch_names[curveClickedNumber] + ' off')
                else:
                    sub1 = menu.addAction ('Turn curve '
                        + self.ch_names[curveClickedNumber] + ' on')

                sub2 = menu.addAction ('Curve properties ...')

                # lambda command allows us to call functions that pass variables!
                sub1.triggered.connect \
                    (lambda:self.toggleVisibility (curveClickedNumber))
                sub2.triggered.connect \
                    (lambda:self.curveProps (curveClickedNumber))

                menu.exec_(self.mapToGlobal(QPoint(self.xpix2, self.ypix2)))

        # if new window has "room" for new data, turn on scrolling.
        # otherwise we presume the user wants to focus on an earlier section of data;
        # hence turn scroling off...
        if self.manager.xmax >= self.latestTime:
            self.manager.timeScrollingOn = True
        else:
            self.manager.timeScrollingOn = False
        
        if self.action == "previousZoomState" and self.wasTimeScrollingOn == True:
            self.manager.timeScrollingOn = True
            
            
        self.action = ""
        self.replot()        


    #----------------------------------------------------------------------------------    

    def wheelEvent (self, event):
        ''' This method controls mousewheel zooming.
        '''

        # if wheel hasn't been turned recently then save prior zoomState
        if self.alreadyWheeling == False:
            self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)
            self.zoomStack.append (self.zoomState)
            self.alreadyWheeling = True

        self.autoYScaleOn = False  

        # get wheel position in pixels
        self.xpix = event.pos ().x ()
        self.ypix = event.pos ().y ()

        # now convert position to REAL x,y (and correct the x-reading)
        self.xpixel_adjust = self.plotLayout().canvasRect().left()
        self.x = self.invTransform (Qwt.QwtPlot.xBottom, self.xpix
                                                         - self.xpixel_adjust)
        self.y = self.invTransform (Qwt.QwtPlot.yLeft, self.ypix)

        # use wheel input to create a zoom factor.
        # Note: event.delta() is 120 for one roll-click of the wheel.  If you roll 
        # fast, you might get 1000 or 1100 in one shot.  So we'll make the zoom 
        # factor close to unity (+/-) this way:
        zoomFactorX =  1.0 - min (1000., event.delta ()) / 2000.
        zoomFactorY =  zoomFactorX

        x_range = self.manager.xmax - self.manager.xmin
        y_range = self.ymax - self.ymin

        if self.x > self.manager.xmin:                
            newXrange = x_range * zoomFactorX
        else:
            newXrange = x_range
        
        if  self.y > self.ymin:
            newYrange = y_range * zoomFactorY
        else:
            newYrange = y_range            

        self.manager.xmin = self.x - newXrange * (self.x - self.manager.xmin) / x_range
        self.manager.xmax = self.x + newXrange * (self.manager.xmax - self.x) / x_range
        self.ymin = self.y - newYrange * (self.y - self.ymin) / y_range
        self.ymax = self.y + newYrange * (self.ymax - self.y) / y_range 

        self.setAxisScale (QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)
        self.setAxisScale (QwtPlot.yLeft, self.ymin, self.ymax)

        # if new window has "room" for new data, turn on scrolling.
        # otherwise we presume the user wants to focus on an earlier section of data;
        # hence turn scroling off...
        if self.manager.xmax >= self.latestTime:
            self.manager.timeScrollingOn = True
        else:
            self.manager.timeScrollingOn = False

        self.replot()


    # ---------------------------------------------------------------------------------

    def resetPlotAxes (self):
        ''' This method resets the plot axes and clears the zoom stack.
        The PolyDAQ Gui calls this when RUN is initiated or re-initiated.
        '''

        # leave time window the same, but shift back to zero        

        if self.manager.xmin >0 or self.manager.xmax <0:
            self.manager.xmax = self.manager.xmax - self.manager.xmin
            self.manager.xmin = 0
            self.setAxisScale(QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)

        self.manager.timeScrollingOn = True
#        self.autoYScaleOn = False

        self.zoomStack = []

        self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)
        self.zoomStack.append(self.zoomState)

        


        self.replot ()


    #----------------------------------------------------------------------------------

    def updatePlot (self, latestTime, time_per_point, NumberOfCurves, trackMinY, trackMaxY):
        ''' This method draws a plot from a set of data.
        '''

        # don't F with the plots if plot units are being changed! 
        if self.manager.unitsHaveChanged == True:
            return

        # if scrolling has been turned off, that means that the plot has been zoomed or panned to
        # an earlier section of the plot.  No need to update the plot!
        self.NumberOfCurves = NumberOfCurves
        

        # if no channels selected, don't bother
#        if self.NumberOfCurves == 0:
#            return

        self.trackMinY = trackMinY
        self.trackMaxY = trackMaxY

        self.latestTime = latestTime

#        self.syncTimeOn = syncTimeOn

 #       # if PolyDAQ wants to force scrolling OFF, then do it.  Ignore if True.
 #       if scrollOn == False:
 #           self.timeScrollingOn = False


#        # Synchronize time axes if Sync is on
#        if self.syncTimeOn == True:
#            self.manager.xmin = syncTimeMin
#            self.manager.xmax = syncTimeMax
#            self.setAxisScale (QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)

        # Original time window (or span, or width)
        timeWindow = self.manager.xmax - self.manager.xmin  
        
        # Scrolling Function.  If it's ON... and the latest time has passed 93% of the window
        # (the 93% gives a little space to the plot, so you can see the latest data being plotted)
        if (self.latestTime > self.manager.xmin+0.93*timeWindow) and (self.manager.timeScrollingOn) == True:
            
            
            # difference between max time axis limit and latest read time
            deltaTime = self.latestTime - self.manager.xmax  
            
            # calculate new limits
            self.manager.xmin += deltaTime + 0.07*timeWindow
            self.manager.xmax += deltaTime + 0.07*timeWindow

#            self.setAxisScale (QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)

        # Autoscale Y function
        # need at least two data points to establish a max AND min
        if self.autoYScaleOn == True:    # and len(time_data)>1:
            # Now adjust ymin and ymax and send it to PolyDAQ_Plot to reassign the axis.
            deltay = self.trackMaxY - self.trackMinY
            if deltay == 0:  # in case y doesn't change, make axis a +/- 5% of nominal
                self.ymin = self.trackMinY * (0.95)
                self.ymax = self.trackMaxY * (1.05)
            else:
                self.ymin = self.trackMinY - .05 * deltay  # adding 10% total to the yrange
                self.ymax = self.trackMaxY + .05 * deltay      

            self.setAxisScale (QwtPlot.yLeft, self.ymin, self.ymax)
            
        #regardless, always update time axis, since user may have changed it. 
        self.setAxisScale (QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)
        
 #       self.replot()

    #----------------------------------------------------------------------------------

    def updateCurve (self, curveNumber, time_per_point, time_data, oneChannelsData):
        ''' If there are data to be plotted, set up the plot curves to display it.
        Each curve's data will have time_data as the X data and one of the items in
        the list of measurements as the Y data. Only the last (points_per_plot) items
        will actually be plotted, so the graph scrolls along as new data are taken.
        '''

        # don't F with the plots if plot units are being changed! 
        if self.manager.unitsHaveChanged == True:
            return

        # the next line causes problems when the Gui/DAQ communication is too slow,
        # and the DAQ "skips" some times.  What happens is, if times get skipped,
        # the array count is lower than you'd expect.  Ex: if xmin = 10 and 
        # time/pt = 0.1, you'd expect 10 minutes of data contains 100 points.  But 
        # let's say, because of skipping, there are only 80 points.  This means that 
        # when you look at point #100, it's at later actual time.  
        #   timeArrayIndexMin = max(int(self.xmin/self.time_per_point), 0)

        # to fix this without having to attach the entire array, we'll estimate the
        # average rate of actual data saving by comparing len (time_data) to 
        # latestTime, and then back-calculate the minIndex value.  Genious!
        
        
        
        estAvgTimePerPoint = float(self.latestTime) / float (len (time_data)) * 1.1
        
            # I added 10% to be safe
        # Note: self.latestTime was updated during plotUpdate!

        timeArrayIndexMin = max (int (self.manager.xmin / estAvgTimePerPoint), 0)
        timeArrayIndexMax = min (int (self.manager.xmax / time_per_point + 2), len (time_data))


        # I added '+2' because the curves didn't quite make it to the end
        # of the plot.

        # Just to make sure there ARE data to plot. Probably unneccesary (??!)
        if (time_data != []):
            self.curves[curveNumber].setData \
                (time_data[timeArrayIndexMin: timeArrayIndexMax], \
                    oneChannelsData[timeArrayIndexMin: timeArrayIndexMax])

#        self.replot ()


    #----------------------------------------------------------------------------------

    def reattachAllData (self, curveNumber, time_data, oneChannelsData):
        ''' This method reattaches the entire array of data to the plots.  Otherwise
        the only viewable data when data collection is stopped will be limited to the 
        time range of the most recent time window.  Thus, this method allows the user
        to navigate the entire set of data when collection is over.
        '''

        if (time_data != []):  # just in case there are no data... not likely.
            self.curves[curveNumber].setData (time_data[0: len(time_data)], \
                         oneChannelsData[0: len(time_data)])
        


    #----------------------------------------------------------------------------------

    def zoomAll_y (self):

        if self.NumberOfCurves == 0: return



        if self.latestTime == 0:                    # If no data yet, can't zoom all y!
            return

        # save prior zoom state        
        self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)
        self.zoomStack.append (self.zoomState)

        self.autoYScaleOn = False

        # Now adjust ymin and ymax and send it to PolyDAQ_Plot to reassign the axis.
        deltay = self.trackMaxY - self.trackMinY
        
        if deltay == 0:  # in case y doesn't change, make axis a +/- 10% of nominal
            self.ymin = self.trackMinY * (0.95)
            self.ymax = self.trackMaxY * (1.05)
        else:
            self.ymin = self.trackMinY - .1 * deltay  # adding 20% total to the yrange
            self.ymax = self.trackMaxY + .1 * deltay 

        # now reset y-axis and replot:
        self.setAxisScale (QwtPlot.yLeft, self.ymin, self.ymax)
        self.replot()


    #----------------------------------------------------------------------------------

    def autoYScale (self):

#        if self.NumberOfCurves == 0:
#            return

        # save previous zoom state (before you turned autoscale on)
        self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)
        self.zoomStack.append (self.zoomState)

        if self.autoYScaleOn == True:
            self.autoYScaleOn = False
        else:
            self.autoYScaleOn = True


    #----------------------------------------------------------------------------------

    def zoomAll_time (self):

        if self.NumberOfCurves == 0:
            return

        if self.latestTime == 0:
            return       

        # save prior zoom state
        self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)   
        self.zoomStack.append(self.zoomState) 

        #now reset entire time range
        self.manager.xmin = 0  # time should always start at zero!  
        self.manager.xmax = self.latestTime*1.1  # added 20% to the time        
        
        # now reset time axis and replot:

        self.setAxisScale (QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)

        self.manager.timeScrollingOn = True

        self.replot()

    #----------------------------------------------------------------------------------

    def resumeTimeScrolling (self):

        if self.NumberOfCurves == 0:
            return

        if self.latestTime == 0:
            return        
 
        if self.manager.timeScrollingOn == True:
            return

        # don't F with the plots if plot units are being changed! 
        if self.manager.unitsHaveChanged == True:
            return
 
        # save prior zoom state
        self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)   
        self.zoomStack.append(self.zoomState) 
        
        self.manager.timeScrollingOn = True
        
        #now reset time limits
        x_range = self.manager.xmax - self.manager.xmin
        self.manager.xmax = self.latestTime + x_range*0.1  # shifted time window over by 20%
        self.manager.xmin = self.manager.xmax - x_range
        
        # now reset time axis and replot:

        self.setAxisScale (QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)
        
        self.replot()
        
            

    #----------------------------------------------------------------------------------

    def toggleVisibility (self, curveClickedNum):
        """Toggle the visibility of a plot item
        """

        self.curves[curveClickedNum].setVisible(not self.curves[curveClickedNum].isVisible())
            
        self.replot()


    #----------------------------------------------------------------------------------

    def newYAxisLimits (self):

 #       if self.NumberOfCurves == 0: return
        

        self.newYAxisWindow = QDialog(self)

        layout = QFormLayout()

        self.enterNewYMin = QLineEdit(str('%.3f' % self.ymin))
        self.enterNewYMax = QLineEdit(str('%.3f' % self.ymax))
        layout.addRow(QLabel('Enter new y range:'))
        layout.addRow(QLabel('Minimum:'), self.enterNewYMin)
        layout.addRow(QLabel('Maximum:'), self.enterNewYMax)
        self.status = QLabel('')
        layout.addRow(self.status)
        
        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")
        okButton.clicked.connect(self.setNewY)
        cancelButton.clicked.connect(self.cancelClicked)

        hbox = QHBoxLayout()
        hbox.addStretch(1)        
        hbox.addWidget(okButton)
        hbox.addWidget(cancelButton)

        vbox = QVBoxLayout()
        vbox.addLayout(layout)
        vbox.addLayout(hbox)
        vbox.addStretch(1)
        
        self.newYAxisWindow.setLayout(vbox)
    #        newYAxisWindow.setGeometry(300, 300, 300, 150)
        self.newYAxisWindow.setWindowTitle('y-axis settings')
        self.newYAxisWindow.setWindowIcon(QIcon('polydaq_icon.png'))

        self.newYAxisWindow.show()


    #----------------------------------------------------------------------------------

    def setNewY (self):

        # Error messages
        if (self.enterNewYMin.text () == '' or self.enterNewYMax.text () == ''):
            self.status.setText ('ERROR: Empty/non-numeric values are not allowed!')

        elif float(self.enterNewYMin.text()) == float(self.enterNewYMax.text()):
            self.status.setText ('ERROR: both limits cannot be the same!')

        elif float(self.enterNewYMin.text()) > float(self.enterNewYMax.text()):
            self.status.setText ('ERROR: The minimum cannot exceed the maximum!')

        else:
            # save prior zoom state
            self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)   
            self.zoomStack.append (self.zoomState)
            

            self.ymin = float (self.enterNewYMin.text())
            self.ymax = float (self.enterNewYMax.text())

            self.setAxisScale (QwtPlot.yLeft, self.ymin, self.ymax)

            self.autoYScaleOn = False

            self.replot ()
            self.newYAxisWindow.close ()


    #----------------------------------------------------------------------------------

    def cancelClicked (self):
        self.newYAxisWindow.close ()


    #----------------------------------------------------------------------------------

    def newTimeAxisLimits (self):

#        if self.NumberOfCurves == 0:
#            return

        self.newAxisWindow = QDialog (self)

        layout = QFormLayout ()

        self.enterNewMin = QLineEdit (str ('%.1f' % self.manager.xmin))
        self.enterNewMax = QLineEdit (str ('%.1f' % self.manager.xmax))
        layout.addRow (QLabel ('Enter new t range:'))
        layout.addRow (QLabel ('Minimum:'), self.enterNewMin)
        layout.addRow (QLabel ('Maximum:'), self.enterNewMax)
        self.status = QLabel ('')
        layout.addRow (self.status)

        okButton = QPushButton ("OK")
        cancelButton = QPushButton ("Cancel")
        okButton.clicked.connect (self.setNewT)
        cancelButton.clicked.connect (self.cancelTClicked)

        hbox = QHBoxLayout ()
        hbox.addStretch (1)        
        hbox.addWidget (okButton)
        hbox.addWidget (cancelButton)

        vbox = QVBoxLayout()
        vbox.addLayout(layout)
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        self.newAxisWindow.setLayout (vbox)
        self.newAxisWindow.setWindowTitle ('time axis settings')
        self.newAxisWindow.setWindowIcon (QIcon ('polydaq_icon.png'))

        self.newAxisWindow.show ()


    #----------------------------------------------------------------------------------

    def setNewT (self):

        # Error messages
        if (self.enterNewMin.text() == '' or self.enterNewMax.text() == ''):
            self.status.setText('ERROR: Empty/non-numeric values are not allowed!')

        elif float(self.enterNewMin.text()) == float(self.enterNewMax.text()):
            self.status.setText('ERROR: both limits cannot be the same!')

        elif float(self.enterNewMin.text()) > float(self.enterNewMax.text()):
            self.status.setText('ERROR: The minimum cannot exceed the maximum!')

        else:
            # save previous zoom state
            self.zoomState = (self.manager.xmin, self.manager.xmax, self.ymin, self.ymax, self.manager.timeScrollingOn, self.autoYScaleOn)   # calculate new zoom state
            self.zoomStack.append(self.zoomState)

            self.manager.xmin = float(self.enterNewMin.text())
            self.manager.xmax = float(self.enterNewMax.text())

            self.setAxisScale (QwtPlot.xBottom, self.manager.xmin, self.manager.xmax)
            
            if self.manager.xmax >= self.latestTime:
                self.manager.timeScrollingOn = True
            else:
                self.manager.timeScrollingOn = False

            self.replot()
            self.newAxisWindow.close()


    #----------------------------------------------------------------------------------

    def cancelTClicked (self):

        self.newAxisWindow.close()


    #----------------------------------------------------------------------------------

    def change_units_to_seconds (self):
        
        self.manager.timeConversionFactor = 1.
        self.manager.units_string ='s'
        self.manager.unitsHaveChanged = True     

    #----------------------------------------------------------------------------------

    def change_units_to_minutes (self):

        self.manager.timeConversionFactor = 1./60.
        self.manager.units_string ='min'
        self.manager.unitsHaveChanged = True

    #----------------------------------------------------------------------------------

    def change_units_to_hours (self):

        self.manager.timeConversionFactor = 1./3600.
        self.manager.units_string ='h'
        self.manager.unitsHaveChanged = True        

    #----------------------------------------------------------------------------------

    def change_units_to_days (self):

        self.manager.timeConversionFactor = 1./24./3600.
        self.manager.units_string ='d'
        self.manager.unitsHaveChanged = True        


    #----------------------------------------------------------------------------------


    def change_units_to_fortnights (self):

        self.manager.timeConversionFactor = 1./24./3600/14.
        self.manager.units_string ='fortnights'
        self.manager.unitsHaveChanged = True        


    #----------------------------------------------------------------------------------

#    def syncTimeAxes (self):
#        
#        if self.NumberOfCurves == 0: return
#        
#        if self.syncTimeOn == False:
#            self.syncTimeOn = True
#
#        else:
#            self.syncTimeOn = False


    #----------------------------------------------------------------------------------

#    def isTimeSyncOn (self):
#
#        return self.syncTimeOn, self.timeScrollingOn, self.manager.xmin, self.manager.xmax


    #----------------------------------------------------------------------------------

    def curveProps (self, curveNumClicked):

        self.curveNumClicked = curveNumClicked

        # initialize a few variables
        self.newCurveColor = self.ch_pen_colors[self.curveNumClicked] 
        self.newLineStyle = self.ch_line_styles[self.curveNumClicked]
        self.newSymbolStyle = self.ch_symbol_styles[self.curveNumClicked]
        self.newSymbolBrushColor = self.ch_pen_colors[self.curveNumClicked]
        self.newSymbolPenColor = self.ch_pen_colors[self.curveNumClicked]
        self.newSymbolSize = self.ch_symbol_sizes[self.curveNumClicked]

        self.curvePropsWindow = QDialog (self)

        # Name of curve to configure
        curveName_label = QLabel ('Curve: ' + self.ch_names[self.curveNumClicked])

        # Change line parameters
        settings_group = QGroupBox (curveName_label)
        settings_layout = QGridLayout ()

        # Symbol style
        symbolStyle_label = QLabel ('Marker Shape')
        self.symbolStyle_box = QComboBox ()
        self.symbolStyle_box.insertItem (1, 'none')      # QwtSymbol.NoSymbol
        self.symbolStyle_box.insertItem (2, 'circle')    # QwtSymbol.Ellipse
        self.symbolStyle_box.insertItem (3, 'square')    # QwtSymbol.Rect
        self.symbolStyle_box.insertItem (4, 'diamond')   # QwtSymbol.Diamond
        self.symbolStyle_box.setCurrentIndex \
                                    (self.ch_symbol_styles[self.curveNumClicked] + 1)
        self.symbolStyle_box.currentIndexChanged.connect (self.setNewSymbolStyle) 

        settings_layout.addWidget (symbolStyle_label,    0, 0)
        settings_layout.addWidget (self.symbolStyle_box, 0, 1)

        # symbol size (width and height will be equal)
        symbolSize_label = QLabel ('Marker Size')
        self.newSymbolSize = QLineEdit ()
        self.newSymbolSize.setText (str (self.ch_symbol_sizes[self.curveNumClicked]))
        settings_layout.addWidget (symbolSize_label,     1, 0)
        settings_layout.addWidget (self.newSymbolSize,   1, 1)

        # line style
        lineStyle_label = QLabel ('Style')
        self.lineStyle_box  = QComboBox ()
        self.lineStyle_box.addItem ('no line')           # Qt.NoPen        
        self.lineStyle_box.addItem ('solid')             # Qt.SolidLine
        self.lineStyle_box.addItem ('dash')              # Qt.DashLine
        self.lineStyle_box.addItem ('dot')               # Qt.DotLine
        self.lineStyle_box.addItem ('dashdot')           # Qt.DashDotLine
        self.lineStyle_box.setCurrentIndex \
                                        (self.ch_line_styles[self.curveNumClicked])
        self.lineStyle_box.currentIndexChanged.connect (self.setNewLineStyle)
        settings_layout.addWidget (lineStyle_label,      2, 0)
        settings_layout.addWidget (self.lineStyle_box,   2, 1)

        # color
        color_label = QLabel ('Color')
        self.color_btn = QPushButton ()         # unichr(9608) is a solid square symbol
        self.color_btn.setAutoDefault(False)

        # Make button the current series color
        self.color_btn.setStyleSheet ('background-color: ' 
                        + QColor (self.ch_pen_colors[self.curveNumClicked]).name ())
        self.color_btn.clicked.connect (functools.partial (self.showColorDialog, QColor(self.ch_pen_colors[self.curveNumClicked])))
        settings_layout.addWidget (color_label,          3, 0)
        settings_layout.addWidget (self.color_btn,       3, 1)

        # Line width
        width_label = QLabel ('Line Width')
        self.newWidth = QLineEdit ()
        self.newWidth.setText (str (self.ch_line_widths[self.curveNumClicked]))

        settings_layout.addWidget (width_label,         4, 0)
        settings_layout.addWidget (self.newWidth,       4, 1)

        settings_group.setLayout (settings_layout)        

        #-------------------------------------------------------------
        # add OK/Cancel buttons:
        okButton = QPushButton ("OK")
        cancelButton = QPushButton ("Cancel")
        okButton.clicked.connect (self.setCurveProps)
        cancelButton.clicked.connect (self.cancelCurveClicked)
        
        hbox = QHBoxLayout ()
        hbox.addStretch (1)
        
        hbox.addWidget (okButton)
        hbox.addWidget (cancelButton)
        
        vbox = QVBoxLayout ()
        vbox.addWidget (curveName_label)
        vbox.addWidget (settings_group)

        self.status_label = QLabel('')
        vbox.addWidget (self.status_label)
        vbox.addStretch (1)
        
        vbox.addLayout (hbox)
        
        self.curvePropsWindow.setLayout (vbox)

        self.curvePropsWindow.setWindowTitle ('Curve Properties')
        self.curvePropsWindow.setWindowIcon (QIcon ('polydaq_icon.png'))

        self.curvePropsWindow.show ()


    #----------------------------------------------------------------------------------

    def setNewLineStyle (self):

        self.newLineStyle = self.lineStyle_box.currentIndex()


    #----------------------------------------------------------------------------------

    def showColorDialog (self, currentColor):

        self.newCurveColor = QColorDialog.getColor (currentColor)
        

        if self.newCurveColor.isValid ():
            self.color_btn.setStyleSheet ('QWidget {background-color: %s }' \
                                                        % self.newCurveColor.name())
        else:
            self.newCurveColor = currentColor


    #----------------------------------------------------------------------------------

    def setNewSymbolStyle (self):
        if self.symbolStyle_box.currentIndex() == 0:
            self.newSymbolStyle = QwtSymbol.NoSymbol

        if self.symbolStyle_box.currentIndex() == 1:
            self.newSymbolStyle = QwtSymbol.Ellipse

        if self.symbolStyle_box.currentIndex() == 2:
            self.newSymbolStyle = QwtSymbol.Rect

        if self.symbolStyle_box.currentIndex() == 3: 
            self.newSymbolStyle = QwtSymbol.Diamond


    #----------------------------------------------------------------------------------

    def setCurveProps (self):
        
        # Error messages
        if float (self.newWidth.text ()) < 0  or float (self.newWidth.text ()) > 10:
            self.status_label.setText ('ERROR: Choose a width between 0. and 10.')

        elif float (self.newSymbolSize.text ()) < 0  \
                    or float(self.newSymbolSize.text ()) > 20:
            self.status_label.setText ('ERROR: Choose a size between 0. and 20.')

        else:
            self.ch_pen_colors[self.curveNumClicked] = self.newCurveColor
            self.ch_line_widths[self.curveNumClicked] = float (self.newWidth.text ())
            self.ch_line_styles[self.curveNumClicked] = self.newLineStyle
            
            self.ch_symbol_styles[self.curveNumClicked] = self.newSymbolStyle
            #self.ch_symbol_pens[self.curveNumClicked] = self.newSymbolPenColor
            #self.ch_symbol_brushes[self.curveNumClicked] = self.newSymbolBrushColor
            self.ch_symbol_sizes[self.curveNumClicked] \
                                                    = int (self.newSymbolSize.text ())

            self.curves[self.curveNumClicked].setPen (QPen 
                                         (self.ch_pen_colors[self.curveNumClicked],
                                          self.ch_line_widths[self.curveNumClicked],
                                          self.ch_line_styles[self.curveNumClicked]))

            self.curves[self.curveNumClicked].setSymbol (QwtSymbol
                                (self.ch_symbol_styles[self.curveNumClicked],
                                QBrush (self.ch_pen_colors[self.curveNumClicked]),
                                QPen (self.ch_pen_colors[self.curveNumClicked]),
                                QSize (self.ch_symbol_sizes[self.curveNumClicked],
                                self.ch_symbol_sizes[self.curveNumClicked])))

            self.replot ()
            self.curvePropsWindow.close ()


    #----------------------------------------------------------------------------------

    def cancelCurveClicked (self):

        self.curvePropsWindow.close ()


#======================================================================================

if __name__ == '__main__':
    a = QApplication (sys.argv)
    p1 = testPlot ()
    a.exec_ ()

