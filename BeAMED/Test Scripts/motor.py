import tkinter as tk
from tkinter import ttk
from tkinter import *
import pyvisa
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import time
from threading import Thread, Event
import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
import numpy as np
from time import sleep

#Matplotlib Config
matplotlib.use('TkAgg')

#https://www.geeksforgeeks.org/on-off-toggle-button-switch-in-tkinter/

#Initialize Visa Resource Manager
rm = pyvisa.ResourceManager()
DMM = rm.open_resource('USB0::0x05E6::0x6500::04386498::INSTR')

root = tk.Tk()
root.title = ('On/Off Switch')
root.geometry = ("500x300")

is_on = False #Keep track of the on/off state of button

# Create Label
my_label = Label(root, 
    text = "The Switch Is On!", 
    fg = "green", 
    font = ("Helvetica", 32))

my_label.pack(pady = 20)
 
# Define our switch function
def switch():
    global is_on
     
    # Determine is on or off
    if is_on:
        on_button.config(image = off)
        my_label.config(text = "The Switch is Off", 
                        fg = "grey")
        is_on = False
    else:
       
        on_button.config(image = on)
        my_label.config(text = "The Switch is On", fg = "green")
        is_on = True
 
# Define Our Images
on = PhotoImage(file = "./BeAMED/on.png")
off = PhotoImage(file = "./BeAMED/off.png")
 
# Create A Button
on_button = Button(root, image = on, bd = 0,
                   command = switch)
on_button.pack(pady = 50)
 
def run():
    run_bool = True
    
    DMM.write(':SENS:FUNC "CONT"')
    DMM.write('TRAC:FILL:MODE CONT,"defbuffer1"') #continuous fill
    with nidaqmx.Task() as do_task:
        Pull = do_task._do_channels.add_do_chan("NI_DAQ/port1/line2")
        Dir = do_task._do_channels.add_do_chan("NI_DAQ/port1/line3")

        while run_bool:
            ohm = float(DMM.query(":READ?"))
            if ohm < 500: #Move down
                DMM.close()
                rm.close()
                break
                '''
                do_task.write([False,True],auto_start=True,timeout=10) 
                sleep(0.5)
                for x in range(1600):
                    do_task.write([True,True],auto_start=True,timeout=10)
                    sleep(.0000025)
                    do_task.write([False,True],auto_start=True,timeout=10)
                    sleep(0.0000025)
                    print("Direction CW")
                    
                sleep(1)
                '''
            else:       #Move down
                
                #do_task.write([True,False],auto_start=True,timeout=10) 
                sleep(0.5)
                for x in range(3200):
                    do_task.write([True,False],auto_start=True,timeout=10)
                    sleep(.0000025)
                    do_task.write([False,False],auto_start=True,timeout=10)
                    sleep(0.0000025)
                    print("Direction Down")
                    ohm = float(DMM.query(":READ?"))
                    if ohm < 500: #Move up
                        sleep(0.5)
                        for x in range(400):
                            do_task.write([True,False],auto_start=True,timeout=10)
                            sleep(.0000025)
                            do_task.write([False,False],auto_start=True,timeout=10)
                            sleep(0.0000025)
                            print("Direction Up")
                        DMM.close()
                        rm.close()
                        break


def clean_exit():
    #runthread.stop()
    DMM.close()
    rm.close()  
    root.destroy()

root.protocol('WM_DELETE_WINDOW', clean_exit) 


runthread = Thread(target = run, daemon=True)         
# Execute Tkinter
runthread.start()
root.mainloop()