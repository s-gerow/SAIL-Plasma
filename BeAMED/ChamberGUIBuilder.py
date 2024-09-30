#import system default packages
import sys
import subprocess
import importlib.metadata
import tkinter as tk
from tkinter.dialog import Dialog
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
import time
from threading import Thread, Event
import logging
import os
import csv
import importlib.util

# Define additional required packages
required = {'pyvisa', 'matplotlib', 'numpy', 'nidaqmx'}
# Get installed packages
installed = {pkg.metadata['Name'].lower() for pkg in importlib.metadata.distributions()}
# Find missing packages
missing = required - installed
if missing:
    # Upgrade pip
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    # Install missing packages
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])


#Interface for Plasma Chamber
import pyvisa
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import numpy as np
import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType

#Matplotlib Config
matplotlib.use('TkAgg')

#Create Device Types
class VisaDevice(pyvisa.resources.Resource):
    def __init__(self, rm: pyvisa.ResourceManager, name: str):
        super().__init__(rm, name)
        self.name = name
        self.options = {}
    
    def configure(self):
        print("configured")
        for config, value in self.options.items():
            print(f"config: {config} | value: {value[0]} | pyvisa command: {value[1]}")

    def new_configurations(self, config_file: str):
        with open(config_file, 'r') as f:
            for i, row in enumerate(csv.reader(f,delimiter='\t')):
                if i == 0:
                    continue
                config_name = row[0]
                default_value = row[1]
                pyvisa_command = row[2]
                self.options.__setitem__(config_name,[default_value,pyvisa_command]) 

class DAQDevice():
    def __init__(self, name):
        self.task = nidaqmx.Task()
        self.name = name

#Tkinter Config Window

#tkinter config frame
class ConfigFrame(tk.LabelFrame):
    def __init__(self, parent, text, relief):
        super().__init__(parent, text=text, relief=relief)
        self.configs = {}

    
    def setConfigLocation(self, config_name, container: tk.StringVar):
        self.configs[config_name] = container

    def setConfigValue(self, config_name, value):
        var = self.configs[config_name]
        var.set(value)

    def getConfig(self, config_name):
        var = self.configs[config_name]
        value = var.get()
        return value
    
#Create Tkinter App
class ChamberApp(tk.Tk):
    def __init__(self):
        super().__init__()

        #Attributes
        self.devices = {}
        self.experiment = None
        self.rm = pyvisa.ResourceManager()

        #Configure Window
        self.title("Plasma Chamber 2.0")
        scrnwidth = self.winfo_screenwidth()
        scrnheight = self.winfo_screenheight()
        self.geometry("%dx%d" % (scrnwidth,scrnheight))
        self.pack_propagate(0)
        self.grid_rowconfigure(0,weight=1)
        self.grid_rowconfigure(1,weight=1)
        self.grid_columnconfigure(0,weight=1)

        self.experimentFrame = tk.LabelFrame(self, text="experiment", relief="sunken")
        self.experimentFrame.grid(row=0, column=0, sticky='nsew')
        self.configFrame = tk.LabelFrame(self, text="device configurations", relief='sunken')
        self.configFrame.grid(row=1, column=0, sticky='nsew')

        self.menubar = ExperimentMenu(self)
        self.menubar.deviceMenu.add_command(label="New Device", command=self.generate_configuration_frame)
        self.config(menu=self.menubar)

    def generate_configuration_frame(self, filename=None):
        if filename != None:
            dialogPopup = Dialog(None, {'title': 'Need Configurations',
                                        'text':
                                        'To connect this device you must import its configurations.\n Do you want to craete configurations manually or import a file.',
                                        'bitmap': 'questhead',
                                        'default': 0,
                                        'strings': ('Cancel', 'Create Configs', 'Import Configs')})
            if dialogPopup.num == 0: return
            elif dialogPopup.num == 1: 
                print("Create Configs Later")
                return
            elif dialogPopup.num == 2:
                filepath = fd.askopenfilename()
        elif filename == None:
            filepath = fd.askopenfilename()
            filename =os.path.splitext(os.path.basename(filepath))[0]
        if filename in self.get_device_names():
            print("device already created")
            return
        else:
            device = VisaDevice(self.rm, filename)
            device.new_configurations(filepath)
            frame = ConfigFrame(self.configFrame, text=device.name + " Configurations", relief='sunken')
            self.devices[device.name] = (device, frame)
            frame.pack(side="left")
            for i,item in enumerate(device.options):
                var = tk.StringVar()
                tk.Label(frame, text=item).grid(row=i, column=0)
                tk.Spinbox(frame, textvariable=var).grid(row=i, column=1)
                frame.setConfigLocation(item, var)
                frame.setConfigValue(item, device.options[item][0])
            self.menubar.updateFrames(device.name)

    def configure_device(self, device_name):
        self.devices[device_name][0].configure()

    def get_device_names(self):
        names = []
        for i in self.devices:
            names.append(i)
        return names


    

#Tkinter Menu for this particualr app
class ExperimentMenu(tk.Menu):
    def __init__(self, master: ChamberApp):
        super().__init__(master)
        self.master = master

        fileMenu = tk.Menu(self, tearoff=0)
        fileMenu.add_command(label="New Experiment", command=self.open_experiment)
        fileMenu.add_command(label="Run", command=self.run_experiment)
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit")

        helpMenu = tk.Menu(self, tearoff=0)
        helpMenu.add_command(label="About")

        self.removeListMenu = tk.Menu(self, tearoff=0)
        self.configureListMenu = tk.Menu(self, tearoff=0)

        self.deviceMenu = tk.Menu(self, tearoff=0)
        self.deviceMenu.add_cascade(label="Remove Device", menu=self.removeListMenu)
        self.deviceMenu.add_cascade(label="Configure Device", menu=self.configureListMenu)

        # Adding cascades
        self.add_cascade(label="File", menu=fileMenu)
        self.add_cascade(label="Devices", menu=self.deviceMenu)
        self.add_cascade(label="Help", menu=helpMenu)

    def updateFrames(self, string):
        self.removeListMenu.add_command(label = string)
        self.configureListMenu.add_command(label = string, command = lambda: self.master.configure_device(string))
    
    def open_experiment(self):
        
        filepath = fd.askopenfilename(title="Select Experiment File", 
                                               filetypes=[("Python Files", "*.py")])
        if filepath:
            if filepath.endswith(".py"):
                try:
                    self.load_experiment(filepath)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load experiment: {e}")
            else:
                messagebox.showwarning("Invalid File", "Please select a valid Python (.py) file.")

    def load_experiment(self, filepath):
        for widget in self.master.experimentFrame.winfo_children():
            widget.destroy()
        module_name = os.path.splitext(os.path.basename(filepath))[0]
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Check if the module has the 'Experiment' class
        if hasattr(module, "Experiment"):
            # Instantiate the Experiment class and pass the current root window
            experiment_instance = module.Experiment(self.master)
            self.master.experiment = experiment_instance  # Save reference to interact with it later
        else:
            messagebox.showerror("Error", "The selected file does not contain 'Experiment' class.")

    def run_experiment(self):
        if self.master.experiment == None:
            messagebox.showwarning("No Experiment Loaded", "Please open a valid experiment file")
        else:
            self.master.experiment.run_experiment()

if __name__ == "__main__":
    dusty = ChamberApp()
    dusty.mainloop()