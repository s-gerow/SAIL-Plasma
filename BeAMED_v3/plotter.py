from hdf5_reader import HDF5Reader
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pathlib import Path
from functools import reduce
from gui.frames.styles import TreeButton, ScrollFrame
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
from dataanalysis import *
from datatypes import PaschenFigureData
from tkinter import messagebox

class plot_app(tk.Tk):
    def __init__(self):
        super().__init__()
        self.state('zoomed')
        self.work_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.reader = HDF5Reader()
        self.figure = Figure(dpi=100)
        self.axes = self.figure.add_subplot()
        self.paschen_figure = PaschenFigureData()

        print(f'HDF5 Plotter started in working directory {self.work_dir}')
        self._init_frames()
        self._init_files()
        self._init_discharges()
        self._init_controls()
        self._init_plot()

    def _init_frames(self):
        self.file_frame = tk.LabelFrame(self, text="Files")
        self.file_frame.grid(row=0, column=0, sticky = 'nsew')
        # self.columnconfigure(0, weight=1)
        self.discharge_frame = ScrollFrame(self, text="Data")
        self.discharge_frame.grid(row=0, column=1, sticky = 'nsew')
        # self.columnconfigure(1, weight=1)
        self.input_frame = tk.LabelFrame(self, text="Controls",)
        self.input_frame.grid(row=0, column=2, sticky = 'nsew')
        # self.columnconfigure(2, weight=1)
        self.plot_frame = tk.LabelFrame(self, text="Plot")
        self.plot_frame.grid(row=0, column=3, columnspan=2, sticky = 'nsew')
        # self.columnconfigure(3, weight=2)

    def _init_files(self):
        tk.Button(self.file_frame, command=self.go_parent_dir, text=". .").grid(row=0, column=0)
        self.read_dir()

    def _init_discharges(self):
        tk.Label(self.discharge_frame.scrollable, text="Discharges").grid(row=0, column=0)

    def _init_controls(self):
        tk.Button(self.input_frame, text="Plot", command=lambda: self.plot_paschen_curve()).grid(row=0, column=0)
        tk.Button(self.input_frame, text="Import Legacy Data", command=self.import_excel_data).grid(row=1, column=0)

    def _init_plot(self):
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        NavigationToolbar2Tk(self.figure_canvas, self.plot_frame).pack(side='bottom')
        self.figure_canvas.get_tk_widget().pack(side='bottom')

    def read_dir(self):
        dir_list = os.scandir(self.work_dir)
        _row = 1
        names = []
        for element in dir_list:
            names.append(element.name)
        res = reduce(lambda x,y: max(x,y), map(len,names))
        dir_list = os.scandir(self.work_dir)
        self._file_list = []
        
        for element in dir_list:
            if element.is_dir():
                tk.Checkbutton(self.file_frame, command=lambda dir = element.path: self.open_dir(dir), text=element.name, width= res, indicatoron=False ).grid(row=_row, column=0)
            elif element.is_file():
                if 'h5' in element.name:
                    if 'test' in element.name:
                        continue
                    TreeButton(self.file_frame, enable_command=lambda dir = element.path: self.open_h5(dir), disable_command=self.close_h5, text=element.name, width=res).grid(row=_row, column=0)
                else:
                    tk.Checkbutton(self.file_frame, state='disabled', text=element.name, width=res, indicatoron=False).grid(row=_row, column=0)
            _row+=1

    def open_dir(self, dir_path):
        print(f'opening {dir_path}')
        self.work_dir = dir_path
        for widget in self.file_frame.winfo_children():
            widget.destroy()
        self._init_files()

    def go_parent_dir(self):
        parent_dir = Path(self.work_dir).parent.absolute()
        self.work_dir = parent_dir
        self.open_dir(parent_dir)

    def open_h5(self, path):
        _row=1
        for widget in self.discharge_frame.scrollable.winfo_children():
            widget.destroy()
        self.reader.open_file(path)
        discharges = self.reader.list_discharges()
        res = reduce(lambda x,y: max(x,y), map(len,discharges))
        self.paschen_figure = self.reader.get_paschen_data(self.paschen_figure)
        for discharge in discharges:
            tk.Button(self.discharge_frame.scrollable, text = discharge, width=res).grid(row=_row, column=0)
            _row+=1

    def plot_paschen_curve(self):
        self.axes.clear()
        if self.reader.is_open():
            #_, vcr, pd_, _ = self.reader.get_paschen_data()
            #vcr, _, pd_, _ = self.reader.get_paschen_data()
            self.axes.scatter(self.paschen_figure.pd_mks, self.paschen_figure.vcr_dmm, label = "h5")
            self.axes.legend()
            self.figure_canvas.draw()
        else:
            print("no file open")

    def close_h5(self):
        for widget in self.discharge_frame.scrollable.winfo_children():
            widget.destroy()
        self.reader.close_file()
        self.paschen_figure = PaschenFigureData()

    def import_excel_data(self):
        file_path = fd.askopenfilename(title="Select Data Source", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            print("no file selected")
            return
        if self.reader.is_open():
            result = messagebox.askokcancel("Append Data?", "You already have Paschen curve data imported, would you like to append this file to the current plot?")
            if not result:
                return
            else:
                pd_, v, _, _ = open_data(filepath=file_path)
                self.axes.scatter(pd_, v, label = "Excel")
                self.axes.legend()
                self.figure_canvas.draw()

            
        

if __name__ == "__main__":
    plotter = plot_app()
    plotter.mainloop()