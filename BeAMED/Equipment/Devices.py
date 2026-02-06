import sys
import subprocess
import importlib.metadata
import tkinter as tk
from tkinter.dialog import Dialog
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
import time
from datetime import datetime
import threading
from threading import Thread, Event, Lock
import logging
import os
import csv
import importlib.util
from typing import Literal


# Define additional required packages
required = {'pyvisa', 'matplotlib', 'numpy', 'nidaqmx', 'pandas', 'openpyxl'}
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
import openpyxl as op
import pandas as pd

#Matplotlib Config
matplotlib.use('TkAgg')

class Device():
    '''
    Abstract class designed to be developed into different ways to access a device. Includes key attributes and methods that all devices should have such as an identifier,
    query, write, open, and close functions.
    '''
    def __init__(self, name: str):
        self.name = name
    
    def getName(self):
        return self.name
    
    def setName(self, name: str):
        self.name = name

    def open(self):
        '''self.open is not enabled for this class and must be overwritten by child classes to be used'''
        raise NotImplementedError(
            f"Method write() is not implemented for device of class {type(self)}"
        )

    def close(self):
        '''self.close is not enabled for this class and must be overwritten by child classes to be used'''
        raise NotImplementedError(
            f"Method write() is not implemented for device of class {type(self)}"
        )  

    def write(self):
        '''self.write is not enabled for this class and must be overwritten by child classes to be used'''
        raise NotImplementedError(
            f"Method write() is not implemented for device of class {type(self)}"
        )

    def read(self):
        '''self.query is not enabled for this class and must be overwritten by child classes to be used'''
        raise NotImplementedError(
            f"Method query() is not implemented for device of class {type(self)}"
        )


