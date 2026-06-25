import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

from gui.frames.baseframe import BaseFrame
from threadcontroller import Controller, ActionResult

class MultimeterFrame(BaseFrame):
    def __init__(self, parent, controller: Controller, equipment_name: str, text:str="Keithley DMM6500"):
        super().__init__(parent, controller, equipment_name, text)
        self._build()

    def _build(self):
        super()._build()
        self._build_widgets()

    def _build_widgets(self):
        btn_col = tk.Frame(self.frame)
        btn_col.pack(fill="both", expand=True, side="top")

        self.func = tk.StringVar(value="VOLT:DC")
        ttk.Combobox(btn_col, textvariable=self.func, values=["VOLT:DC", "CONT"]).grid(row=0, column=0)
        tk.Button(btn_col, 
                  text="Set Func", 
                  command=lambda a="dmm_func_select", m="func_select": self._run(a, m, func = self.func.get())
                  ).grid(row=0, column=1)

        self.mode = tk.StringVar(value="")

    def _run(self, a, m, **kwargs):
        self.controller.run(action = a, target=self.equipment, method=m, **kwargs)
