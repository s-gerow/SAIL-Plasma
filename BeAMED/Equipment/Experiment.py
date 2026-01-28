import pyvisa
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
import time
from threading import Thread, Event, Lock
import numpy as np
import pandas as pd
import os
import importlib.util
import sys
from Devices import DAQDevice, VisaDevice, VisaDeviceFrame, DAQDeviceFrame



class experimentWindow(tk.Tk):
    '''
    Creates a top-level widget to contain one or more device interaction spaces. Allows for the importing of devices which contain logic, storage, and tkinter widgets for the 
    control of external devices.
    '''
    def __init__(self, title = "untitled experiment window", fullscreen = False):
        super().__init__(className = title)
        self.equipmentDict = {}
        if fullscreen:
            self.geometry("%dx%d" % (self.winfo_screenwidth(),self.winfo_screenheight()))
        self.rm = pyvisa.ResourceManager()
        self.menuBar = tk.Menu(self)
        self.fileMenu = tk.Menu(self, tearoff=0)
        self.equipmentlist = tk.Menu(self.fileMenu, tearoff=0)
        self.fileMenu.add_cascade(label="Add Equipment", menu=self.equipmentlist)
        self.menuBar.add_cascade(label="File", menu=self.fileMenu)
        self.config(menu=self.menuBar)
        
    def get_resources(self):
        '''
        Returns a tuple containing resources available to the resource manager.
        '''
        return self.rm.list_resources()
    
    def open_resource(self, inst: str):
        '''
        Opens a resource with a given name
        '''
        return self.rm.open_resource(resource_name=inst)
    
    def add_equipment(self, instrument: VisaDeviceFrame | DAQDeviceFrame):
        '''
        Adds the equipment frame of a given Visa or DAQ instrument
        '''
        self.equipmentDict[instrument.getName()] = instrument

    
    

if __name__ == "__main__":
    #Automatically creates chamber app and imports experiment
    #For this to work you will need to write in the file location of the current file as well as the file location of the configuration files
    chamber = experimentWindow(title='test gui', fullscreen = True)
    chamber.mainloop()