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
from scipy import interpolate as interp

class MFCWindow(tk.Tk):
    def __init__(self, screenName = None, baseName = None, className = "mfc window", useTk = True, sync = False, use = None):
        super().__init__(screenName, baseName, className, useTk, sync, use)

        pressure = np.array([0.0001,0.0002,0.0005,0.001,0.002,0.005,0.01,0.02,0.05,0.1,0.2,0.5,1,2,5,10,20,50,100,200,300,400,500,600,700,760,800,900,1000])
        log10pressure = np.log10(pressure)
        ar = np.array([1, 1.301, 1.699, 1.845, 2.146, 2.519, 2.82, 3.117, 3.511, 3.808, 4.1, 4.494, 4.778, 5.057, 5.389, 5.602, 5.763, 5.895, 5.946, 5.991, 6.053, 6.13, 6.207, 6.274, 6.338, 6.375, 6.4, 6.455, 6.512])
        self.arVtoP = interp.CubicSpline(ar, log10pressure, bc_type='natural',extrapolate=True)



        self.protocol('WM_DELETE_WINDOW', lambda: self.clean_exit())

        self.daqLock = Lock()
        self.tkLock = Lock()

        self.measure = Event()
        self.pid = Event()
        self.stop = Event()
        self.stoppid = Event()

        #tasks for controlling inputs and outputs
        self.ao_task = nidaqmx.Task()
        self.ai_task = nidaqmx.Task()
        self.do_task = nidaqmx.Task() #I do not think that this will be needed

        #assign daq channels
        self.ao_task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao1", name_to_assign_to_channel="SetPointOutput", min_val=0, max_val=5)
        self.ai_task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", name_to_assign_to_channel= "KJLPressure", min_val=0, max_val=10, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF)
        self.ai_task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai1", name_to_assign_to_channel= "MKSPressure", min_val=0, max_val=10, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF)
        self.ai_task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai3", name_to_assign_to_channel="FlowSignalInput", min_val=0, max_val=10, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF)
        self.do_task.do_channels.add_do_chan("NI_DAQ/port0/line1", name_to_assign_to_lines="ValveOpen")
        self.do_task.do_channels.add_do_chan("NI_DAQ/port0/line0", name_to_assign_to_lines="ValveClose")


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
        #self.axes.set_title('MFC I/O Plot')
        self.axes.set_ylabel('Pressure (Torr)')
        self.axes.set_xlabel('Time (s)')

        self.axes2 = self.axes.twinx()
        self.axes2.set_ylabel('Voltage (V)')
        figure.tight_layout()
        self.figure_canvas.get_tk_widget().pack(side='top')

        self.variableFrame = tk.LabelFrame(self, text="GE50A Control")
        self.variableFrame.grid(column=1, row=0)
        self.tksetPointInput = tk.DoubleVar()
        
        tk.Label(self.variableFrame, text = "Flow Point Input (0-5 VDC)").grid(row=0,column=0)
        tk.Spinbox(self.variableFrame,
                        from_=0,
                        to = 5,
                        textvariable=self.tksetPointInput
                        ).grid(row=1, column=0)
        
        self.tkmkspressure = tk.DoubleVar()
        tk.Label(self.variableFrame, text="MKS Pressure").grid(row=2,column=0)
        tk.Spinbox(self.variableFrame,
                        from_=0,
                        to = 5,
                        textvariable=self.tkmkspressure
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
        tk.Button(self.variableFrame, text='Vent Chamber',command=lambda: self.control_valve('vent')).grid(row=12,column=0)
        tk.Button(self.variableFrame, text='Pump Chamber',command=lambda: self.control_valve('pump')).grid(row=13,column=0)
        tk.Button(self.variableFrame, text='Close Valves',command=lambda: self.control_valve('stop')).grid(row=14,column=0)

        self.tkpressureSetPoint = tk.DoubleVar(value=1)
        tk.Label(self.variableFrame, text = "Pressure Set Point (Torr)").grid(row=0, column=1)
        tk.Spinbox(self.variableFrame,
                   from_=0,
                   to=10,
                   textvariable=self.tkpressureSetPoint).grid(row=1,column=1)
        
        self.tkKp = tk.DoubleVar(value=0.115*0.6)
        self.tkKi = tk.DoubleVar(value=0.5*0.4)
        self.tkKd = tk.DoubleVar(value=0.4/8)
        tk.Label(self.variableFrame, text="K_p").grid(row=2,column=1)
        tk.Spinbox(self.variableFrame,
                   textvariable=self.tkKp).grid(row=3,column=1)
        tk.Label(self.variableFrame, text="K_i").grid(row=4,column=1)
        tk.Spinbox(self.variableFrame,
                   textvariable=self.tkKi).grid(row=5,column=1)
        tk.Label(self.variableFrame, text="K_d").grid(row=6,column=1)
        tk.Spinbox(self.variableFrame,
                   textvariable=self.tkKd).grid(row=7,column=1)
        
        tk.Button(self.variableFrame, text='Enable Control',command=lambda:self.start_pid()).grid(row=8, column=1)
        tk.Button(self.variableFrame, text='Disable Control',command=lambda:self.stop_pid()).grid(row=9, column=1)

        #making data storage arrays
        self.dataframe = pd.DataFrame()
        self.flowSignalVoltage = []
        self.KJLvoltage = []
        self.MKSvoltage = []
        self.setPointVoltage = []
        self.time = []
        self.starttime = 0

        self.pressure_min = 0.11 #Torr #MKS Sensor
        self.pressure_max = 10 #Torr #MKS Sensor

    def argonVoltage2Pressure(self,V):
        logp = self.arVtoP(V)
        return 10**logp
    
    def clean_exit(self):
        '''clean_exit() is used by the parent menu to intercept the "X' button at the top right and ensure that all 
        threads and open processes are closed before the UI quits'''
        self.ai_task.close()
        self.ao_task.close()
        self.do_task.close()
        self.destroy()

    def pid_controller(self, setpoint, pv, kp, ki, kd, prev_error, integral, dt):
        volume = V = 45.30695
        error = setpoint - pv
        integral += error * dt
        derivative = (error - prev_error) / dt
        control = kp * error + ki *integral + kd * derivative
        control_mod = (control*V)*(1.333224)*(1/0.0168875)*(5/100) #V
        control_clamp = max(0.0, min((5.0, control_mod)))
        return control_clamp, error, integral
    
    def start_pid(self):
        if self.pid.is_set():
            pass
        else:
            self.pid.set()
        self.error = 0
        self.integral = 0

    def stop_pid(self):
        self.pid.clear()

    def start_measure(self):
        self.stop.clear()
        self.flowSignalVoltage.clear()
        self.KJLvoltage.clear()
        self.MKSvoltage.clear()
        self.setPointVoltage.clear()
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
        self.starttime = time.time()
        while(self.measure.is_set()):
            with self.tkLock:
                setpoint = float(self.tksetPointInput.get())
                if self.pid.is_set():
                    pressure_setpoint = float(self.tkpressureSetPoint.get())
                    kp = float(self.tkKp.get())
                    ki = float(self.tkKi.get())
                    kd = float(self.tkKd.get())
            with self.daqLock:
                kjlpressure_voltage, mkspressure_voltage, flowSignal_voltage = self.ai_task.read(10) #, flowSignal_voltage
                flowSignal_unfiltered_avg = np.median(flowSignal_voltage)
                kjlpressure_unfiltered_avg = np.median(kjlpressure_voltage)
                mkspressure_unfiltered_avg = np.median(mkspressure_voltage)
                read_time = time.time()
                # if len(self.time)>=1:
                #     print(read_time-self.time[-1])
            match self.tkgas.get():
                case 'N2':
                    true_pressure = 10**(kjlpressure_unfiltered_avg - 5)
                    new_true_pressure = (mkspressure_unfiltered_avg/10)*(self.pressure_max-self.pressure_min)+self.pressure_min

                case 'Ar':
                    print("ar")
                    print(kjlpressure_unfiltered_avg)
                    ar2_pressure = 10**(kjlpressure_unfiltered_avg - 5) #fix this, find correct conversion factor
                    true_pressure = self.argonVoltage2Pressure(kjlpressure_unfiltered_avg)
                    print(ar2_pressure)
                    print(true_pressure)

            if self.pid.is_set() and len(self.time)>=1:
                control, self.error, self.integral = self.pid_controller(pressure_setpoint, new_true_pressure, kp, ki, kd, self.error, self.integral, read_time-self.time[-1])
            else:
                control = setpoint
            with self.daqLock:
                self.ao_task.write(control, auto_start = True, timeout=1)
            with self.tkLock:
                self.after(0, self.tksetPointInput.set(control))
                self.after(0, self.tkpressure.set(true_pressure))
                self.after(0, self.tkflowSignalOutput.set(flowSignal_unfiltered_avg))
                self.after(0, self.tkmkspressure.set(new_true_pressure))
            self.KJLvoltage.append(true_pressure)
            self.MKSvoltage.append(new_true_pressure)
            self.time.append(time.time())
            self.setPointVoltage.append(setpoint)
            self.flowSignalVoltage.append(flowSignal_unfiltered_avg)

            self.update_plot(self.time[0])
            if self.stop.is_set():
                self.measure.clear()
                return
            
    def update_plot(self, start_time):
        self.axes.clear()
        self.axes2.clear()
        if len(self.time) >= 600:
            time_axis = (np.array(self.time)-start_time)[-600:]
            kjlpressure = np.array(self.KJLvoltage)[-600:]
            set_point = np.array(self.setPointVoltage)[-600:]
            flow_signal = np.array(self.flowSignalVoltage)[-600:]
            mkspressure = np.array(self.MKSvoltage)[-600:]
        else:
            time_axis = (np.array(self.time)-start_time)
            kjlpressure = np.array(self.KJLvoltage)
            set_point = np.array(self.setPointVoltage)
            flow_signal = np.array(self.flowSignalVoltage)
            mkspressure = np.array(self.MKSvoltage)
        self.axes.plot(time_axis, kjlpressure, label = "KJL Pressure (Torr) [ai0]")
        self.axes.plot(time_axis, mkspressure, label = "MKS Pressure (Torr) [ai1]")
        self.axes2.plot(time_axis, flow_signal, label = "MKS Flow Signal Output (V) [ai3]", color='xkcd:red')
        self.axes2.plot(time_axis, set_point, label = "Set Point Input (V) [ao1]", color = 'xkcd:green')
        self.axes.set_ylim(top=max(kjlpressure)*1.5)
        self.axes2.set_ylim((-0.25,5.25))
        #self.axes.set_title('MFC I/O Plot')
        self.axes.set_ylabel('Pressure (Torr)')
        self.axes2.set_ylabel('Voltage (V)')
        self.axes.set_xlabel('Time (s)')
        #self.axes.set_xlim(0, 30)
        self.axes2.legend(loc='upper center', bbox_to_anchor=(0.5,1.05), ncol=2, fancybox=True, shadow=True)
        self.axes.legend(loc='upper center', bbox_to_anchor=(0.5,0.98), ncol=2, fancybox=True, shadow=True)
        self.axes.spines['top'].set_visible(False)
        self.axes2.spines['top'].set_visible(False)
        self.figure_canvas.draw()
    
    def control_valve(self, arg:str):
        with self.daqLock:
            match arg:
                case 'vent':
                    self.do_task.write([False,True],auto_start=True,timeout=3)
                    return
                case 'pump':
                    self.do_task.write([True,False],auto_start=True,timeout=3)
                    return
                case 'stop':
                    self.do_task.write([False,False],auto_start=True,timeout=3)
                    return
                case _:
                    return



if __name__ == "__main__":
    chamber = MFCWindow()

    chamber.mainloop()