class DAQDevice():
    '''
    Class to aid in the programming of devices which communicate using a national instruments digital aquisition device.
    This class is keyed specifically to the NI USB-6002
    '''
    def __init__(self, parent: tk.Tk, DAQ = 'NI_DAQ', title = "untitled DAQ device"):
        '''
        :param parent: Parent tkinter object the window will reside in
        :type parent: tk.Tk
        :param DAQ: Name of National Instruments DAQ you are connecting to.
        :param title: Internal window title
        '''
        self.parentWindow = parent
        self.daq = DAQ
        self.name = title
        self.Frame = tk.LabelFrame(self.parentWindow, text=title)
        self.Frame.pack()
        tk.Label(self.Frame, text = "daqdevice").pack()
        self.pins = {}
        self.tasks = {'do': None,
                      'di': None,
                      'ao': None,
                      'ai': None}
        self.dataframe = pd.DataFrame()
        self.dataframe['Time'] = pd.Series()
        self.methods = {}
    
    def getName(self):
        return self.name
    
    def setName(self, name: str):
        self.name = name
        self.Frame.configure(text=name)

    def add_task(self, key: Literal['ai', 'ao', 'di', 'do']):
        '''
        Adds a task to the device for control of analog inputs (ai), analog outputs(ao), digital inputs (di), or digital outputs(do). A task allows for the output or input of data of any type.
        '''
        match key:
            case 'ai':
                ai_task = nidaqmx.Task()
                self.tasks[key] = ai_task
            case 'ao':
                ao_task = nidaqmx.Task()
                self.tasks[key] = ao_task
            case 'di':
                di_task = nidaqmx.Task()
                self.tasks[key] = di_task
            case 'do':
                do_task = nidaqmx.Task()
                self.tasks[key] = do_task
            case _:
                raise KeyError(f'Expected key value [ai, ao, di, do] instead got {key}')
            
    def add_analog_input(self, pin: Literal['ai1', 'ai2'], name: str, terminal_config: Literal['RSE', 'DIFF'], values: tuple = (0,5)):
        '''
        Add an analog voltage input channel on a given line.
        Parameters:
            pin: string representation of pin to add. will be used to construct line string of the form "DAQ_name/line", e.g. "DAQ/ai7"
            name: name of data input. if name is not passed then the pin will be used as placeholder.
            terminal_config: configures between differential and single ended input configuration. \n
                RSE: referenced single ended configuration measures potential difference between AI and AI_GND \n
                DIFF: referenced single ended configuration measures potential difference between AI+ and AI-. If you use DIFF mode then only supply the single differential channel pin. e.g.
                AI0 and AI4 are tied together such that AI0 = AI0+ and AI4 = AI0-, in DIFF mode only supply AI0 as a pin, not AI0, AI4.\n
            values: minimum and maximum values of the analog line, default for USB-6002 is 0 and 10V.
        '''
        v_min = values[0]
        v_max = values[1]
        if not isinstance(self.tasks['ai'], nidaqmx.Task):
            raise NameError('Analog Input task does not exist')
        ai_task = self.tasks['ai']
        line = self.daq + "/" + pin
        name = name
        match terminal_config:
            case 'RSE':
                term_cfg = nidaqmx.constants.TerminalConfiguration.RSE
            case 'DIFF':
                term_cfg = nidaqmx.constants.TerminalConfiguration.DIFF
            case _:
                raise ValueError(f'Unexpected terminal configuration {terminal_config}')
        self.pins[name] = line
        ai_task.ai_channels.add_ai_voltage_chan(line, name_to_assign_to_channel=name, min_val=v_min, max_val=v_max, terminal_config=term_cfg)
        self.dataframe[name] = pd.Series()

    def add_analog_output(self, pin: Literal['ai1', 'ai2'], name: str, values: tuple = (0,5)):
        '''
        Add an analog voltage output channel on a given line.
        Parameters:
            pin: pin name as shown on DAQ: 'ai1'.
            name: name to call the line, will be used to label the value in the metadata.
            values: minimum and maximum expected output values.
        '''
        v_min = values[0]
        v_max = values[1]
        if not isinstance(self.tasks['ao'], nidaqmx.Task):
            raise NameError('Analog Output task does not exist')
        ao_task = self.tasks['ao']
        line = self.daq + "/" + pin
        name = name
        self.pins[name] = line
        ao_task.ao_channels.add_ao_voltage_chan(line, name_to_assign_to_channel=name, min_val=v_min, max_val=v_max)
        self.dataframe[name] = pd.Series()
        
    def add_digital_input(self, port: int, line: int, name: str):
        '''
        Add a digital input channel on the given port, I am not entirely sure what this would be used for
        Parameters:
            port: port number of output line
            line: line number of output line
            name: string for input
        '''
        if not isinstance(self.tasks['di'], nidaqmx.Task):
            raise NameError('Digital Input task does not exist')
        di_task = self.tasks['di']
        line = 'port'+port+'/'+'line'+line
        name = name
        self.pins[name] = line
        di_task.di_channels.add_di_chan(line,name_to_assign_to_channel=name)

    def add_digital_output(self, port: int, line: int, name: str):
        '''
        Add a digital output channel on the given port.
        Parameters:
            port: port number of output line
            line: line number of output line
            name: string for input
        '''
        if not isinstance(self.tasks['do'], nidaqmx.Task):
            raise NameError('Digital Output task does not exist')
        do_task = self.tasks['do']
        line = 'port'+port+'/'+'line'+line
        name = name
        self.pins[name] = line
        do_task.do_channels.add_do_chan(line,name_to_assign_to_channel=name)

    def add_read_method(self, name):
        '''
        Function used to add a method to a the DAQDevice which can be run using read_threads
        :param target: function handle of target function
        :type target: function
        :param name: name of the function, can be used to run it specfically, otherwise used for logging.
        '''
    
    def nidaqmx_method(self, task: Literal['ai', 'ao', 'di', 'do'], function, *args, **kwargs):
        '''Execute a nidaqmx task function on the chosen task.\n
        Parameters:
            task: string representation of which task object to perform the function on.
            function: callable task method.
            *args: arguments for method:
            *kwargs: keyword arguments for function.
        Examples:
        You can pass the function including its arguments using lamba.
            >>> DAQDeviceWindow.nidaqmx_method(
                'ao', 
                lambda task: task.ao_channels.add_ao_func_gen_chan(
                        'Dev/ao1',
                        name_to_assign_to_channel="name",
                        type=FuncGenType.SINE,
                        freq=1000.0
                )
            )\n
        Or you can pass the arguments as args and kwargs which are forwarded to the function
            >>> DAQDeviceWindow.nidaqmx_method(
                'ao',
                lambda task, *a, **kw: task.ao_channels.add_ao_func_gen_chan(*a, **kw),
                'Dev1/ao1',
                name_to_assign_to_channel="name",
                type=FuncGenType.SINE,
                freq=1000.0
            )\n
        Both of these will create a channel for continually generating a waveform on the selected physical channel. See the nidaqmx-python readthedocs for specific functions.
        '''
        return function(self.tasks[task], *args, **kwargs)
        
