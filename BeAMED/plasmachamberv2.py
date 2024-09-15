#Interface for Plasma Chamber
import tkinter as tk
from tkinter import ttk
import pyvisa
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import time
from threading import Thread, Event
import numpy as np
import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
import logging


class chamber_gui_window(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Plasma Chamber 1.0")
        self.scrnwidth = self.winfo_screenwidth()
        self.scrnheight = self.winfo_screenheight()
        self.geometry("%dx%d" % (self.scrnwidth,self.scrnheight))
        self.devices = []
        self.box_selection = tk.StringVar()
        ttk.Button(self,
                   text="open config window",
                   command=self.open_window).pack()
        
        self.devices_box = ttk.Combobox(values=self.devices,
                                        textvariable=self.box_selection)
        self.devices_box.pack()
        
    def open_window(self):
        window = configuration_window(self, self.box_selection.get())
        window.grab_set() #prevents users from using the main window

    def update_devices(self,device):
        self.devices.append(device)
        self.devices_box['values'] = self.devices
        

class device():
    def __init__(self):
        pass

class data_aquisition_device(device):
    def __init__(self):
        pass

class oscilloscope(device):
    def __init__(self):
        self.channel = 'C1'
        self.attenuation = '1'
        self.vertical_offset = '0'
        self.vertical_range = '0.15'
        self.timebase = '0.0005'
        self.horizontal_position = ''
        self.continuous_aquisition = ''
        self.trigger_mode = ''
        self.trigger_slope = ''
        self.trigger_level = ''
        self.trigger_holdoff = ''
        
    def get_configs(self):
        print(self.__dict__)

    def run_config(self):
        print(self.__dict__)

    def __str__(self):
        return "Oscilloscope"

class configuration_window(tk.Toplevel):
    def __init__(self,parent,external_device: device):
        super().__init__(parent)
        self.title(str(external_device) + " Configuration Window")

        ttk.Label(self,
                  text = "Configuration Window for External Device: " + external_device.__str__())
        
        self.tk_variables = []
        for i, item in enumerate(external_device.__dict__.items()):
            var = tk.StringVar()
            self.tk_variables.append(var)

            label = tk.Label(self, text = item)
            label.grid(row=i, column=0, padx=5, pady=5)

            combobox = ttk.Combobox(self, textvariable=var)
            combobox.grid(row=i, column=1, padx=5, pady=5)
        
        

if __name__ == "__main__":
    chamber = chamber_gui_window()
    #pressure = configuration_window(chamber)
    osc_config = {'first config': '1', 'second config': '2'}
    osc = oscilloscope()
    osc.run_config()
    chamber.update_devices(osc)
    chamber.mainloop()
    