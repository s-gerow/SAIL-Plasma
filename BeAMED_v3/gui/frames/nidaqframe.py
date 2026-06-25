import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging
import time
from collections import deque

from datatypes import ActionResult, ConnectResult
from gui.frames.styles import HeaderLabel, IND_ON
from gui.frames.baseframe import BaseFrame
from threadcontroller import Controller

class PressureFrame(BaseFrame):
    POLL_MS = 100
    WINDOW_S = 60
    MAX_POINTS = 600

    def __init__(self, parent, controller: Controller, equipment_name = "nidaq", text="Pressure"):
        super().__init__(parent, controller, equipment_name, text)

        self._t_start = time.perf_counter()
        self._times = deque(maxlen=self.MAX_POINTS)
        self._kjl_pressure = deque(maxlen=self.MAX_POINTS)
        self._mks_pressure = deque(maxlen=self.MAX_POINTS)

        self._pressure_monitor_params: dict[str, tk.Variable] = {}
        self._running = False
        self._build()

    def _build(self):
        super()._build()
        self._build_controls()
        self._build_readout()
        self._build_plot()

    def _build_controls(self):
        control_col = tk.Frame(self)
        control_col.pack(fill="y",side="right")

        control_col.columnconfigure(0,weight=1)
        control_col.columnconfigure(1,weight=1)
        
        # Pressure Monitor Set-Up
        row_num = 0
        HeaderLabel(control_col, text="Pressure Monitor").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Label(control_col, text="Poll Frequency (ms)").grid(row=row_num, column=0)
        self._pressure_monitor_params["poll_freq"] = tk.DoubleVar(value=self.POLL_MS)
        ttk.Spinbox(control_col, 
                    textvariable=self._pressure_monitor_params["poll_freq"],
                    from_=1,
                    to=500,
                    state="disabled",
                    increment=0.1).grid(row=row_num,column=1)

        row_num += 1
        tk.Button(control_col, text="Start Pressure Monitor Thread", command=self._start).grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(control_col, text="Stop Pressure Monitor Thread", command=self._stop).grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(control_col, text="Clear Pressure Series", command = self._clear).grid(row=row_num, column=0, columnspan=2)
        row_num += 1

        # PI Control Panel
        HeaderLabel(control_col, text="PI Controller").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Label(control_col, text="K_p").grid(row=row_num, column=0)
        self._pressure_monitor_params["pi_kp"] = tk.DoubleVar(value=0.0)
        ttk.Spinbox(control_col, 
                    textvariable=self._pressure_monitor_params["pi_kp"],
                    from_=0,
                    to=1,
                    state="disabled",
                    increment=0.1).grid(row=row_num,column=1)
        row_num += 1
        tk.Label(control_col, text="K_i").grid(row=row_num, column=0)
        self._pressure_monitor_params["pi_ki"] = tk.DoubleVar(value=0.0)
        ttk.Spinbox(control_col, 
                    textvariable=self._pressure_monitor_params["pi_kp"],
                    from_=0,
                    to=1,
                    state="disabled",
                    increment=0.01).grid(row=row_num,column=1)
        row_num += 1
        tk.Button(control_col, text="Configure PI Controller").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(control_col, text="Start PI Controller").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(control_col, text="Stop PI Controller").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(control_col, text="Clear PI Series").grid(row=row_num, column=0, columnspan=2)
        row_num += 1

        # Valve Control Panel
        HeaderLabel(control_col, text="Valve Control").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(control_col, text="Vent Chamber").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(control_col, text="Pump Chamber (main)").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(control_col, text="Pump Chamber (secondary)").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(control_col, text="Close Valves").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        
    def _build_readout(self):
        row = tk.Frame(self)
        row.pack(fill="x", side="top")

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
        self.canvas.get_tk_widget().pack(side="bottom",fill="both", expand=True)

    def _style_axes(self):
        self.logger.warning(f"{type(self).__name__} does not implement _style_axes() yet")

    def handle_connect_result(self, result: ConnectResult):
        if result.success:
            self.connect_indicator.set_color(IND_ON)
            self.connect_indicator.set(True)
        else:
            self.connect_indicator.set(False)

    def _start(self):
        self.controller.run("nidaq_start_pressure", self.equipment, "start_pressure_acquisition")
        self._running = True
        self._poll()
        self.logger.info("Pressure display started")

    def _stop(self):
        self._running = False
        self.controller.run("nidaq_stop_pressure",self.equipment,"stop_pressure_acquisition")
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
        
        nidaq = self.controller.get(self.equipment)
        
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