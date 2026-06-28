import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

from gui.frames.baseframe import BaseFrame
from gui.frames.styles import EnableButton, HeaderLabel, ValueDisplay
from threadcontroller import Controller, ActionResult

class PowerFrame(BaseFrame):
    def __init__(self, parent, controller: Controller, equipment_name:str, text:str="Keithley 2260B-800-1"):
        super().__init__(parent, controller, equipment_name, text)
        self._build()
        self._output = False
        self._enable = False

    def _build(self):
        super()._build()
        self._build_widgets()


    def _build_widgets(self):
        btn_col = tk.Frame(self.frame)
        btn_col.pack(fill="both", expand=True, side="top")

        row_num = 0
        tk.Label(btn_col, text = "Enable V-output Power (T:Enable)").grid(row=row_num, column=0, columnspan=2)
        self._enabled = tk.StringVar(value="Disable")
        EnableButton(btn_col,
                     self._enable_output,
                     self._disable_output,
                     self._enabled).grid(row=row_num, column=2)
        
        row_num += 1
        HeaderLabel(btn_col, "Output").grid(row=row_num, column=0, columnspan=3)

        row_num += 1
        self.v_out = ValueDisplay(btn_col, "Voltage", "V")
        self.v_out.grid(row=row_num, column=0, columnspan=2)
        self._output = tk.StringVar(value="disable")
        EnableButton(btn_col, 
                     self._start_output,
                     self._stop_output,
                     self._output,
                     on_text = "Stop Output",
                     off_text= "Start Output"
                     ).grid(row=row_num, rowspan=2, column=2)
        row_num += 1
        self.i_out = ValueDisplay(btn_col, "Current", "A")
        self.i_out.grid(row=row_num, column=0, columnspan=2)

        row_num += 1
        HeaderLabel(btn_col, "Set").grid(row=row_num, column=0,columnspan=3)

        row_num += 1
        self._set_voltage_var = tk.DoubleVar(value=0.0)
        tk.Label(btn_col, text = "Voltage (V)").grid(row=row_num, column=0)
        ttk.Spinbox(btn_col,
                   textvariable=self._set_voltage_var,
                   from_=0,
                   to=800,
                   increment=0.1
                   ).grid(row=row_num, column=1)
        tk.Button(btn_col, 
                  text="Set",
                  command=lambda: self._set_voltage(self._set_voltage_var.get()),
                  ).grid(row=row_num, column=2)
        
        row_num += 1
        self._set_current_var = tk.DoubleVar(value=0.0)
        tk.Label(btn_col, text = "Current (A)").grid(row=row_num, column=0)
        ttk.Spinbox(btn_col,
                   textvariable=self._set_current_var,
                   from_=0,
                   to=1,
                   increment=0.1
                   ).grid(row=row_num, column=1)
        tk.Button(btn_col, 
                  text="Set",
                  command=lambda : self._set_current(self._set_current_var.get()),
                  ).grid(row=row_num, column=2)
        
    def _run(self, a, m, **kwargs):
        self.controller.run(action = a, target=self.equipment, method=m, **kwargs)

    def _enable_output(self):
        self._run("pwr_enable_output", "enable_output")

    def _disable_output(self):
        self._run("pwr_disable_output", "disable_output")

    def _start_output(self):
        if self._output:
            return
        self._output = True
        self._run("pwr_start_output", "start_output")
        self._poll()
    
    def _stop_output(self):
        self._output = False
        self._run("pwr_stop_output", "stop_output")

    def _set_voltage(self, voltage: str | float):
        self._run("pwr_set_voltage","set_voltage", voltage = voltage)

    def _set_current(self, current: str | float):
        self._run("pwr_set_current","set_current", current = current)

    def _poll(self):
        if not self._output:
            return
        
        pwr = self.controller.get(self.equipment)
        
        read = pwr.latest

        self.v_out.set(float(read[0]))
        self.i_out.set(float(read[1]))

        self.after(100, self._poll)

    def handle_result(self, result):
        if not result.success:
            self.logger.error(f"Power Supply action failed: {result.error}")
            if result.action == "pwr_enable_output":
                self._enabled.set("disable")
            elif result.action == "pwr_disable_output":
                self._enabled.set("enable")
            return
        if result.action == "pwr_enable_output":
            self._enable = True
        elif result.action == "pwr_disable_output":
            self._enable = False
        else:
            self.logger.warning(f"Unhandled dmm result: {result.action}")
        