import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

from threadcontroller import Controller, ActionResult
from equipment.oscilloscope import Waveform

class OscilloscopeFrame(tk.LabelFrame):

    def __init__(self, parent, controller: Controller):
        super().__init__(parent, text="Siglent SDS1240X-E")
        self.controller = controller
        self.logger = logging.getLogger("BeAMED.gui.oscilloscope")
        self._build()

    def _build(self):
        self._build_widgets()
        self._build_figure()

    def _build_widgets(self):
        btn_row = tk.Frame(self,relief="solid")
        btn_row.pack(fill="x")

        for text, action, method in [
            #("Connect", "osc_connect", "connect"),
            #("Disconnect", "osc_disconnect", "disconnect"),
            ("Capture", "osc_capture", "capture")
        ]:
            tk.Button(btn_row, text = text, command = lambda a=action, m=method: self._run(a, m)).pack(side="left")

    def _build_figure(self):
        self.figure = Figure(figsize=(5,3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        NavigationToolbar2Tk(self.canvas, self).pack(fill="x")
        self.canvas.get_tk_widget().pack(fill="both", expand=False)

    def _style_axes(self):
        self.logger.warning(f"{type(self).__name__} does not implement _style_axes() yet")
    
    def _run(self, action: str, method: str, **kwargs):
        self.controller.run(action, "Oscilloscope", method, **kwargs)

    def _capture(self):
        self.logger.info("Capturing Oscilloscope View")
        self.controller.run("osc_capture", "Oscilloscope", "capture")

    def handle_result(self, result: ActionResult):
        if not result.success:
            self.logger.error(f"Oscilloscope action failed: {result.error}")
            return

        if result.action == "osc_capture":
            self._plot_waveform(result.data["result"])
        elif result.action == "osc_write":
            self.logger.debug("Write Acknowledged")
        else:
            self.logger.warning(f"Unhandled osc result: {result.action}")

    def _plot_waveform(self, waveform: Waveform):
        self.ax.clear()
        self._style_axes()
        self.ax.plot(waveform.time, waveform.voltage)
        self.canvas.draw()
