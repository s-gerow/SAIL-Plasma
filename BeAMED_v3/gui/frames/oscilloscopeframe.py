import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

from gui.frames.styles import ValueDisplay
from gui.frames.baseframe import BaseFrame
from threadcontroller import Controller
from datatypes import ActionResult, Waveform

class OscilloscopeFrame(BaseFrame):

    def __init__(self, parent, controller: Controller, equipment_name: str, text: str = "Siglent SDS1240X-E"):
        super().__init__(parent, controller, equipment_name, text)
        self._build()

    def _build(self):
        super()._build()
        self._build_widgets()
        self._build_figure()

    def _build_widgets(self):
        btn_col = tk.Frame(self.frame,relief="solid")
        btn_col.pack(fill="x", side="bottom")

        row_num = 0
        for i, (text, action, method) in enumerate([
            #("Connect", "osc_connect", "connect"),
            #("Disconnect", "osc_disconnect", "disconnect"),
            ("Capture", "osc_capture", "capture"),
            ("Arm Trigger", "osc_arm_trigger", "arm_trigger"),
            ("Stop", "osc_stop", "stop")
        ]):
            tk.Button(btn_col, text = text, command = lambda a=action, m=method: self._run(a, m)).grid(column=row_num,row=0)
            row_num +=1
        self.pkpk = tk.DoubleVar(value=0.0) 
        val_disp = ValueDisplay(btn_col, "Trigger Amplitude", "V | A", self.pkpk, )
        val_disp.lbl.config(width=15)
        val_disp.grid(column=row_num, row=0)

    def _build_figure(self):
        self.figure = Figure(figsize=(4,4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.figure, self.frame)
        NavigationToolbar2Tk(self.canvas, self).pack(fill="x",side="top")
        self.canvas.get_tk_widget().pack(fill="both", expand=False, side='top')

    def _style_axes(self):
        self.ax.set_ylabel("Voltage (V) | Current (A)")
        self.ax.set_xlabel("Time (s)")

    def _capture(self):
        self.logger.info("Capturing Oscilloscope View")
        self._run(action="osc_capture", method="capture")

    def _read_pkpk(self):
        self._run("osc_read_pkpk", "read_pkpk")

    def handle_result(self, result: ActionResult):
        if not result.success:
            self.logger.error(f"Oscilloscope action failed: {result.error}")
            return
        if result.action == "osc_capture":
            self._plot_waveform(result.data["result"])
        elif result.action == "osc_write":
            self.logger.debug("Write Acknowledged")
        elif result.action == "osc_read_pkpk":
            if result.data['result'] == "****":
                pkpk = 0.0
            else:
                pkpk = float(result.data['result'])
            self.pkpk.set(pkpk)
        elif result.action == "osc_arm_trigger":
            self._plot_waveform(result.data["result"])
            self.pkpk.set(result.data["result"].dy)
        else:
            self.logger.warning(f"Unhandled osc result: {result.action}")

    def _plot_waveform(self, waveform: Waveform):
        self.ax.clear()
        self._style_axes()
        self.ax.plot(waveform.time, waveform.voltage)
        self.canvas.draw()
