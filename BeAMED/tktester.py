import tkinter as tk
from tkinter import ttk



class Window(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent)

        self.geometry('300x100')
        self.title('Toplevel')

        ttk.Label(self,
                  text="Hello this is the toplevel window",
                  ).pack(expand=True)
        
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.geometry('300x200')
        self.title('Main Window')

        ttk.Button(self,
                   text="open new window",
                   command=self.open_window).pack()
        
    def open_window(self):
        window = Window(self)
        window.grab_set() #prevents users from using the main window



app = App()

app.mainloop()