class VisaDevice(Device):
    '''
    Base class for VISA devices
    '''
    def __init__(self, parent:tk.Tk, manager: pyvisa.ResourceManager, inst:str, title = "untitled visa device", auto_import_configurations = False, configuration_file: str = None):
        super().__init__(name=title)
        self.parentWindow = parent
        self.resourceManager = manager
        self.instrumentID = inst
        self.configOptions = {}
        self.configFile = None
        self.state = False #True = open, False = close. Can be verified with list_opened resources.
        self.resource = None

        if auto_import_configurations and configuration_file != None:
            self.setConfigsFromFile(configuration_file)
        elif auto_import_configurations and configuration_file == None:
            configuration_file = fd.askopenfilename()
            self.setConfigsFromFile(configuration_file)
    
    def open(self):
        if self.state:
            print("cannot open when device is already open")
        else:
            print("opening...")
            self.resource = self.resourceManager.open_resource(self.instrumentID)
            if self.resource in self.resourceManager.list_opened_resources():
                print("Device Successfully Opened")
                self.state = True
    
    def close(self):
        if self.state:
            self.resource.close()
            if self.resource in self.resourceManager.list_opened_resources():
                print("Failed to close resource")
            else:
                print("Resource Successfully Closed")
                self.state = False
        
    def identify(self):
        if self.instrumentID in self.resourceManager.list_resources():
            print(self.resourceManager.list_resources(self.instrumentID)[0])
            return self.resourceManager.list_resources(self.instrumentID)[0]
        else:
            raise NameError(
                f"Instrument with ID {self.instrumentID} not found. Implementation to choose new ID is not yet available."
            )
    
    def getConfigOption(self, option = None):
        '''VisaDevice.configure() prints the configurations stored in the dictionary'''
        if option == None:    
            configArray = np.array([])
            for config, value in self.configOptions.items():
                print(f"config: {config} | value: {value[0]} | range: {value[1]}")
                configArray = np.concat([[value[0], value[1]]])
            return configArray
        else:
            return np.array([self.configOptions[option]])

    def setConfigs(self, config_name, value):
        '''VisaDevice.setConfiguration(config_name, value) changes the value of a given configuration which already exists to the parameter value'''
        raise NotImplementedError(
            f"Method is not implemented for device of class {type(self)}"
        )

    def setConfigsFromFile(self, config_file: str):
        '''VisaDevice.new_configurations uses a configuration text file of the correct format to set the configuration options attribute to the given settings.'''
        with open(config_file, 'r') as f:
            for i, row in enumerate(csv.reader(f,delimiter='\t')):
                if i == 0:
                    continue
                config_name = row[0]
                default_value = row[1]
                range = row[2]
                self.configOptions.__setitem__(config_name,[default_value,range])
    
    def configureDevice(self):
        raise NotImplementedError(
            f"Method is not implemented for device of class {type(self)}"
        )

class VisaDeviceFrame(ttk.LabelFrame):
    '''
    Frame for displaying VISA device information
    '''
    def __init__(self, parent: tk.Tk, device: VisaDevice, text = None):
        self.device = device
        super().__init__(parent, text=self.device.getName())
        self.device = device
        self.instrumentFrame = tk.Frame(self)
        self.create_widgets()


    def create_widgets(self):
        ''''''
        instrumentInitFrame = tk.Frame(self)
        instrumentInitFrame.pack(side='top', fill = 'x')
        self.instrumentFrame.pack(side='top', fill = 'both')

        tk.Button(instrumentInitFrame, text="Identify Instrument", command=lambda: instrumentNameVar.set(self.device.identify())).grid(row=0, column=0)
        instrumentNameVar = tk.StringVar()
        tk.Spinbox(instrumentInitFrame, textvariable=instrumentNameVar, state='readonly').grid(row=0, column=1)
        tk.Button(instrumentInitFrame, text="Open Instrument", command = self.device.open).grid(row=0,column=2)
        tk.Button(instrumentInitFrame, text="Close Instrument", command=self.device.close).grid(row=0,column=3)

class DAQDeviceFrame(ttk.Frame):
    '''
    Frame for displaying DAQ Device information
    '''
    pass

class keithleyDMM6500(VisaDevice):
    '''
    Keithley DMM6500 Digital Multimeter
    '''
    def __init__(self, parent: tk.Tk, inst = "USB0::0x05E6::0x6500::04386498::INSTR", title="Keithley DMM6500"):
        super().__init__(self, parent, inst, title)

class keithley2260B(VisaDevice):
    '''
    Keithley 2260B-800-1 Power Supply
    '''
    pass

class keithley2290_5(VisaDevice):
    '''
    Keithley 2290_5 5kV Power Supply
    '''
    pass

