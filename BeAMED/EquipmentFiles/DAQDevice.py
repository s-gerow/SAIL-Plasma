import tkinter as tk
from tkinter import ttk
import nidaqmx
from typing import Literal
import nidaqmx.constants
import pandas as pd

class DAQDeviceWindow():
    '''
    Class to aid in the programming of devices which communicate using a national instruments digital aquisition device.
    This class is keyed specifically to the NI USB-6002
    '''
    def __init__(self, parent: tk.Tk, DAQ = 'NI_DAQ', title = "untitled DAQ device"):
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
    
    def getName(self):
        return self.name
    
    def setName(self, name: str):
        self.name = name
        self.Frame.configure(text=name)

    def add_task(self, key: Literal['ai', 'ao', 'di', 'do']):
        '''
        Adds a task to the device for control of analog inputs (ai), analog outputs(ao), digital inputs (di), or digital outputs(do).
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
            
    def add_analog_input(self, pin: Literal['ai1', 'ai2'], name: str, terminal_config: Literal['RSE', 'DIFF']):
        '''
        Function adds analog input line on pin(s) provided.
        RSE: referenced single ended configuration measures potential difference between AI and AI_GND
        DIFF: referenced single ended configuration measures potential difference between AI+ and AI-. If you use DIFF mode then only supply the single differential channel pin. e.g.
        AI0 and AI4 are tied together such that AI0 = AI0+ and AI4 = AI0-, in DIFF mode only supply AI0 as a pin, not AI0, AI4
        '''
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
        ai_task.ai_channels.add_ai_voltage_chan(line, name_to_assign_to_channel=name, min_val=0, max_val=5, terminal_config=term_cfg)
        self.dataframe[name] = pd.Series()

    def add_analog_output():
        pass
        
    def add_digital_input():
        pass

    def add_digital_output():
        pass