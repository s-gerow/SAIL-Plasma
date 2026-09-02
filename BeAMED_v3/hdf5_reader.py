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

    def is_open(self):
        return self.open

    def open_file(self, filepath: Path | str):
        if os.path.exists(self._save_dir/filepath):
            print(f"Successfully opened file: {self._save_dir/filepath}")
        else:
            print(f"Failed to open file {self._save_dir/filepath}. Does not exist")
            return
        self.filepath = Path(filepath)
        self.open = True

    def close_file(self):
        if self.open:
            self.filepath = None
            self.open = False
        return

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
            return list(f['discharges'])

    def get_discharge_group(self):
        if not self.open:
            return
        with h5py.File(self._save_dir/self.filepath, mode='r') as f:
            return f['discharges']
    
    def get_paschen_data(self):
        # ['current_pwr', 'current_pwr_err', 'gap_cm', 'gap_err', 'pd_kjl_err', 'pd_mks_err', 'pressure_kjl', 'pressure_kjl_err', 'pressure_mks', 'pressure_mks_err', 'source', 'voltage_dmm', 'voltage_dmm_err', 'voltage_pwr', 'voltage_pwr_err']
        if not self.open:
            return
        vcr_pwr = []
        vcr_dmm = []
        pd_kjl = []
        pd_mks = []
        vcr_pwr_err = []
        vcr_dmm_err = []
        pd_kjl_err = []
        pd_mks_err = []
        with h5py.File(self._save_dir/self.filepath, mode='r') as f:
            for key in f['discharges']:
                vcr_dmm.append(f['discharges'][key]['critical data'].attrs['voltage_dmm'])
                vcr_dmm_err.append(f['discharges'][key]['critical data'].attrs['voltage_dmm_err'])
                vcr_pwr.append(f['discharges'][key]['critical data'].attrs['voltage_pwr'])
                vcr_pwr_err.append(f['discharges'][key]['critical data'].attrs['voltage_pwr_err'])
                pd_mks.append(f['discharges'][key]['critical data'].attrs['pressure_mks']*f['discharges'][key]['critical data'].attrs['gap_cm'])
                pd_mks_err.append(f['discharges'][key]['critical data'].attrs['pd_mks_err'])
                pd_kjl.append(f['discharges'][key]['critical data'].attrs['pressure_kjl']*f['discharges'][key]['critical data'].attrs['gap_cm'])
                pd_kjl_err.append(f['discharges'][key]['critical data'].attrs['pd_kjl_err'])
        return ((vcr_pwr, vcr_pwr_err), (vcr_dmm, vcr_dmm_err), (pd_mks, pd_mks_err), (pd_kjl, pd_kjl_err))

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