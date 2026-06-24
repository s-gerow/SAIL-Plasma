import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

from threadcontroller import Controller, ActionResult

class MultimeterFrame(tk.LabelFrame):
    def __init__(self, parent, controller: Controller):
        super().__init__(parent, text="Keithley DMM6500")
        self.logger = logging.getLogger("BeAMED.gui.dmm")
        self.controller = controller

        self.equipment = self.controller.get("dmm").getName()
        self._build()

    def _build(self):
        self._build_widgets()

    def _build_widgets(self):
        btn_col = tk.Frame(self)
        btn_col.pack(fill="both", expand=True, side="top")

        self.dmm_mode = tk.StringVar(value="VOLT:DC")
        ttk.Combobox(btn_col, textvariable=self.dmm_mode, values=["VOLT:DC", "CONT"]).grid(row=0, column=0)
        tk.Button(btn_col, text="Set Func", command=lambda a="dmm_func_select", m="func_select": self._run(a, m, func = self.dmm_mode.get())).grid(row=0, column=1)

    def _run(self, a, m, **kwargs):
        self.controller.run(action = a, target=self.equipment, method=m, **kwargs)
