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



#daq ai0 = pressure
#ao0 = valve 5v


def clean_exit(self):
    self.rm.close()
    self.destroy()

class pressure_gui(tk.Tk):
    def __init__(self):
        super().__init__()

        self.geometry('300x500')
        self.title("Pressure Sensor Configuration")
        self.protocol('WM_DELETE_WINDOW', lambda: clean_exit(self)) 

        #Matplotlib Config
        matplotlib.use('TkAgg')

        #Initialize Visa Resource Manager
        self.rm = pyvisa.ResourceManager()

        self.pressure = tk.IntVar()
        self.target_min_pressure = tk.IntVar()
        self.target_exp_pressure = tk.IntVar()

        pressure_label = tk.Label(self, text="Pressure").pack(anchor='w')
        pressure_box = tk.Spinbox(self,
                                  textvariable=self.pressure,
                                from_=0,
                                to=1000,)
        pressure_box.pack(anchor='e')
        target_min_label = tk.Label(self, text="Target Minimum Pressure").pack(anchor='w')
        target_min_pressure_box = tk.Spinbox(self, textvariable=self.target_min_pressure,
                                from_=0,
                                to=1000,)
        target_min_pressure_box.pack(anchor='e')
        target_exp_label = tk.Label(self, text="Target Experiment Pressure").pack(anchor="w")
        target_exp_pressure_box = tk.Spinbox(self, textvariable=self.target_exp_pressure,
                                from_=0,
                                to=1000,)
        target_exp_pressure_box.pack(anchor='e')


    
    def read_pressure(self):
        with nidaqmx.Task() as read:
            ai_channel = read.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=1, max_val=8, terminal_config=TerminalConfiguration.RSE)
            read.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
            
            while True:
                pressure_sensor_voltage = np.array(read.read(100))
                unfiltered_avg = np.median(pressure_sensor_voltage)
                true_pressure = 10**(unfiltered_avg - 5)
                self.after(1, lambda: self.pressure.set(true_pressure))
        
    def test_mfc_valve(self):
        self.target_min_pressure.set(100)
        self.target_exp_pressure.set(700)
        global run_bool 
        run_bool = True

        gas = "gas"
        state = 0
        with nidaqmx.Task() as task:
            ao_channel0 = task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao0", min_val=0,max_val=5)
            ao_channel1 = task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao1", min_val=0, max_val=5)
            print('pressure start')
            #pressure_thread.start()
            time.sleep(1)
            print('while bool start')
            if gas != "air":
                while run_bool:
                    match state:
                        case 0:
                            print("case 0")
                            if self.pressure.get() > self.target_min_pressure.get():
                                task.write([[0],[0]],auto_start=True, timeout=10)
                            else:
                                state = 1
                        case 1:
                            print("case 1")
                            if self.pressure.get() < self.target_exp_pressure.get():
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
    
    def test_run(self):
        
        read = Thread(target = self.read_pressure, daemon=True)
        read.start()

    

    




if __name__ == "__main__":
    pressure = pressure_gui()
    pressure.test_run()
    pressure.mainloop()
