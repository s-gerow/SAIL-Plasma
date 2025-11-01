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
# rm = pyvisa.ResourceManager()
# DMM = rm.open_resource('USB0::0x05E6::0x6500::04386498::INSTR')

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
 
# def run():
#     #run_bool=True
#     with nidaqmx.Task() as do_task:
#         Pull = do_task._do_channels.add_do_chan("NI_DAQ/port1/line2")
#         Dir = do_task._do_channels.add_do_chan("NI_DAQ/port1/line3") #false = up, true =down
#         #while run_bool:
#         #do_task.write([True,True],auto_start=True,timeout=10) 
#         #sleep(0.5)
#         #do_task.write([True,False],auto_start=True,timeout=3)
#         # sleep(0.000005)
#         # for x in range(400):
#         #     do_task.write([False,True],auto_start=True,timeout=10)
#         #     sleep(.000005)
#         #     do_task.write([True,True],auto_start=True,timeout=10)
#         #     sleep(0.000005)
#         do_task.write([True,True],auto_start=True,timeout=10)
#         sleep(0.5)
#         do_task.write([True,False],auto_start=True,timeout=10) 
#         sleep(0.5)
#         #do_task.write([True,False],auto_start=True,timeout=3)
#         sleep(0.000005)
#         for x in range(400):
#             do_task.write([False,False],auto_start=True,timeout=10)
#             sleep(.000005)
#             do_task.write([True,False],auto_start=True,timeout=10)
#             sleep(0.000005)
#         do_task.write([False,False])

def move(dir_state, steps, delay=0.000005):
    with nidaqmx.Task() as do_task:
        Pull = do_task._do_channels.add_do_chan("NI_DAQ/port1/line2")
        Dir = do_task._do_channels.add_do_chan("NI_DAQ/port1/line1") #false = up, true =down
        # Set direction (second bit)
        do_task.write([False, dir_state])
        time.sleep(0.00005)  # allow DIR to settle before stepping

        # Pulse step pin (first bit)
        for _ in range(steps):
            do_task.write([True, dir_state])   # rising edge on STEP
            time.sleep(delay)
            do_task.write([False, dir_state])  # falling edge
            time.sleep(delay)

# Move down
move(True, 400)
time.sleep(0.5)

# Move up
move(False, 400)            



