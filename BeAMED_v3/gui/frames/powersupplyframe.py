import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

from threadcontroller import Controller, ActionResult

class PowerFrame(tk.LabelFrame):
    def __init__(self, parent, controller: Controller):
        super().__init__(parent, text="Keithley 2260B-800-1")
        self.controller = controller
        self.logger = logging.getLogger("BeAMED.gui.pwr")
        self._build()

    def _build(self):
        btn_col = tk.Frame(self)
        btn_col.pack(fill="both", expand=True, side="top")

        tk.Label(btn_col, text="filler label")
        