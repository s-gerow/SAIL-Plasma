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
from dataclasses import field

class plot_app(tk.Tk):
    def __init__(self):
        super().__init__()
        self.state('zoomed')
        self.work_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.reader = HDF5Reader()

        self.paschen_figure_plot = Figure(dpi=90)
        self.paschen_axes = self.paschen_figure_plot.add_subplot()
        self.paschen_figure: dict[str,PaschenFigureData] = {}

        self.discharge_figure_plot = Figure(dpi=90)
        self.discharge_axes = self.discharge_figure_plot.add_subplot()

        self.selected_files = {}
        self.selected_file_frames = {}
        self.selected_points = {}

        print(f'HDF5 Plotter started in working directory {self.work_dir}')
        self._init_frames()
        self._init_files()
        self._init_discharges()
        self._init_controls()
        self._init_plot()
        self._init_discharge_info()
        self._init_discharge_plot()

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
        self.discharge_info_frame = tk.LabelFrame(self, text = "Discharge Data")
        self.discharge_info_frame.grid(row=1, column=0, columnspan=3, sticky='nsew')

        self.discharge_time_plot_frame = tk.LabelFrame(self, text="Discharge Timeseries")
        self.discharge_time_plot_frame.grid(row=1, column=3, sticky='nsew')

    def _init_files(self):
        tk.Button(self.file_frame, command=self.go_parent_dir, text=". .").grid(row=0, column=0)
        self.read_dir()

    def _init_discharges(self):
        for widget in self.discharge_frame.scrollable.winfo_children():
                widget.destroy()
        for i,(file,path) in enumerate(self.selected_files.items()):
            self.selected_file_frames[file] = tk.LabelFrame(self.discharge_frame.scrollable, text=file)
            self.selected_file_frames[file].pack(side='left',fill = 'y')
            self.open_h5(path)
            # self.selected_file_buttons[file] = TreeButton(self.selected_file_frame, enable_command=lambda dir = path: self.open_h5(dir), disable_command=self.close_h5, text=file)
            # self.selected_file_buttons[file].grid(row=i, column=0)

    def _init_controls(self):
        tk.Button(self.input_frame, text="Plot", command=lambda: self.plot_paschen_curve()).grid(row=0, column=0)
        tk.Button(self.input_frame, text="Import Legacy Data", command=self.import_excel_data).grid(row=1, column=0)
        tk.Button(self.input_frame, text="Clear Plot", command=self.clear_plot).grid(row=2,column=0)

    def _init_plot(self):
        self.paschen_figure_canvas = FigureCanvasTkAgg(self.paschen_figure_plot, self.plot_frame)
        NavigationToolbar2Tk(self.paschen_figure_canvas, self.plot_frame).pack(side='bottom')
        self.paschen_figure_canvas.get_tk_widget().pack(side='bottom')

    def _init_discharge_info(self):
        for widget in self.discharge_info_frame.winfo_children():
            widget.destroy()
        self.discharge_field_containers: dict[str,tk.Entry] = {}
        for key in self.selected_points.keys():
            show_frame = tk.Frame(self.discharge_info_frame)
            show_frame.pack(anchor='n', fill='both')
            TreeButton(show_frame, text="Selected Points")
            # frame = tk.LabelFrame(self.discharge_info_frame, text=key)
            # frame.pack(anchor='w', fill='y')
            # TreeButton(frame, text="Edit", enable_command=self.enable_discharge_edit, disable_command=self.disable_discharge_edit).grid(row=0, column=0)

    def _init_discharge_plot(self):
        self.discharge_figure_canvas = FigureCanvasTkAgg(self.discharge_figure_plot, self.discharge_time_plot_frame)
        NavigationToolbar2Tk(self.discharge_figure_canvas, self.discharge_time_plot_frame).pack(side='bottom')
        self.discharge_figure_canvas.get_tk_widget().pack(side='bottom')

    def enable_discharge_edit(self):
        for container in self.discharge_field_containers.values():
            container.config(state='normal')

    def disable_discharge_edit(self):
        for container in self.discharge_field_containers.values():
            container.config(state='readonly')
    
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
                    TreeButton(self.file_frame, enable_command=lambda dir = element.path, name = element.name: self.select_h5(name, dir), disable_command=lambda name=element.name: self.deselect_h5(name), text=element.name, width=res).grid(row=_row, column=0)
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

    def select_h5(self, file, path):
        self.selected_files[file] = path
        print(self.selected_files.keys())
        self._init_discharges()

    def deselect_h5(self, file):
        try:
            if file in self.selected_files.keys():
                self.selected_files.pop(file)
            self.close_h5(file)
        except KeyError:
            print(f"{file} not in selection")
        
    def open_h5(self, path):
        _row=0
        #self._init_discharges()
        self.reader.open_file(path)
        discharges = self.reader.list_discharges()
        res = reduce(lambda x,y: max(x,y), map(len,discharges))
        file_key = list(filter(lambda key: self.selected_files[key] == path, self.selected_files))[0]
        self.paschen_figure[file_key] = self.reader.get_paschen_data()
        frame = self.selected_file_frames[file_key]
        for discharge in discharges:
            tk.Button(frame, text = discharge, width=res, command=lambda path=path, point = discharge: self.inspect_point(point, path)).grid(row=_row, column=0)
            _row+=1
        self.reader.close_file()

    def plot_paschen_curve(self):
        self.paschen_axes.clear()
        if len(self.paschen_figure) > 0:
            for name,figure in self.paschen_figure.items():
                #_, vcr, pd_, _ = self.reader.get_paschen_data()
                #vcr, _, pd_, _ = self.reader.get_paschen_data()
                print(type(self.paschen_figure[name]))
                self.paschen_axes.scatter(self.paschen_figure[name].pd_mks, self.paschen_figure[name].vcr_dmm, label = f"h5: {name}")
                self.paschen_axes.legend()
                self.paschen_figure_canvas.draw()
        else:
            print("no file open")

    def close_h5(self, file):
        self._init_discharges()
        if file in self.paschen_figure.keys():
            self.paschen_figure.pop(file)
        
    def import_excel_data(self):
        file_path = fd.askopenfilename(title="Select Data Source", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            print("no file selected")
            return
        if len(self.paschen_figure) > 0:
            result = messagebox.askokcancel("Append Data?", "You already have Paschen curve data imported, would you like to append this file to the current plot?")
            if not result:
                return
            else:
                pd_, v, _, _ = open_data(filepath=file_path)
                self.paschen_axes.scatter(pd_, v, label = "Excel")
                self.paschen_axes.legend()
                self.paschen_figure_canvas.draw()

    def clear_plot(self):
        self.paschen_axes.clear()
        self.paschen_figure_canvas.draw()
            
    def inspect_point(self, point, file):
        self.reader.open_file(file)
        print(self.selected_points.keys())
        if point in self.selected_points.keys():
            pass
        else:
            self.selected_points[point] = self.reader.get_discharge_data(point)
        self.reader.close_file()
        self._init_discharge_info()

if __name__ == "__main__":
    plotter = plot_app()
    plotter.mainloop()