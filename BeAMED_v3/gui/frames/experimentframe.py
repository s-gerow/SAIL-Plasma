import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

from threadcontroller import Controller, ActionResult


class ExperimentControlFrame:
    def __init__(self, parent, controller: Controller):
        self._parent = parent
        self.controller = controller
        self.logger = logging.getLogger("BeAMED.gui.control")

        self._input_frame = ExperimentInputFrame(self._parent, self)
        self._output_frame = ExperimentOutputFrame(self._parent, self)

    @property
    def input_frame(self) -> tk.LabelFrame:
        return self._input_frame
    
    @property
    def output_frame(self) -> tk.LabelFrame:
        return self._output_frame
    
class ExperimentInputFrame(tk.LabelFrame):
    def __init__(self, parent, exp_controller):
        super().__init__(parent, text="Experiment Input")
        self.exp_controller = exp_controller
        self._input_vars: dict[str, tk.Variable] = {}

        self._build()

    def _build(self):
        input_col = tk.Frame(self)
        input_col.pack(fill="both", expand=True,side="top")
        input_col.columnconfigure(0,weight=1)
        input_col.columnconfigure(1,weight=1)
        
        # Power Supply Set-Up
        row_num = 0
        tk.Label(input_col, text="Power Set-Up").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Label(input_col, text="Starting Input Voltage (V)").grid(row=row_num, column=0)
        self._input_vars["pwr_volt_start"] = tk.DoubleVar(value=0.0)
        ttk.Spinbox(input_col, 
                    textvariable=self._input_vars["pwr_volt_start"],
                    from_=0,
                    to=500,
                    increment=0.5).grid(row=row_num,column=1)
        row_num += 1
        
        tk.Label(input_col, text="Current Output Limit (0.5 A)").grid(row=row_num, column=0)
        self._input_vars["pwr_curr_lim"] = tk.DoubleVar(value=0.5)
        ttk.Spinbox(input_col, 
                    textvariable=self._input_vars["pwr_curr_lim"],
                    from_=0,
                    to=1,
                    increment=0.05).grid(row=row_num,column=1)
        row_num += 1
        
        # Electrode
        tk.Label(input_col, text="Electrode Set-Up").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Label(input_col, text="Electrode Position (cm)").grid(row=row_num, column=0)
        self._input_vars["feedthrough_pos"] = tk.DoubleVar(value=0.5)
        ttk.Spinbox(input_col, 
                    textvariable=self._input_vars["feedthrough_pos"],
                    from_=0,
                    to=2,
                    increment=0.1).grid(row=row_num,column=1)
        row_num += 1
        
        tk.Label(input_col, text="Anode Material").grid(row=row_num, column=0)
        self._input_vars["anode_mat"] = tk.StringVar(value="Al 6061")
        ttk.Combobox(input_col, 
                    textvariable=self._input_vars["anode_mat"],
                    values=["Al 6061"]
                    ).grid(row=row_num,column=1)
        row_num += 1
        
        tk.Label(input_col, text="Cathode Material").grid(row=row_num, column=0)
        self._input_vars["cathode_mat"] = tk.StringVar(value="Al 6061")
        ttk.Combobox(input_col, 
                    textvariable=self._input_vars["cathode_mat"],
                    values=["Al 6061"]
                    ).grid(row=row_num,column=1)
        row_num += 1
        
        # Pressure
        tk.Label(input_col, text="Pressure Set-Up").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Label(input_col, text="Pressure Min (Torr)").grid(row=row_num, column=0)
        self._input_vars["pressure_min"] = tk.DoubleVar(value=0.1)
        ttk.Spinbox(input_col, 
                    textvariable=self._input_vars["pressure_min"],
                    from_=0.1,
                    to=10,
                    increment=0.1).grid(row=row_num,column=1)
        row_num += 1

        tk.Label(input_col, text="Pressure Max (Torr)").grid(row=row_num, column=0)
        self._input_vars["pressure_max"] = tk.DoubleVar(value=10)
        ttk.Spinbox(input_col, 
                    textvariable=self._input_vars["pressure_max"],
                    from_=0.1,
                    to=10,
                    increment=0.1).grid(row=row_num,column=1)
        row_num += 1

        tk.Label(input_col, text="Number of Discharges").grid(row=row_num, column=0)
        self._input_vars["num_discharges"] = tk.DoubleVar(value=1)
        ttk.Spinbox(input_col, 
                    textvariable=self._input_vars["num_discharges"],
                    from_=1,
                    to=50,
                    increment=1).grid(row=row_num,column=1)
        row_num += 1
        
        tk.Label(input_col, text="Gas Species").grid(row=row_num, column=0)
        self._input_vars["gas_species"] = tk.StringVar(value="Air")
        ttk.Combobox(input_col, 
                    textvariable=self._input_vars["gas_species"],
                    values=["Air", "Ar", "CO2", "He", "N2"]
                    ).grid(row=row_num,column=1)
        row_num += 1

        # Control Panel
        tk.Label(input_col, text="Control Panel").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(input_col, text="Configure Series").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(input_col, text="Start Series").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(input_col, text="Pause Series").grid(row=row_num, column=0, columnspan=2)
        row_num += 1
        tk.Button(input_col, text="Abort Series").grid(row=row_num, column=0, columnspan=2)
        

        

class ExperimentOutputFrame(tk.LabelFrame):
    def __init__(self, parent, exp_controller):
        super().__init__(parent, text="Experiment Ouput")
        self.exp_controller = exp_controller
        self._output_names = (("pwr_volt_out", "Power Supply Voltage (V)"), 
                             ("pwr_curr_out", "Power Supply Current (A)"),
                             ("dmm_volt_out", "DMM Voltage Output (V)"),
                             ("target_pressure", "Target Pressure (Torr)"),
                             ("kjl_pressure", "KJL Discharge Pressure (Torr)"),
                             ("mks_pressure", "MKS Discharge Pressure (Torr)"),
                             ("osc_dv", "Oscilloscope Trigger (V)"),
                             ("trigger_method", "Trigger Method"),
                             )
        self._output_vars: dict[str, tk.Variable] = {} 

        self._build()

    def _build(self):
        output_col = tk.Frame(self)
        output_col.pack(fill="both", expand=True, side="top")
        for i, (var, name) in enumerate(self._output_names):
            self._output_vars[var] = tk.DoubleVar(value=0.0)
            tk.Label(output_col, text=name).grid(row=i, column=0)
            tk.Label(output_col, text=f"{self._output_vars[var].get():.3f}").grid(row=i, column=1)


