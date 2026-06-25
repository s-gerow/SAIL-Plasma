import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging
from threading import Thread

from gui.frames.styles import IndicatorButton, IND_ERROR, IND_ON, IND_WARN
from threadcontroller import Controller, ActionResult, ConnectResult, DisconnectResult

class BaseFrame(tk.LabelFrame):
    def __init__(self, parent, controller: Controller, equipment_name: str, text: str, _build=False):
        super().__init__(parent, text=text)
        self.controller = controller
        self.logger = logging.getLogger("BeAMED.gui."+equipment_name)
        self.equipment = equipment_name

        if _build:
            self._build()

    def _run(self, action: str, method: str, **kwargs):
        self.controller.run(action, self.equipment, method, **kwargs)

    def _build(self):
        self._status_frame = tk.Frame(self)
        self._status_frame.pack(anchor="n", fill="x", expand=False)
        self.frame = tk.Frame(self)
        self.frame.pack(fill="both", expand=True)

        self.connect_indicator = IndicatorButton(self._status_frame, "small", off_color=IND_ERROR, on_color=IND_WARN)
        self.connect_indicator.pack(side="left")

        self.connect_button = tk.Button(self._status_frame, text="Connect", command=self._connect)
        self.connect_button.pack(side="left")

        self.validate_button = tk.Button(self._status_frame, text="Validate")

    def _connect(self):
        self.controller.connect(self.equipment)

    def _disconnect(self):
        self.controller.disconnect(self.equipment)

    def handle_connect_result(self, result: ConnectResult|DisconnectResult):
        if isinstance(result, ConnectResult):
            if result.success:
                self.connect_indicator.set_color(IND_WARN)
                self.connect_indicator.set(True)
                self.connect_button.config(text="Disconnect", command=self._disconnect)
            else:
                self.connect_indicator.set(False)
        elif isinstance(result, DisconnectResult):
            if result.success:
                self.connect_indicator.set(False)
                self.connect_button.config(text="Connect", command=self._connect)
            else:
                self.connect_indicator.set(False)

    def handle_result(self, result: ActionResult):
        self.logger.debug(f"Unhandled action '{result.action}'")


    