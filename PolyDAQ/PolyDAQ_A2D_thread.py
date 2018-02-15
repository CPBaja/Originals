#**************************************************************************************
# File: PolyDAQ_A2D_thread.py
#   This class implements a thread in which data is periodically measured. 
#
#
#**************************************************************************************

import time
import serial
import threading
import new_config as config


#======================================================================================

class data_acq_thread (threading.Thread):
    ''' Class which runs a thread that acquires data from the PolyDAQ.

    This class runs a thread, one which carries out the data acquisition by asking 
    the PolyDAQ board for readings at the correct times. The thread is helpful 
    because it allows data acquisition while the main (GUI) thread is doing 
    whatever it needs to be doing at the time, even things such as saving data to 
    a file, which causes the main thread to get stuck for a while. 
    '''

    def __init__ (self, run_interval):

        threading.Thread.__init__ (self, name = "DataAcqThread")

        # Create arrays to store data and a lock to prevent their corruption
        self.data_lock = threading.Lock ()
        self.time_array = []
        self.data_array = [[]]

        # Save the starting value of the time interval between data points
        self.run_interval = run_interval

        # Start up in the not-running state (not saving data)
        self.running = False

        # Create the serial port object; it hasn't been set up yet
        self.serial_port = None

        # Set an empty list of things to measure; when someone calls the method
        # set_measurands(), this list will be filled or updated
        self.measurands = []

        # Record the starting time, and set it as the most recent and next run times
        self.start_time = time.time ()
        self.next_run_time = self.start_time
        self.last_run_time = self.start_time

        # Create a lock for the serial port. This lock will be used to prevent calls
        # to functions in this class from other threads from trying to use the serial
        # port while the functions which run in this thread are already using it
        self.serial_lock = threading.Lock ()




    #----------------------------------------------------------------------------------

    def run (self):
        ''' This is the run method for this thread; it runs "simultaneously" with 
            whatever is running in other threads in the program. This thread takes
            data periodically.
            '''

        while (True):
            # Check if it's time to take data yet; if so, do it and update the timer
            now_time = time.time ()
            if (now_time >= self.next_run_time):
                self.next_run_time += self.run_interval

                # If we're in data taking mode, take data and put it in the array; 
                # if not, go to sleep for a while to save processor cycles
                if (self.running and (self.serial_port != None)):
                    # Grab serial port lock so nobody else can butt in on our port use
                    self.serial_lock.acquire ()

                    # Grab the global data lock so other threads can't mess with the
                    # data arrays while this thread is writing to them
                    self.data_lock.acquire ()

                    try:
                        self.time_array += [(now_time - self.start_time)]

                        # For each item in the list of measurands, send the item as a
                        # command to the PolyDAQ and get a string of data back
                        for index, item in enumerate (self.measurands):


                            # original data collection:
                            self.serial_port.timeout = 0.20
                            self.serial_port.flushInput()                # clear the buffer, or else channels get confused!
                            self.serial_port.write (item)                # send the board the channel name
                            response_string = self.serial_port.readline ()  # read its value
                            #print ('response string, channel ', item[1], '= ', response_string)        #### JRR
                            self.serial_port.timeout = 0

                            # We should get a string containing an integer; find the
                            # integer in the string. It is an A/D reading
                            try:
                                a2d_reading = int (response_string)
