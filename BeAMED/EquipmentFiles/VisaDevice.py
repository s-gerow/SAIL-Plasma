import tkinter as tk
from tkinter import ttk
import pyvisa

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