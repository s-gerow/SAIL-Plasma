from tkinter import ttk
import tkinter as tk
import nidaqmx
import nidaqmx.constants
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from threading import Thread, Event, Lock
import time

class MFCWindow(tk.Tk):
    def __init__(self, screenName = None, baseName = None, className = "mfc window", useTk = True, sync = False, use = None):
        super().__init__(screenName, baseName, className, useTk, sync, use)
        
        self.protocol('WM_DELETE_WINDOW', lambda: self.clean_exit())

        self.daqLock = Lock()
        self.tkLock = Lock()

        self.measure = Event()
        self.stop = Event()

        #tasks for controlling inputs and outputs
        self.ao_task = nidaqmx.Task()
        self.ai_task = nidaqmx.Task()
        #do_task = nidaqmx.Task() #I do not think that this will be needed

        #assign daq channels
        self.ao_task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao0", name_to_assign_to_channel="SetPointInput", min_val=0, max_val=5)
        self.ai_task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai3", name_to_assign_to_channel="ValveTestPoint", min_val=0, max_val=5, terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
        self.ai_task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai7", name_to_assign_to_channel="FlowSignal", min_val=0, max_val=5, terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
        #do_task.do_channels.add_do_chan("NI_DAQ/port1/line0", name_to_assign_to_lines="ValveOpen")
        #do_task.do_channels.add_do_chan("NI_DAQ/port1/line1", name_to_assign_to_lines="ValveClose")
        self.ai_task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", name_to_assign_to_channel= "KJLPressure", min_val=0, max_val=10, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF)

        #set input settings
        self.ai_task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=100)

        #do_task.channels.do_output_drive_type = nidaqmx.constants.DigitalDriveType.ACTIVE_DRIVE
        self.plotFrame = tk.LabelFrame(self, text="GE50A I/O Plot")
        self.plotFrame.grid(row=0, column=0)

        #make plot to display data
        figure = Figure(dpi=75)
        self.figure_canvas = FigureCanvasTkAgg(figure, self.plotFrame)
        NavigationToolbar2Tk(self.figure_canvas,self.plotFrame).pack(side='top')
        self.axes = figure.add_subplot()
        self.axes.set_title('MFC I/O Plot')
        self.axes.set_ylabel('Voltage')
        self.axes.set_xlabel('Time')
        self.figure_canvas.get_tk_widget().pack(side='top')

        self.variableFrame = tk.LabelFrame(self, text="GE50A Control")
        self.variableFrame.grid(column=1, row=0)
        self.tksetPointInput = tk.DoubleVar()
        tk.Label(self.variableFrame, text = "Set Point Input (0-5 VDC)").grid(row=0,column=0)
        tk.Spinbox(self.variableFrame,
                        from_=0,
                        to = 5,
                        textvariable=self.tksetPointInput
                        ).grid(row=1, column=0)
        self.tkvalveTestPoint = tk.DoubleVar()
        tk.Label(self.variableFrame, text="Valve Test Point Output (0-5VDC)").grid(row=2,column=0)
        tk.Spinbox(self.variableFrame,
                        from_=0,
                        to = 5,
                        textvariable=self.tkvalveTestPoint
                        ).grid(row=3, column=0)
        self.tkflowSignalOutput = tk.DoubleVar()
        tk.Label(self.variableFrame, text="Flow Signal Output (0-5VDC)").grid(row=4,column=0)
        tk.Spinbox(self.variableFrame,
                        from_=0,
                        to = 5,
                        textvariable=self.tkflowSignalOutput
                        ).grid(row=5, column=0)
        self.tkpressure = tk.DoubleVar()
        tk.Label(self.variableFrame, text="Pressure (Torr)").grid(row=6,column=0)
        tk.Spinbox(self.variableFrame,
                        from_=0,
                        to = 5,
                        textvariable=self.tkpressure
                        ).grid(row=7, column=0)
        self.tkgas = tk.StringVar()
        tk.Label(self.variableFrame, text="Gas").grid(row=8,column=0)
        tk.Spinbox(self.variableFrame,
                        values=['N2','Ar'],
                        textvariable=self.tkgas
                        ).grid(row=9, column=0)
        tk.Button(self.variableFrame, text="Start Monitoring", command=lambda: self.start_measure()).grid(row=10,column=0)
        tk.Button(self.variableFrame, text='Stop Monitoring', command=lambda: self.stop_measure()).grid(row=11,column=0)

        #making data storage arrays
        self.dataframe = pd.DataFrame()
        self.valveTestPoint = []
        self.flowSignalOutput = []
        self.pressureKJL = []
        self.pressureVoltage = []
        self.setPointInput = []
        self.time = []

    def clean_exit(self):
        '''clean_exit() is used by the parent menu to intercept the "X' button at the top right and ensure that all 
        threads and open processes are closed before the UI quits'''
        self.ai_task.close()
        self.ao_task.close()
        self.destroy()

    def start_measure(self):
        self.stop.clear()
        self.valveTestPoint.clear()
        self.flowSignalOutput.clear()
        self.pressureKJL.clear()
        self.pressureVoltage.clear()
        self.setPointInput.clear()
        self.time.clear()
        measure_thread = Thread(target=lambda: self.measure_daq(), daemon=True)
        measure_thread.start()

    def stop_measure(self):
        self.stop.set()

    def measure_daq(self):
        if self.measure.is_set():
            pass
        else:
            self.measure.set()
        start_time = time.time()
        while(self.measure.is_set()):
            with self.tkLock:
                setpoint = float(self.tksetPointInput.get())
            with self.daqLock:
                valveTest_voltage, flowSignal_voltage, pressure_voltage = self.ai_task.read(10)
                valveTest_unfiltered_avg = np.median(valveTest_voltage)
                flowSignal_unfiltered_avg = np.median(flowSignal_voltage)
                pressure_unfiltered_avg = np.median(pressure_voltage)
                self.ao_task.write(setpoint, auto_start = True, timeout=1)
            match self.tkgas.get():
                case 'N2':
                    true_pressure = 10**(pressure_unfiltered_avg - 5)
                case 'Ar':
                    true_pressure = 10**(pressure_unfiltered_avg - 5) #fix this, find correct conversion factor
            with self.tkLock:
                self.after(1, self.tkpressure.set(true_pressure))
                self.after(1, self.tkflowSignalOutput.set(flowSignal_unfiltered_avg))
                self.after(1, self.tkvalveTestPoint.set(valveTest_unfiltered_avg))
            self.pressureKJL.append(true_pressure)
            self.pressureVoltage.append(pressure_unfiltered_avg)
            self.time.append(time.time())
            self.setPointInput.append(setpoint)
            self.valveTestPoint.append(valveTest_unfiltered_avg)
            self.flowSignalOutput.append(flowSignal_unfiltered_avg)
            self.update_plot(start_time)
            if self.stop.is_set():
                self.measure.clear()
                return
            
    def update_plot(self, start_time):
        self.axes.clear()
        time_axis = np.array(self.time)-start_time
        pressure = np.array(self.pressureVoltage)
        valve_test = np.array(self.valveTestPoint)
        set_point = np.array(self.setPointInput)
        flow_signal = np.array(self.flowSignalOutput)

        self.axes.plot(time_axis, pressure, label = "Pressure Output (V)")
        self.axes.plot(time_axis, valve_test, label = "Valve Test Point (V)")
        self.axes.plot(time_axis, flow_signal, label = "Flow Signal Output (V)")
        self.axes.plot(time_axis, set_point, label = "Set Point Input (V)")
        self.axes.set_title('Discharge Plot')
        self.axes.set_ylabel('Voltage (V)')
        self.axes.set_xlabel('Time (s)')
        self.axes.legend()

        self.figure_canvas.draw()



if __name__ == "__main__":
    chamber = MFCWindow()

    chamber.mainloop()