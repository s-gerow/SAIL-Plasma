import tkinter as tk
from tkinter.dialog import Dialog
from tkinter import ttk
from tkinter import filedialog as fd
import csv
import os

class Window(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent)

        self.geometry('300x100')
        self.title('Toplevel')

        #ttk.Label(self,
        #          text="Hello this is the toplevel window",
        #          ).pack(expand=True)
        
class Config_Frame(tk.Frame):
    def __init__(self,parent,config_file):
        super().__init__(parent)

        self.config(borderwidth=5, relief='sunken')

        self.options = {}

        self.name = os.path.splitext(os.path.basename(config_file))[0]

        with open(config_file, 'r') as f:
            tk.Button(self,text="print configs", command=lambda: print(self.get_configs())).grid(row=0, column = 1, pady = 5, columnspan=2)
            tk.Label(self,text=self.name).grid(row=0, column=0)
            for i, row in enumerate(csv.reader(f,delimiter='\t')):
                if i == 0:
                    continue
                config_name = row[0]
                default_value = row[1]
                pyvisa_command = row[2]
                self.options.__setitem__(config_name,[default_value,pyvisa_command])
                tk.Label(self,text = config_name).grid(row=i+2, column=0, padx=5, pady=5)
                tk.Spinbox(self).grid(row=i+2, column = 1, padx=5, pady=5)

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

        menubar = tk.Menu(self)
        self.config(menu=menubar)

        self.experiment_input_frame = tk.Frame(self, relief='raised')
        self.experiment_input_frame.grid(row=0, column=0)
        tk.Label(self.experiment_input_frame, text="This is the experiment input frame").grid()

        self.experiment_output_frame = tk.Frame(self, relief='raised')
        self.experiment_output_frame.grid(row=0, column=1)
        tk.Label(self.experiment_output_frame, text="This is the experiment output frame").grid()

        experiment_menu = tk.Menu(menubar)
        device_menu = tk.Menu(menubar)

        experiment_menu.add_command(label="Add Element")
        experiment_menu.add_command(label="Build Experiment",
                                    command=self.build_experiment)
        device_menu.add_command(label="Add Device",
                                    command=self.import_configs)

        menubar.add_cascade(label="Experiment", 
                            menu=experiment_menu)
        menubar.add_cascade(label="Devices",
                            menu=device_menu)

        
    def open_window(self):
        window = Window(self)
        window.grab_set() #prevents users from using the main window

    def create_config_frame(self, config_file):
        config_frame = Config_Frame(self, config_file)
        self.config_frames[config_frame.name] = config_frame
        config_frame.grid(row=1, column=len(self.config_frames)-1)

    def get_config_frame(self, frame):
        return self.config_frames.get(frame)

    def import_configs(self):
        filenames = fd.askopenfilenames()
        for file in filenames:
            self.create_config_frame(file)
    
    def build_experiment(self):
        print("built")



def test():
    d = Dialog(None, {'title': 'File Modified',
                      'text':
                      'File "Python.h" has been modified'
                      ' since the last time it was saved.'
                      ' Do you want to save it before'
                      ' exiting the application.',
                      'bitmap': 'questhead',
                      'default': 0,
                      'strings': ('Save File',
                                  'Discard Changes',
                                  'Return to Editor')})
    print(d.num)

        

root = tk.Tk()
tk.Button(root, text='Test', command=test).pack()
root.mainloop()

