import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

from gui.frames.styles import HeaderLabel, ValueDisplay, EnableButton
from gui.frames.baseframe import BaseFrame
from threadcontroller import Controller, ActionResult

class MultimeterFrame(BaseFrame):
    def __init__(self, parent, controller: Controller, equipment_name: str, text:str="Keithley DMM6500"):
        super().__init__(parent, controller, equipment_name, text)
        self._running = False
        self._build()

    def _build(self):
        super()._build()
        self._build_widgets()

    def _build_widgets(self):
        btn_col = tk.Frame(self.frame)
        btn_col.pack(fill="both", expand=True, side="top")


        row_num = 0
        tk.Label(btn_col, text="Auto Range (T:Enable)").grid(row=row_num, column=0)
        self.auto_range = tk.StringVar(value="Disable")
        EnableButton(btn_col, 
                     self._enable_auto_range, 
                     self._disable_auto_range, 
                     self.auto_range).grid(row=row_num, column=1)

        row_num += 1
        HeaderLabel(btn_col, "Output").grid(row=row_num, column=0, columnspan=2)

        row_num += 1
        self.meas = ValueDisplay(btn_col, label="Voltage:", unit="V")
        self.meas.grid(row=row_num, column=0)
        tk.Button(btn_col,
                  text=":MEAS?",
                  command=lambda a="dmm_meas", m="measure": self._run(a, m)
                  ).grid(row=row_num,column=1)

        row_num += 1
        self.func = tk.StringVar(value="VOLT:DC")
        ttk.Combobox(btn_col, textvariable=self.func, values=["VOLT:DC", "CONT"]).grid(row=row_num, column=0)
        tk.Button(btn_col, 
                  text="Set Func", 
                  command=lambda a="dmm_func_select", m="func_select": self._run(a, m, func = self.func.get())
                  ).grid(row=row_num, column=1)
        
        row_num += 1
        tk.Button(btn_col,
                  text = "Start Continuous Measurement",
                  command = self._start_cont_meas,
                  ).grid(row=row_num, column=0, columnspan=2)
        
        row_num += 1
        tk.Button(btn_col,
                  text = "Stop Continuous Measurement",
                  command = self._stop_cont_meas
                  ).grid(row=row_num, column=0, columnspan=2)
        

    def _run(self, a, m, **kwargs):
        self.controller.run(action = a, target=self.equipment, method=m, **kwargs)

    def handle_result(self, result):
        if not result.success:
            self.logger.error(f"Multimeter action failed: {result.error}")
            return
        if result.action == "dmm_func_select":
            self._func_select()
        elif result.action == "dmm_meas":
            self.meas.set(float(result.data["result"]))
        # elif result.action == "dmm_cont_meas":
        #     pass
        else:
            self.logger.warning(f"Unhandled dmm result: {result.action}")

    def _func_select(self):
        func = self.func.get()
        if func == "CONT":
            self.meas.set_unit("\u03A9")
        elif func == "VOLT:DC":
            self.meas.set_unit("V")

    def _start_cont_meas(self):
        if self._running:
            self.logger.warning("Continuous dmm acquisition thread already runnning")
            return
        self._run("dmm_cont_meas", "start_continuous_measure")
        self._running = True
        self._poll()

    def _stop_cont_meas(self):
        self._running = False
        self._run("dmm_cont_meas", "stop_continuous_measure")


    def _poll(self):
        if not self._running:
            return
        
        dmm = self.controller.get(self.equipment)
        
        read = dmm.latest

        self.meas.set(float(read))

        self.after(100, self._poll)

    def _enable_auto_range(self):
        self._run(a="dmm_auto_range_enable", m="enable_auto_range")

    def _disable_auto_range(self):
        self._run(a="dmm_auto_range_disable", m="disable_auto_range")
        
