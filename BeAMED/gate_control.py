import tkinter as tk
from tkinter import ttk
import pyvisa
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
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

pressure_box = tk.Spinbox(textvariable=pressure,
                          from_=0,
                          to=10,)
pressure_box.pack()
target_min_pressure_box = tk.Spinbox(textvariable=target_min_pressure,
                          from_=0,
                          to=10,)
target_min_pressure_box.pack()
target_exp_pressure_box = tk.Spinbox(textvariable=target_exp_pressure,
                          from_=0,
                          to=10,)
target_exp_pressure_box.pack()



def run():
    pressure.set(10)
    target_min_pressure.set(1)
    target_exp_pressure.set(5)
    run_bool = True

    gas = "gas"
    state = 0
    with nidaqmx.Task() as ao_task, nidaqmx.Task() as do_task:
        #ai_channel = task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=1, max_val=8, terminal_config=TerminalConfiguration.RSE)
        '''
        task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
        
        pressure_sensor_voltage = np.array(task.read(100))
        unfiltered_avg = np.median(pressure_sensor_voltage)
        true_pressure = 10**(unfiltered_avg - 5)
        print(true_pressure)
        '''
        ao_channel1 = ao_task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao1", min_val=0,max_val=5)
        do_channel_1_0 = do_task._do_channels.add_do_chan("NI_DAQ/port1/line0")
        do_channel_1_1 = do_task._do_channels.add_do_chan("NI_DAQ/port1/line1")
        
        
        while run:
            match state:
                case 0:
                    match gas:
                        case "air":
                            print("air")
                            ao_task.write([0],auto_start=True, timeout=10)
                        case "gas":
                            #print("gas")
                            
                            if pressure.get() > target_min_pressure.get():      #Pumping down chamber
                                ao_task.write([0],auto_start=True, timeout=10)
                                do_task.write([True,False],auto_start=True,timeout=10)
                                
                            else:                                               #At minimum threshold for backfill
                                state = 1
                case 1:                                                         #Beginning backfill
                    if pressure.get() < target_exp_pressure.get():
                        ao_task.write([5],auto_start=True, timeout=10)
                        do_task.write([False,True],auto_start=True,timeout=10)
                    else:
                        ao_task.write([0],auto_start=True, timeout=10)
                        do_task.write([True,False],auto_start=True,timeout=10)
                        state = 2
                case 2:
                    print("begin dischage")
                    time.sleep(2)
                    case = 0
                    break

run_experiment = Thread(target=run, daemon=True)

run_experiment.start()
root.mainloop()

                         