import queue
import logging
import threading
import tkinter as tk
from tkinter import ttk

from gui.logger import QueueHandler
from gui.terminal import BenchTerminal
from gui.threadmonitor import ThreadMonitor
from gui.frames.oscilloscopeframe import OscilloscopeFrame
from gui.frames.nidaqframe import PressureFrame
from threadcontroller import Controller, ConnectResult, ActionResult

class MainWindow(tk.Tk):
    POLL_INTERVAL_MS = 50

    def __init__(self, controller: Controller):
        super().__init__()
        self.logger = logging.getLogger("BeAMED.gui")
        self.controller = controller
        self.title("BeAMED Control Panel v3")
        self.state('zoomed')
        # self.configure(bg='#1e1e1e')

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
        self._build_frames()
        self._build_menubar()
    
    def _build_frames(self):
        self.rowconfigure(0, weight=8)
        self.rowconfigure(1, weight=2)
        self.columnconfigure(0,weight=1)
        self.main_frame = tk.Frame(self)
        self.main_frame.grid(row=0, column=0, sticky="NSEW")
        
        self.debug_frame = tk.Frame(self)
        self.debug_frame.grid(row=1,column=0,sticky="nsew")
        self.debug_frame.columnconfigure(0,weight=8)
        self.debug_frame.columnconfigure(1,weight=2)
        self.debug_frame.rowconfigure(0, weight=1)

        self.terminal_frame = BenchTerminal(self.debug_frame, namespace=self._build_namespace(), log_queue=self.queue)
        self.terminal_frame.grid(row=0, column=0, sticky="NSEW")
        self.thread_frame = ThreadMonitor(self.debug_frame, namespace=self._build_namespace(), log_queue=self.queue)
        self.thread_frame.grid(row=0, column=1,sticky="nsew")

        self._debug_open = tk.BooleanVar(value=True)
        self._terminal_open = tk.BooleanVar(value=True)
        self._threads_open = tk.BooleanVar(value=True)

        self.osc_frame = OscilloscopeFrame(self.main_frame, self.controller)
        self.osc_frame.pack(fill="both", expand=True)

        self.pressure_frame = PressureFrame(self.main_frame, self.controller)
        self.pressure_frame.pack(fill="both", expand=True, side="right")
        
    def _build_namespace(self) -> dict:
        """
        This is basically the PATH variable for a regular terminal. it defines the commands the terminal bar in the gui can recognize
        """
        return {
            "controller": self.controller,
            "debug": lambda name: logging.getLogger(f"BeAMED.{name}").setLevel(logging.DEBUG),
            "quiet": lambda name: logging.getLogger(f"BeAMED.{name}").setLevel(logging.WARNING),
        }

    def _toggle_terminal(self):
        if self._terminal_open.get():
            self.terminal_frame.grid(row=0, column=0, sticky="NSEW")
            self.logger.debug("Closing Terminal")
        else:
            self.terminal_frame.grid_forget()
            self.logger.debug("Opening Terminal")

    def _toggle_debug(self):
        if self._debug_open.get():
            self.debug_frame.grid(row=1, column=0, sticky="NSEW")
            self.logger.debug("Closing Debug")
        else:
            self.debug_frame.grid_forget()
            self.logger.debug("Opening Debug")

    def _toggle_threads(self):
        if self._threads_open.get():
            self.thread_frame.grid(row=0, column=1, sticky="NSEW")
            self.logger.debug("Closing Thread Monitor")
        else:
            self.thread_frame.grid_forget()
            self.logger.debug("Opening Thread Monitor")

    def _build_menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File Menu
        # This should have exit, preferences, save, save as, export, import, and similar options
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        # Edit
        # This normally has copy paste delete undo redo but I dont think I need those
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        # View
        # This has stuf related to the view. I think this should be where I toggle the output/terminal panel on or off. I think a 
        # fullscreen button. maybe an option to turn off different equipment views? I am not sure. This may not have a lof of things
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Toggle Debug", command=self._toggle_debug, variable=self._debug_open, )
        view_menu.add_checkbutton(label="Toggle Terminal", command=self._toggle_terminal, variable=self._terminal_open, )
        view_menu.add_checkbutton(label="Toggle Thread Monitor", command=self._toggle_threads, variable=self._threads_open, )
        # Equipment Menu
        # First custom menu, this will have the options for equipment. Connect all, disconnect all. Connect individual, disconnect individual,
        # open debug console for a specific equipment. etc.
        equipment_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Equipment", menu=equipment_menu)
        equipment_menu.add_command(label="Connect All", command=self.controller.connect_all)
        equipment_menu.add_command(label="Disconnect All", command = self.controller.disconnect_all)
        # Run
        # This has stuff to do with running an experiment trial. I think run in debug, run normal, possibly run with a breakpoint. edit 
        # operation order (toggle if certain tasks are done like return to atmosphere or ground the electrode.) etc
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        # Help
        # Open help menu which maybe just takes you to docs page. or just opens a dialog box with an FAQ or the regular operating instructions. 
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)


    def _poll(self):
        #self.logger.debug("Polling queue...")
        try:
            while True:
                result = self.controller.queue.get_nowait()
                self._route_result(result)
        except queue.Empty:
            pass
        self.after(self.POLL_INTERVAL_MS, self._poll)

    def _route_result(self, result):
        if isinstance(result, ConnectResult):
            if result.success:
                self.logger.info(f"Connected: {result.key}")
            else:
                self.logger.error(f"Failed to connect {result.key}: {result.error}")
        elif isinstance(result, ActionResult):
            if result.action.startswith("osc_"):
                self.osc_frame.handle_result(result)
            else:
                self.logger.warning(f"Unhandled action result: {result.action}")
        else:
            self.logger.warning(f"Unkown result type on queue: {type(result)}")

    def _on_close(self):
        self.controller.shutdown()
        self.destroy()