class siglentSDS1204X_E(VisaDevice):
    '''
    Siglent SDS1204X-E Oscilloscope
    '''
    def __init__(self, parent: tk.Tk, manager: pyvisa.ResourceManager, inst = "USB0::0xF4EC::0xEE38::SDSMMFCD4R9625::INSTR", title="Siglent SDS1204X-E", auto_import_configurations = False, configuration_file: str = None):
        super().__init__(parent, manager=manager, inst= inst, title = title, auto_import_configurations=auto_import_configurations, configuration_file=configuration_file)

    def create_widgets(self, frame: ttk.Frame|ttk.LabelFrame,):
        configFrame = tk.Frame(frame)
        configFrame.grid(row=0, column=0, rowspan=2)
        plotFrame = tk.Frame(frame)
        plotFrame.grid(row=0, rowspan=2, column=1, columnspan=2)
        buttonFrame = tk.Frame(frame)
        buttonFrame.grid(row=2, column=1, columnspan=2)

        figure = Figure(dpi=75)
        self.figure_canvas = FigureCanvasTkAgg(figure, plotFrame)
        NavigationToolbar2Tk(self.figure_canvas, plotFrame).pack(side='top')
        self.axes = figure.add_subplot()
        self.axes.set_title('Oscilloscope')
        self.axes.set_ylabel('Voltage')
        self.axes.set_xlabel('Time')
        self.figure_canvas.get_tk_widget().pack(side='top')
        
        tk.Button(buttonFrame, text="Save Plot", command = self.savePlot).grid(row=0, column=0)
        tk.Button(buttonFrame, text="Grab Plot", command=self.getPlot).grid(row=0, column=1)

    def savePlot(self):
        print("saving plot...")
        print("nothing happened, this function is not completed")        

    def getPlot(self):
        print("getting current plot from oscilloscope")
        self.axes.clear()
        self.resource.write("CHDR OFF")
        self.resource.write('DATASOURCE CHANNEL2')
        self.resource.write('DATA:ENCDG SRI')
        self.resource.write('DATA:WIDTH 2')
        self.resource.write('DATA:START 0')
        self.resource.write('DATA:STOP 1000')
        
        sample_rate = self.resource.query("SARA?")
        time_inter = 1/float(sample_rate)
        tdiv = float(self.resource.query("TDIV?"))
        offset = float(self.resource.query("C1:OFST?"))
        vdiv = float(self.resource.query("C1:VDIV?"))
        self.resource.write("C1:WF? DAT2")
        wf = self.resource.read_raw()
        wf = wf[16:-2]

        hgrid = 14

        decimal = []
        for i,byte in enumerate(wf):
            decimal.append(int.from_bytes(wf[i:i+1], byteorder=sys.byteorder))
        data = np.array(decimal)
        time = np.flip(np.array([(tdiv*hgrid)-(idx*time_inter) for idx in range(0,data.size) ]))

        voltage_data = np.array([int(code)*(vdiv/25)-offset if int(code) < 127 else (int(code)-256)*(vdiv/25)-offset for code in data])

        self.axes.plot(time, voltage_data)
        self.axes.set_title('Discharge Plot')
        self.axes.set_ylabel('Voltage (V)')
        self.axes.set_xlabel('Time (s)')

        self.figure_canvas.draw()

    def monitorTrigger(self):
        self.resource.open()
        
        while(self.isExperimentStarted.is_set()& self.isDischargeTriggered.is_set() == False):
            VPP = self.Osc.resource.query(f"{self.Osc.options['Channel'][0]}:PARAMETER_VALUE? PKPK")
            if VPP[5:-1] == "****":
                VPP_num = 0
            else:
                VPP_num = float(VPP[5:-1])
            if VPP_num > 0:
                self.t_trigger = time.time()
                self.isDischargeTriggered.set()
                self.triggered_var.set(1)

                self.Osc.resource.write("STOP")
                self.log_message("OSC", "INFO", "Discharge Detected")
                self.osc_plot()
                self.Osc.close_device()
                return
            if(self.StopALL.is_set()):
                self.log_message("OSC", "WARN", "Stop All Detected. Quitting...")
                return
        self.Osc.close_device()
        time.sleep(5)
        

        # def configureOscilloscope(self, oscName):
        # thread = "CFG-OSC"
        # level = "INFO"
        # self.log_message(thread, level, f"configuring{oscName}")
        # self.Osc = self.parent.devices[oscName][0]
        
        # self.Osc.open_device()
        # if self.Osc.options['Reset'][0] == "True":
        #     self.Osc.resource.write("*RST")
        # self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:ATTN {self.Osc.options['Attenuation'][0]}")
        # self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:OFST {self.Osc.options['Vertical Offset'][0]}")
        # self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:VDIV {self.Osc.options['Voltage Division'][0]}")
        # self.Osc.resource.write(f"TDIV {self.Osc.options['Time Division'][0]}")
        # self.Osc.resource.write(f"HPOS {self.Osc.options['Horizontal Position'][0]}")
        # self.Osc.resource.write(f"TRMD {self.cont_acq}")
        # self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:TRSL {self.Osc.options['Trigger Slope'][0]}")
        # self.Osc.resource.write(f"TRSE EDGE,SR,{self.Osc.options['Channel'][0]},HT,TI,HV,{self.Osc.options['Holdoff'][0]}")
        # self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:TRLV {self.Osc.options['Trigger Level'][0]}")
        # self.Osc.resource.write("CHDR OFF")
        # self.Osc.close_device()
        # self.log_message(thread, level, f"{oscName} Successfully Configured")
        # self.isOscConfigured.set()
        