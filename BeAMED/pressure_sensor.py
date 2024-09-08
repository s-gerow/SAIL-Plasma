import tkinter as tk
from tkinter import ttk
import pyvisa
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from pylablib.devices import NI
import time
from threading import Thread, Event
import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
import numpy as np

#Matplotlib Config
matplotlib.use('TkAgg')

#Initialize Visa Resource Manager
rm = pyvisa.ResourceManager()

#daq ai0 = pressure
#ao0 = valve 5v

root = tk.Tk()

pressure = tk.IntVar()
target_min_pressure = tk.IntVar()
target_exp_pressure = tk.IntVar()

pressure_label = tk.Label(text="Pressure").pack(anchor='w')
pressure_box = tk.Spinbox(textvariable=pressure,
                          from_=0,
                          to=1000,)
pressure_box.pack(anchor='e')
target_min_label = tk.Label(text="Target Minimum Pressure").pack(anchor='w')
target_min_pressure_box = tk.Spinbox(textvariable=target_min_pressure,
                          from_=0,
                          to=1000,)
target_min_pressure_box.pack(anchor='e')
target_exp_label = tk.Label(text="Target Experiment Pressure").pack(anchor="w")
target_exp_pressure_box = tk.Spinbox(textvariable=target_exp_pressure,
                          from_=0,
                          to=1000,)
target_exp_pressure_box.pack(anchor='e')



def run():
    target_min_pressure.set(100)
    target_exp_pressure.set(700)
    global run_bool 
    run_bool = True

    gas = "gas"
    state = 0
    with nidaqmx.Task() as task:
        #ai_channel = task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=1, max_val=8, terminal_config=TerminalConfiguration.RSE)
        '''
        task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
        
        pressure_sensor_voltage = np.array(task.read(100))
        unfiltered_avg = np.median(pressure_sensor_voltage)
        true_pressure = 10**(unfiltered_avg - 5)
        print(true_pressure)
        '''
        ao_channel0 = task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao0", min_val=0,max_val=5)
        ao_channel1 = task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao1", min_val=0, max_val=5)
        #task.write(5,auto_start=True, timeout=10)
        #time.sleep(2)

        #task.stop()
        print('pressure start')
        pressure_thread.start()
        time.sleep(1)
        print('while bool start')
        if gas != "air":
            while run_bool:
                match state:
                    case 0:
                        print("case 0")
                        if pressure.get() > target_min_pressure.get():
                            task.write([[0],[0]],auto_start=True, timeout=10)
                        else:
                            state = 1
                    case 1:
                        print("case 1")
                        if pressure.get() < target_exp_pressure.get():
                            task.write([[5],[3]],auto_start=True, timeout=10)
                        else:
                            task.write([[0],[0]],auto_start=True, timeout=10)
                            state = 2
                    case 2:
                        print("case 2")
                        print("begin dischage")
                        time.sleep(2)
                        case = 0
                        run_bool = False
                        break


def read_pressure():
    with nidaqmx.Task() as read:
        ai_channel = read.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=1, max_val=8, terminal_config=TerminalConfiguration.RSE)
        read.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
        
        while run_bool:
            pressure_sensor_voltage = np.array(read.read(100))
            unfiltered_avg = np.median(pressure_sensor_voltage)
            true_pressure = 10**(unfiltered_avg - 5)
            root.after(1, lambda: pressure.set(true_pressure))


def clean_exit():
    rm.close()
    root.destroy()

root.protocol('WM_DELETE_WINDOW', clean_exit) 

pressure_thread = Thread(target=read_pressure, daemon=True)
print("run init")
run_experiment = Thread(target=run, daemon=True)
print("run start")
run_experiment.start()
root.mainloop()

                         



'''
#Create GUI Window
root = tk.Tk()

def clean_exit():
    print("cleaning up...")
    stop_all_event.set()
    print("threads stopped")
    daq.stop()
    daq.close()
    print("daq closed")
    print("quitting")
    root.destroy()

root.protocol('WM_DELETE_WINDOW', clean_exit)  # root is your root window

stop_all_event = Event()
def read_pressure(event: stop_all_event):
    daq.start()
    nsamples = 0
    while nsamples<100:
        pressure_sensor_voltage = daq.read()[0][0]
        true_pressure = 10**(pressure_sensor_voltage-5)
        pressure_var.set(true_pressure)
        #print(pressure_var.get())
        nsamples+=0
        if event.is_set():
            print("event flag set: stopping...")
            print("Stopped Reading Pressure. Last Reading: {}",true_pressure)
            break

'''
