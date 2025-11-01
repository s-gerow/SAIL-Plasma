import nidaqmx
import pyvisa
import numpy as np
import tkinter as tk
from tkinter import ttk


class Device():
    '''
    Abstract class designed to be developed into different ways to access a device. Includes key attributes and methods that all devices should have such as an identifier,
    query, write, open, and close functions.
    '''
    def __init__(self, name: str):
        self.name = name

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

x = Device('test')
x.write()


