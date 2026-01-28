import nidaqmx
import pyvisa
import numpy as np
import tkinter as tk
from tkinter import ttk
import nidaqmx
from typing import Literal
import nidaqmx.constants
import pandas as pd


class Device():
    '''
    Abstract class designed to be developed into different ways to access a device. Includes key attributes and methods that all devices should have such as an identifier,
    query, write, open, and close functions.
    '''
    def __init__(self, name: str):
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

    def query(self):
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
        
class VisaDevice():
    '''
    Base class for VISA devices
    '''
    def __init__(self, parent:tk.Tk, inst:str, title = "untitled visa device"):
        self.parentWindow = parent
        self.name = title

    def getName(self):
        return self.name
    
    def setName(self, name: str):
        self.name = name

class keithleyDMM6500(VisaDevice):
    '''
    Keithley DMM6500 Digital Multimeter
    '''
    def __init__(self, parent: tk.Tk, inst = "USB0::0x05E6::0x6500::04386498::INSTR", title="Keithley DMM6500"):
        super().__init__(parent, inst, title)

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
    pass

class VisaDeviceFrame(ttk.Frame):
    '''
    Frame for displaying VISA device information
    '''
    def __init__(self, parent: tk.Tk, device: VisaDevice):
        super().__init__(parent)
        self.device = device
        self.create_widgets()

    def create_widgets(self):
        self.label = ttk.Label(self, text=f"Device: {self.device.getName()}")
        self.label.pack()

class DAQDeviceFrame(ttk.Frame):
    '''
    Frame for displaying DAQ Device information
    '''