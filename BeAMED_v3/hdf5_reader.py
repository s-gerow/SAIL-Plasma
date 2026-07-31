import h5py
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import os

class HDF5Reader:
    def __init__(self):
        self.filepath: Path | str | None = None
        self._save_dir: Path = Path("c:/Users/gerows/Python/SAIL-Plasma/BeAMED_v3/data")
        self.open = False

    def open_file(self, filepath: Path | str):
        if os.path.exists(self._save_dir/filepath):
            print(f"Successfully opened file: {self._save_dir/filepath}")
        else:
            print(f"Failed to open file {self._save_dir/filepath}. Does not exist")
            return
        self.filepath = Path(filepath)
        self.open = True

    def set_directory(self, dir_ = Path | str):
        self._save_dir = dir_
        if os.path.isdir(dir_):
            return
        else:
            os.makedirs(dir_)

    def list_discharges(self):
        if not self.open:
            return
        with h5py.File(self._save_dir/self.filepath, mode='r') as f:
            print(list(f['discharges']))

    def plot_discharge_timeseries(self, index: int):
        if not self.open:
            return
        with h5py.File(self._save_dir/self.filepath, mode = 'r') as f:
            voltage_dmm = np.array(f['discharges'][f"discharge_{index:03d}"]['dmm']['voltage_values'])
            time_dmm = np.array(f['discharges'][f"discharge_{index:03d}"]['dmm']['voltage_times'])
            voltage_pwr = np.array(f['discharges'][f"discharge_{index:03d}"]['power_supply']['voltage_values'])
            time_pwr = np.array(f['discharges'][f"discharge_{index:03d}"]['power_supply']['voltage_times'])
            #discharge_time = 
            #print(list(f['discharges'][f"discharge_{index:03d}"]['dmm']['t_trigger']))
        fig, ax = plt.subplots()
        ax.set_title(r'Air $\O$=0.8cm', fontdict = dict(fontweight='bold'))
        ax.set_xlabel(r'time (t)', fontdict = dict(fontweight='bold', fontsize = 'large'))
        ax.set_ylabel(r'voltage (V)', fontdict = dict(fontweight='bold', fontsize = 'large'))

        ax.plot(time_pwr, voltage_pwr)
        #ax.plot(voltage_dmm, time_dmm)
        return ax