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



#daq ai0 = pressure
#ao0 = valve 5v


def clean_exit(self):
    self.read_bool = False
    self.destroy()

class pressure_gui(tk.Tk):
    def __init__(self):
        super().__init__()

        self.geometry('300x500')
        self.title("Pressure Sensor Configuration")
        self.protocol('WM_DELETE_WINDOW', lambda: clean_exit(self))

        self.read_bool = False

        #Matplotlib Config
        matplotlib.use('TkAgg')

        #Initialize Visa Resource Manager

        self.old_pressure = tk.IntVar()
        self.new_pressure = tk.IntVar()
        self.new_voltage = tk.IntVar()

        self.pressure_min = 0.11 #Torr
        self.pressure_max = 10 #Torr

        old_pressure_label = tk.Label(self, text="Old Pressure Sensor").pack(anchor='w')
        old_pressure_box = tk.Spinbox(self,
                                  textvariable=self.old_pressure,
                                from_=0,
                                to=1000,)
        old_pressure_box.pack(anchor='e')
        new_pressure_label = tk.Label(self, text="New Pressure Sensor").pack(anchor='w')
        new_pressure_box = tk.Spinbox(self,
                                  textvariable=self.new_pressure,
                                from_=0,
                                to=1000,)
        new_pressure_box.pack(anchor='e')
        new_pressure_V_label = tk.Label(self, text="New Pressure Sensor Voltage Output").pack(anchor='w')
        new_voltage_box = tk.Spinbox(self,
                                  textvariable=self.new_voltage,
                                from_=0,
                                to=10,)
        new_voltage_box.pack(anchor='e')

        start_read = tk.Button(self, text="Start Reading", command=self.start_pressure)
        start_read.pack(anchor='w')

        end_read = tk.Button(self, text="Stop Reading", command=self.stop_pressure)
        end_read.pack(anchor='w')
        


    
    def read_pressure(self):
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=0, max_val=10, terminal_config=TerminalConfiguration.DIFF)
            task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai1", min_val=0, max_val=10, terminal_config=TerminalConfiguration.DIFF)

            task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
            
            while self.read_bool:
                pressure_sensor_voltage = np.array(task.read(100))
                old_pressure_unfiltered_avg = np.median(pressure_sensor_voltage[0])
                new_pressure_unfiltered_avg = np.median(pressure_sensor_voltage[1])
                old_true_pressure = 10**(old_pressure_unfiltered_avg - 5)
                new_true_pressure = (new_pressure_unfiltered_avg/10)*(self.pressure_max-self.pressure_min)+self.pressure_min
                self.after(1, lambda: self.old_pressure.set(old_true_pressure))
                self.after(1, lambda: self.new_voltage.set(new_pressure_unfiltered_avg))
                self.after(1, lambda: self.new_pressure.set(new_true_pressure))
            


    def start_pressure(self):
        self.read_bool = True
        pressure_thread = Thread(target=self.read_pressure, daemon=True)

        pressure_thread.start()


    def stop_pressure(self):
        self.read_bool = False

    def test_mfc_valve(self):
        self.target_min_pressure.set(2) #20mTorr. Turn on 
        self.target_exp_pressure.set(6) #Target pressure for experiment, turn off.
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
        self.test_mfc_valve()

    

    




if __name__ == "__main__":
    pressure = pressure_gui()
    pressure.mainloop()
