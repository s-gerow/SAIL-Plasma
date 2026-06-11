import queue
import logging
import threading
import tkinter as tk
from tkinter import ttk

from gui.logger import QueueHandler
from gui.terminal import BenchTerminal
from threadcontroller import Controller, ConnectResult, ActionResult

class MainWindow(tk.Tk):
    POLL_INTERVAL_MS = 50

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller
        self.title("BeAMED Control Panel v3")
        scrnwidth = self.winfo_screenwidth()
        scrnheight = self.winfo_screenheight()
        self.geometry("%dx%d" % (scrnwidth,scrnheight))
        #self.configure(bg='#1e1e1e')

        self.queue = queue.Queue()
        self._init_logging()
        self._build_widgets()
        self._poll()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_logging(self):
        handler = QueueHandler(self.queue)
        handler.setLevel(logging.DEBUG)
        logging.getLogger("BeAMED").addHandler(handler)

    def _build_widgets(self):
        pass

    def _poll(self):
        try:
            while True:
                result = self.controller.queue.get_nowait()
                self._route_result(result)
        except queue.Empty:
            pass
        self.after(self.POLL_INTERVAL_MS, self._poll)

    def _route_result(self, result):
        pass

    def _on_close(self):
        self.controller.shutdown()
        self.destroy()