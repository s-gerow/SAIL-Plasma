import queue
import logging
import threading
import tkinter as tk
from tkinter import scrolledtext
import io
import sys
import datetime
import traceback

class ThreadMonitor(tk.Frame):
    REFRESH_MS = 500

    def __init__(self, parent, namespace: dict, log_queue: queue.Queue):
        super().__init__(parent)
        self.logger = logging.getLogger("BeAMED.gui.debug")
        self.namespace = namespace
        self.queue = log_queue
        self._build()
        self._poll_threads()

    def _build(self):
        tk.Label(self, text="Active Threads").pack(side="top", fill="x")
        self.thread_listbox = tk.Listbox(
            self,
            bg="#252526",
            fg="#d4d4d4",
            font=("Courier New", 9),
            relief="flat",
            selectmode='browse'
        )
        self.thread_listbox.pack(side="top", fill="both", expand=True)

    def _poll_threads(self):
        self._update_thread_list()
        self.after(self.REFRESH_MS, self._poll_threads)

    def _update_thread_list(self):
        threads = threading.enumerate()
        self.thread_listbox.delete(0,"end")
        for t in threads:
            name = f"{'[D] ' if t.daemon else '     '}{t.name}"
            self.thread_listbox.insert("end", name)
            if t.daemon:
                self.thread_listbox.itemconfig("end", fg="#808080")
            else:
                self.thread_listbox.itemconfig("end", fg="#d4d4d4")
