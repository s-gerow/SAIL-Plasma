import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

from gui.frames.baseframe import BaseFrame
from threadcontroller import Controller, ActionResult

class PowerFrame(BaseFrame):
    def __init__(self, parent, controller: Controller, equipment_name:str, text:str="Keithley 2260B-800-1"):
        super().__init__(parent, controller, equipment_name, text)
        self._build()

    def _build(self):
        super()._build()
        btn_col = tk.Frame(self.frame)
        btn_col.pack(fill="both", expand=True, side="top")

        tk.Label(btn_col, text="filler label")
        