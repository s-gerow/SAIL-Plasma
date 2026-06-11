import queue
import logging
import threading
import tkinter as tk
from tkinter import scrolledtext
import io
import sys
import datetime
import traceback

class BenchTerminal(tk.Frame):
    '''
    This is a terminal frame accessible via the GUI which allows for dynamic calling of functions not directly available to you
    using the GUI. This will be important for testing and applying minute changes without re-running the GUI or debugging problems 
    as they happen.
    '''
    COLORS = {
        "bg":       "#1e1e1e",
        "fg":       "#d4d4d4",
        "prompt":   "#569cd6",   # blue  — for >>> input echo
        "DEBUG":    "#808080",   # gray
        "INFO":     "#d4d4d4",   # white
        "WARNING":  "#ce9178",   # orange
        "ERROR":    "#f44747",   # red
        "CRITICAL": "#f44747",   # red bold
        "result":   "#b5cea8",   # green — eval() return values
        "stdout":   "#9cdcfe",   # light blue — print() output
        "input_bg": "#2d2d2d",
        "cursor":   "#aeafad",
    }
    def __init__(self, parent, namespace: dict, log_queue: queue.Queue):
        super().__init__(parent, bg=self.COLORS['bg'])
        self.namespace = namespace
        self.queue = log_queue
        self.history: list[str] = []
        self.history_idx:int = 0
        self._build()
        self._configure_tags()
        self._poll()

    def _build(self):
        self.output = scrolledtext.ScrolledText(
            self,
            state='disabled',
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg'],
            font=('Courier New', 10),
            relief='flat',
            borderwidth=0,
            wrap='word',
            height=12,
        )
        self.output.pack(fill='both', expand=True)

        tk.Frame(self, height=1, bg='#3c3c3c').pack(fill='x')

        input_row=tk.Frame(self, bg=self.COLORS['input_bg'])
        input_row.pack(fill='x')

        tk.Label(
            input_row,
            text='>>>',
            fg=self.COLORS['prompt'],
            bg=self.COLORS['input_bg'],
            font=('Courier New', 10)
            ).pack(side='left',padx=(6,2))
        
        self.entry = tk.Entry(
            input_row,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['fg'],
            font=('Courier New', 10),
            insertbackground=self.COLORS['cursor'],
            relief='flat',
            borderwidth=0
        )
        self.entry.pack(fill='x', expand=True, padx=(0,6), pady=4)

        self.entry.bind('<Return>', self._on_enter)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Up>",     self._history_up)
        self.entry.bind("<Down>",   self._history_down)
        self.entry.focus()

    def _configure_tags(self):
        """Each tag maps to a colour in the output area."""
        for tag, color in self.COLORS.items():
            self.output.tag_config(tag, foreground=color)
        # errors and critical get bold on top of the colour
        self.output.tag_config(
            "ERROR",    foreground=self.COLORS["ERROR"],
            font=("Courier New", 10, "bold")
        )
        self.output.tag_config(
            "CRITICAL", foreground=self.COLORS["CRITICAL"],
            font=("Courier New", 10, "bold")
        )

    def _poll(self):
        try:
            while True:
                record = self.queue.get_nowait()
                self._write_log_record(record)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _write_log_record(self, record: logging.LogRecord):
        dt = datetime.datetime.fromtimestamp(record.created)
        ts = dt.strftime("%H:%M:%S.%f")[:-3]
        name = record.name.replace("BeAMED.","")
        line = f"{ts} | {record.levelname:<8} | {name:<20} | {record.getMessage()}\n"
        self._insert(line, tag=record.levelname)

        if record.exc_info:
            tb = "".join(traceback.format_exception(*record.exc_info))
            self._insert(tb, tag = "ERROR")

    def _insert(self, text: str, tag: str = "fg"):
        self.output.config(state='normal')
        self.output.insert("end", text, tag)
        self.output.see("end")
        self.output.config(state='disabled')

    def _on_enter(self, event=None):
        line= self.entry.get().strip()
        if not line:
            return
        self.history.append(line)
        self.history_idx = len(self.history)
        self.entry.delete(0, 'end')
        self._insert(f">>> {line}\n", tag="prompt")

        threading.Thread(target = self._execute,
                         args=(line,),
                         daemon=True).start()
    
    def _execute(self, line: str):
        stdout_buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_buf

        try:
            try:
                result = eval(line, self.namespace)
                captured = stdout_buf.getvalue()
                if captured:
                    self._insert_threadsafe(captured, tag="stdout")
                if result is not None:
                    self._insert_threadsafe(repr(result) + "\n", tag = "stdout")
            except SyntaxError:
                exec(line, self.namespace)
                captured = stdout_buf.getvalue()
                if captured:
                    self._insert_threadsafe(captured, tag="stdout")
        except Exception as e:
            tb = traceback.format_exc()
            self._insert_threadsafe(tb, tag="ERROR")
        finally:
            sys.stdout = old_stdout

    def _insert_threadsafe(self, text:str, tag:str='fg'):
        self.after(0, self._insert, text, tag)

    def _history_up(self, event):
        if self.history_idx > 0:
            self.history_idx -= 1
            self._set_entry(self.history[self.history_idx])
        return "break"   # stops tkinter's default arrow key behaviour

    def _history_down(self, event):
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self._set_entry(self.history[self.history_idx])
        else:
            self.history_idx = len(self.history)
            self._set_entry("")
        return "break"

    def _set_entry(self, text: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, text)

if __name__ =="__main__":
    root = tk.Tk()
    root.title("Terminal Test")
    root.geometry('900x500')
    root.configure(bg='#1e1e1e')

    log_queue = queue.Queue()

    terminal = BenchTerminal(
        root,
        namespace={
            "hello": "world",
            "add": lambda a, b: a + b
        },     # empty for now
        log_queue=log_queue,
    )
    terminal.pack(fill="both", expand=True, padx=4, pady=4)

    # pump some fake log records into the queue so we can
    # see the colours before the log polling is wired up
    def make_record(level: str, logger_name: str, message: str) -> logging.LogRecord:
        record = logging.LogRecord(
            name=logger_name,
            level=getattr(logging, level),
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None,
        )
        return record

    # put some records in the queue directly
    for level, name, msg in [
        ("DEBUG",    "bench.oscilloscope",   "QUERY: TDIV?"),
        ("DEBUG",    "bench.oscilloscope",   "RESPONSE: 1.0E-03"),
        ("INFO",     "bench.controller",     "Registered: oscilloscope (SiglentSDS1204XE)"),
        ("INFO",     "bench.oscilloscope",   "Connected successfully"),
        ("WARNING",  "bench.power_supply",   "connect() called but already connected — ignoring"),
        ("ERROR",    "bench.oscilloscope",   "Failed to open resource USB0::0xF4EC::..."),
    ]:
        log_queue.put(make_record(level, name, msg))

    root.mainloop()