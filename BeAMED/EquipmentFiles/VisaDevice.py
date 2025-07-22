import tkinter as tk
from tkinter import ttk
import pyvisa

class VisaDeviceWindow():
    def __init__(self, parent:tk.Tk, inst:str, title = "untitled visa device"):
        self.parentWindow = parent
        self.name = title

    def getName(self):
        return self.name
    
    def setName(self, name: str):
        self.name = name

class keithleyDMM6500(VisaDeviceWindow):
    def __init__(self, parent: tk.Tk, inst = "USB0::0x05E6::0x6500::04386498::INSTR", title="Keithley DMM6500"):
        super().__init__(parent, inst, title)