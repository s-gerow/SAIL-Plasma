import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import csv
import os



class Window(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent)

        self.geometry('300x100')
        self.title('Toplevel')

        ttk.Label(self,
                  text="Hello this is the toplevel window",
                  ).pack(expand=True)
        
class Config_Frame(tk.Frame):
    def __init__(self,parent,config_file):
        super().__init__(parent)

        self.config(borderwidth=5, relief='sunken')

        self.options = {}

        self.name = os.path.splitext(os.path.basename(config_file))[0]

        with open(config_file, 'r') as f:
            for i, row in enumerate(csv.reader(f,delimiter='\t')):
                if i == 0:
                    continue
                config_name = row[0]
                default_value = row[1]
                pyvisa_command = row[2]
                self.options.__setitem__(config_name,[default_value,pyvisa_command])
                tk.Label(self,text = config_name).grid(row=i, column=0, padx=5, pady=5)
                tk.Spinbox(self).grid(row=i, column = 2, padx=5, pady=5)
        tk.Button(text="print configs", command=lambda: print(self.get_configs())).pack()

    def get_name(self):
        return self.name

    def get_configs(self):
        configs = []
        for config, value in self.options.items():
            configs.append((config,value))
        return configs

        
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.geometry('300x200')
        self.title('Main Window')

        self.config_frames = {}

        ttk.Button(self,
                   text="open config files",
                   command=self.import_configs).pack()
        
    def open_window(self):
        window = Window(self)
        window.grab_set() #prevents users from using the main window

    def create_config_frame(self, config_file):
        config_frame = Config_Frame(self, config_file)
        config_frame.pack()
        self.config_frames[config_frame.name] = config_frame

    def get_config_frame(self, frame):
        return self.config_frames.get(frame)

    def import_configs(self):
        filenames = fd.askopenfilenames()
        for file in filenames:
            self.create_config_frame(file)

if __name__ == "__main__":
    app = App()
    #print(os.listdir())
    #app.create_config_frame(r"C:\Users\gerows\Python\SAIL-Plasma\BeAMED\example_config.txt")
    #frame = app.get_config_frame("example_config")
    #print(frame.get_configs())
    app.mainloop()
