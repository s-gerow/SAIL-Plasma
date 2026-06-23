import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging
import time
from collections import deque

from threadcontroller import Controller

class PressureFrame(tk.LabelFrame):
    POLL_MS = 100
    WINDOW_S = 60
    MAX_POINTS = 600

    def __init__(self, parent, controller: Controller):
        super().__init__(parent, text = "Pressure")
        self.controller = controller
        self.logger = logging.getLogger("BeAMED.gui.pressure")

        self._t_start = time.perf_counter()
        self._times = deque(maxlen=self.MAX_POINTS)
        self._kjl_pressure = deque(maxlen=self.MAX_POINTS)
        self._mks_pressure = deque(maxlen=self.MAX_POINTS)

        self._running = False
        self._build()

    def _build(self):
        self._build_controls()
        self._build_readout()
        self._build_plot()

    def _build_controls(self):
        column = tk.Frame(self)
        column.pack(fill="y",side="right")

        tk.Button(column, text = "Start",
                  command=self._start).pack(side="top")
        tk.Button(column, text = "Stop",
                  command=self._stop).pack(side="top")
        tk.Button(column, text = "Clear",
                  command=self._clear).pack(side="top")
        
    def _build_readout(self):
        row = tk.Frame(self)
        row.pack(fill="x", side="left")

        tk.Label(row, text="KJL").pack(side="left")
        self._kjl_var = tk.StringVar(value = "--- V")
        tk.Label(row, textvariable=self._kjl_var).pack(side="left")

        tk.Label(row, text="MKS").pack(side="left")
        self._mks_var = tk.StringVar(value = "--- V")
        tk.Label(row, textvariable=self._mks_var).pack(side="left")

    def _build_plot(self):
        self.fig = Figure(figsize=(5,3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self._style_axes()

        self._line_kjl, = self.ax.plot([], [], linewidth=0.8, label="KJL")
        self._line_mks, = self.ax.plot([], [], linewidth=0.8, label="MKS")

        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        NavigationToolbar2Tk(self.canvas, self).pack(fill="x")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _style_axes(self):
        self.logger.warning(f"{type(self).__name__} does not implement _style_axes() yet")

    def _start(self):
        nidaq = self.controller.registry.get("nidaq")
        if nidaq is None:
            self.logger.error("NIDAQ not registered")
            return
        nidaq.pressure.start()
        self._running = True
        self._poll()
        self.logger.info("Pressure display started")

    def _stop(self):
        self._running = False
        nidaq = self.controller.registry.get("nidaq")
        if nidaq:
            nidaq.pressure.stop()
        self.logger.info("Pressure display stopped")

    def _clear(self):
        self._times.clear()
        self._kjl_pressure.clear()
        self._mks_pressure.clear()
        self._t_start = time.perf_counter()
        self._line_kjl.set_data([],[])
        self._line_mks.set_data([],[])
        self.canvas.draw()

    def _poll(self):
        if not self._running:
            return
        
        nidaq = self.controller.registry.get("nidaq")
        if nidaq is None:
            return
        
        kjl, mks = nidaq.pressure.latest
        t = time.perf_counter() - self._t_start

        self._times.append(t)
        self._kjl_pressure.append(kjl)
        self._mks_pressure.append(mks)

        self._kjl_var.set(f"{kjl:.4f} V")
        self._mks_var.set(f"{mks:.4f} V")

        self._update_plot()

        self.after(self.POLL_MS, self._poll)

    def _update_plot(self):
        times = list(self._times)
        kjl_p = list(self._kjl_pressure)
        mks_p = list(self._mks_pressure)
        
        if not times:
            return
        
        self._line_kjl.set_data(times, kjl_p)
        self._line_mks.set_data(times, mks_p)

        window = self.WINDOW_S
        t_now = times[-1]
        self.ax.set_xlim(max(0, t_now - window), t_now + 1)

        all_valls = kjl_p+mks_p

        if all_valls:
            mn, mx = min(all_valls), max(all_valls)
            margin = max((mx-mn)*0.1, 0.05)
            self.ax.set_ylim(mn-margin, mx+margin)

        self.canvas.draw()