#                                self.data_array[index] += [float(a2d_reading)*self.slopes[index]
 #                                                  + self.offsets[index]]
                                self.data_array[index] += [config.calibrationEquation(a2d_reading,item)]

                            except ValueError:
                                a2d_reading = -99

                                self.data_array[index] += -999e9

                    # No matter how the outer try block came out, we will get here
                    finally:
                        self.data_lock.release ()
                        self.serial_lock.release ()

            # Sleep until the next time this task is supposed to run
            time.sleep (self.run_interval / 20.0)


    #----------------------------------------------------------------------------------

    def set_serial_port (self, port_name, baud_rate):
        ''' This method is used to set the serial port to which we're connecting.  It 
            opens (or attempts to open) the port; if successful, the port's ready; if 
            not, an error indication is given.  If the port is successfully opened, 
            the other buttons will be activated. 
            '''

        try:
            # Grab the serial port lock so nobody else can butt in on our port use
            self.serial_lock.acquire ()
                        
            # Port mode is 8 data bits, 1 stop bit, no parity, timeout = 0.  The zero
            # timeout means return immediately from a read rather than waiting
            self.serial_port = serial.Serial (port_name, baud_rate, serial.EIGHTBITS, 
                serial.PARITY_NONE, serial.STOPBITS_ONE, 0)
            self.serial_lock.release ()

        # If there was a problem opening the port, complain
        except serial.SerialException:
            self.serial_port = None
            return ([("Cannot open port " + port_name), False])

        # A value error means the serial port parameter was just plain wacked out
        except ValueError:
            self.serial_port = None
            return ([("Serial port parameter out of range"), False])

        # No exception; greet the PolyDAQ and set it up. Use a timeout for getting a 
        # response to the "v" command.  Tell it to oversample!
        else:
            self.serial_lock.acquire ()
            self.serial_port.timeout = 0.5
            self.serial_port.write ("v")
            init_response = self.serial_port.read (32)
            self.serial_port.timeout = 0
            self.serial_port.write ("O" + str(config.oversampling) + "\n")
            self.serial_lock.release ()

            # If PolyDAQ doesn't respond, complain; otherwise we're ready to go
            if init_response == '':
                return ([("<b>ERROR:</b> No response from PolyDAQ \nStart again by clicking CHOOSE PORT."), False])
                self.serial_port = None

            # If we got this far, we can return a response string
            return (["Connected to " + init_response, True])


    #----------------------------------------------------------------------------------

    def set_measurands (self, measurands): #, slopes, offsets):
        ''' This method saves a list of things which are going to be measured. The list
            holds one-character commands; each command will query the PolyDAQ so that
            it sends one item of data. For example, the command '0' will cause the 
            PolyDAQ to send back one A/D reading from channel 0. 
            '''

        self.measurands = measurands
#        self.slopes = slopes
#        self.offsets = offsets
        

    #----------------------------------------------------------------------------------

    def set_interval (self, new_time_interval):
        ''' This method sets the time interval between data points.
            '''

        self.run_interval = new_time_interval

    #----------------------------------------------------------------------------------

    def start_taking_data (self):
        ''' This method sets a flag so that the data acquisition thread will take data.
            It also records the time at the beginning of the run so that the time at 
            which each data point is recorded can be computed.
            '''

        # Set up the timing variables which control when data is to be taken
        self.start_time = time.time ()
        self.next_run_time = self.start_time
        self.last_run_time = self.start_time

        # Lock the data arrays, then initialize the data arrays. The main data array
        # must be a list of empty lists; the number of lists is the number of data
        # items to acquire each time data is acquired
        self.data_lock.acquire ()
        self.time_array = []
        self.data_array = []
        for item in enumerate (self.measurands):
            self.data_array += [[]]
        self.data_lock.release ()
        self.running = True


    #----------------------------------------------------------------------------------

    def stop_taking_data (self):
        ''' This method sets a flag so that the data acquisition thread will stop 
            taking data.
            '''

        self.running = False


    #----------------------------------------------------------------------------------

    def balance_bridge (self, command_string):
        ''' This function will only be called for a PolyDAQ 2 with its D/A converter
            based strain gauge bridge balancers. It asks the PolyDAQ 2 to run an 
            auto-balance on one bridge and returns the string which the PolyDAQ sent 
            over the serial port.
            '''

        # Grab serial port lock so nobody else can butt in on our port use, then 
        # send the "L" and "M" commands to attempt auto-balance of each bridge
        self.serial_lock.acquire ()
        self.serial_port.timeout = 0.20

        self.serial_port.write (command_string);

        while True:
        
            response_string = self.serial_port.readline ()
            if "balance" in response_string:
                break

        self.serial_port.timeout = 0
        self.serial_lock.release ()

        return response_string


    #----------------------------------------------------------------------------------

    def reset_avr (self):
        ''' This method is called by the main GUI thread when its reset AVR button is 
            pressed. It writes an "R" to the serial port, asking the AVR to reset 
            itself.  Reset functionality is currently NOT implemented on the PolyDAQ 2.
            ''' 

        self.serial_lock.acquire ()
        self.serial_port.write ("R")
        self.serial_lock.release ()

