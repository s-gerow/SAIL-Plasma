from ChamberGUIBuilder import *

class Experiment():
    def __init__(self, parent: ChamberApp):
        self.parent = parent
        self.logger = logging.getLogger('BeAMED')
        self.rm = parent.rm
        self.Pwr = None
        self.v_out = None
        self.auto_range = None
        self.StopALL = Event()
        self.isExperimentStarted = Event()
        self.isPowerConfigured = Event()
        self.isDmmConfigured = Event()
        self.isFeedthroughset = Event()
        parent.geometry('800x500')
        parent.title("BeAMED DEMO")

        #_________________Configure Experiment Frame________________________________#
        parent.experimentFrame.grid_columnconfigure(0, weight=1)
        parent.experimentFrame.grid_columnconfigure(1, weight=1)
        parent.experimentFrame.grid_columnconfigure(2, weight=1)
        parent.experimentFrame.grid_columnconfigure(3, weight=1)
        parent.experimentFrame.grid_columnconfigure(4, weight=1)

        #Frame to take device inputs
        device_opt_frame = tk.Frame(parent.experimentFrame)
        device_opt_frame.grid(row=0, column=0)
        
        tk.Label(device_opt_frame, text = 'VISA Power').grid(row=0, column=0)
        self.pwr_cbox = ttk.Combobox(device_opt_frame, state = 'readonly', values = self.check_IO())
        self.pwr_cbox.bind('<<ComboboxSelected>>', lambda event: self.update_combo_box(event, self.pwr_cbox))
        self.pwr_cbox.grid(row =0, column=1)
        
        tk.Label(device_opt_frame, text = 'VISA DMM').grid(row=1,column=0)
        self.dmm_cbox = ttk.Combobox(device_opt_frame, state = 'readonly', values = self.check_IO())
        self.dmm_cbox.bind('<<ComboboxSelected>>', lambda event: self.update_combo_box(event, self.dmm_cbox))
        self.dmm_cbox.grid(row=1,column=1)

        #Frame for pre-configs ( Auto Range, V_out, etc)
        enabledisable_frame = tk.Frame(parent.experimentFrame)
        enabledisable_frame.grid(row=0,column=1)
        #Button appearance
        self.true_image = tk.PhotoImage(width=15, height=15)
        self.false_image = tk.PhotoImage(width=15, height = 15)
        self.true_image.put(("lime"), to=(0,0,14,14))
        self.false_image.put(("green"), to=(0,0,14,14))
        
        self.trig_true_image = tk.PhotoImage(width=50, height=50)
        self.trig_false_image = tk.PhotoImage(width=50, height=50)
        self.trig_true_image.put(("lime"), to=(0,0,49,49))
        self.trig_false_image.put(("green"), to=(0,0,49,49))

        self.auto_range_var = tk.StringVar(value = "Disable")
        tk.Label(enabledisable_frame, text = 'Auto Range DMM (T: Enable)').grid(row=2 )
        self.auto_button = tk.Checkbutton(enabledisable_frame, 
                                    text = 'T: Enable',
                                    variable=self.auto_range_var,
                                    image = self.false_image, 
                                    selectimage = self.true_image, 
                                    indicatoron = False, 
                                    compound= 'left',
                                    onvalue="Enable",
                                    offvalue="Disable",
                                    command = lambda: self.toggle_check_btn(self.auto_button, self.auto_range_var))
        self.auto_button.grid(row=3 )
        
        self.v_out_var = tk.StringVar(value = "Disable")
        tk.Label(enabledisable_frame, text = 'Enable V-Output Power (T: Enable)').grid(row=4 )
        self.vout_button = tk.Checkbutton(enabledisable_frame, 
                                text = 'T:Enable',
                                image = self.false_image, 
                                selectimage = self.true_image, 
                                indicatoron = False, 
                                compound= 'left',
                                variable = self.v_out_var,
                                onvalue="Enable",
                                offvalue="Disable",
                                command = lambda: self.toggle_check_btn(self.vout_button, self.v_out_var))
        self.vout_button.grid(row=5 )
        #Frame for initial conditions (voltage, current, electrode position)
        experimentCondysFrame = tk.Frame(parent.experimentFrame)
        experimentCondysFrame.grid(row=0, column=2)

        self.init_v_var = tk.StringVar(value = '0')
        tk.Label(experimentCondysFrame,
                text = "Input Voltage (V)",
                ).grid(row=0)
        ttk.Spinbox(experimentCondysFrame,
                    from_ = 0,
                    to = 100000,
                    textvariable=self.init_v_var
                    ).grid(row=1)

        self.init_current_var = tk.StringVar(value = '0')
        tk.Label(experimentCondysFrame,
                text = "Current Level (0.5A)").grid(row=2)
        ttk.Spinbox(experimentCondysFrame,
                    from_ = 0,
                    to = 1000000,
                    textvariable = self.init_current_var
                    ).grid(row=4)
        #Position of the plates
        self.plate_pos_var = tk.StringVar()
        ttk.Spinbox(experimentCondysFrame,
                    from_=-10,
                    to=10,
                    textvariable=self.plate_pos_var,
                    state='disabled'
                    ).grid(row=6)
        tk.Label(experimentCondysFrame,
                                text = "Plate Position (cm)").grid(row=5)
        tk.Label(experimentCondysFrame,
                text = "Electrode Position (cm)").grid(row=7)
        self.electrode_pos_var = tk.StringVar(value=0)
        ttk.Spinbox(experimentCondysFrame,
                    from_=-10,
                    to=10,
                    increment=0.5,
                    textvariable=self.electrode_pos_var
                    ).grid(row=8)
        #Frame for displaying Data (pressure, voltage,)
        experimentOutputFrame = tk.Frame(parent.experimentFrame)
        experimentOutputFrame.grid(row=0, column=3)

        tk.Label(experimentOutputFrame,
                            text = "Power Supply Voltage").grid(row = 0)
        tk.Label(experimentOutputFrame,
                             text = "Power Supply Current").grid(row=2)
        tk.Label(experimentOutputFrame,
                        text = "Voltage Output").grid(row=4)
        tk.Label(experimentOutputFrame,
                        text = "Pressure (Torr)").grid(row=6)
        self.PS_voltage_var = tk.DoubleVar()
        tk.Spinbox(experimentOutputFrame,
                        from_=0,
                        to = 800,
                        textvariable=self.PS_voltage_var
                        ).grid(row=1)
        self.PS_current_var = tk.DoubleVar()
        tk.Spinbox(experimentOutputFrame,
                        from_=0,
                        to = 800,
                        textvariable=self.PS_current_var
                        ).grid(row=3)
        self.voltage_out_var = tk.DoubleVar()
        tk.Spinbox(experimentOutputFrame,
                        from_=0,
                        to = 800,
                        textvariable=self.voltage_out_var
                        ).grid(row=5)
        self.pressure_var = tk.DoubleVar()
        tk.Spinbox(experimentOutputFrame,
                        from_=0,
                        to = 800,
                        textvariable=self.pressure_var
                        ).grid(row=7)
        #Frame for start and stop buttons
        experimentControlFrame = tk.Frame(parent.experimentFrame)
        experimentControlFrame.grid(row=0, column=4)
        ttk.Button(experimentControlFrame, text = 'START', command=self.run_experiment).grid(row=0)
        ttk.Button(experimentControlFrame, text = 'STOP',command=self.clean_exit).grid(row=1)


    #______________________________Experiment Control Functions________________________________#
    def clean_exit(self):
            '''clean_exit() is used by the parent menu to intercept the "X' button at the top right and ensure that all 
            threads and open processes are closed before the UI quits'''
            level = "INFO"
            thread = "MAIN"
            self.log_message(thread, level, f"Quitting Application. Cleaning up loose threads.")
            self.StopALL.set()
            if isinstance(self.Pwr, VisaDevice):
                self.log_message(thread, level, f"Closing {self.Pwr.name}")
                self.Pwr.open_device()
                self.Pwr.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
                self.Pwr.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")
                self.Pwr.resource.write("OUTP:STAT:IMM OFF")
                self.Pwr.close_device()
            if isinstance(self.Dmm, VisaDevice):
                self.log_message(thread,level, f"Closing {self.Dmm.name}")
                self.Dmm.close_device()
            self.parent.destroy()

    def start_log(self):
        '''start_log() initlizes the logger into a file called debug.log which will record events for the experiment'''
        handler = logging.FileHandler('debug.log', mode = 'w')
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self.log_message("MAIN", "INFO", f"BeAMED Plasma Chamber DEMO debug log started")

    def log_message(self, thread, level, message):
        '''Adds a message to the debug file'''
        dt = datetime.now()
        self.logger.debug(f"{thread}: {dt.hour}:{dt.minute}:{dt.second}.{dt.microsecond} - {level} - {message}")


        #I/O selection for Oscilloscope, Power, and Digital Multimeter
    def check_IO(self):
        '''This method adds the resources from the pyvisa resource manager to the dropdown boxes'''
        IO_opts = ["Refresh"]
        for i in self.rm.list_resources():
            if self.rm.list_resources_info()[i][4] == None:
                IO_opts.append(i)
            else:
                IO_opts.append(self.rm.list_resources_info()[i][4])
        return IO_opts

    def update_combo_box(self, event, cbox_name):
        '''When a dropdown box is set to refresh, it will refresh all of the dropdown boxes to new values using check_IO()'''
        IO_opts = self.check_IO()
        # Update the combo box with new resources
        if cbox_name.get() == "Refresh":
            self.pwr_cbox['values'] = IO_opts
            self.dmm_cbox['values'] = IO_opts
            cbox_name.set("")
        else:
            self.parent.generate_configuration_frame(filename= cbox_name.get())

    def toggle_check_btn(self, btn, var):
        '''toggle_check_btn allows the check buttons to change their text when they are activated by clicking'''
        if var.get() == "Enable":
            btn.configure(text='T: Enable')
        elif var.get() == "Disable":
            btn.configure(text='F: Disable')

    def run_experiment(self):
        thread = "MAIN"
        level = "INFO"
        self.start_log()
        
        self.isExperimentStarted.set()
        self.isFeedthroughset.clear()
        '''This is the main experiment logic. In order to run, all configurations must be complete as declared by an event flag in run_experiment_configuration'''
        #First check to ensure voltage output is enabled and do not start the experiment if it is disabled
        if self.v_out_var.get() == "Disable":
            messagebox.showerror("Experiment Initilization Error", "Voltage Output Disabled.\nPlease enable voltage output then try again", icon=messagebox.ERROR)
            return
        if self.auto_range_var.get() == "Enable":
            self.auto_range = "ON"
        else:
            self.auto_range = "OFF"
        #Identify selected devices
        pwrName = self.pwr_cbox.get()
        dmmName = self.dmm_cbox.get()
        #configure devices based on the imported configurations
        self.parent.devices[pwrName][1].configureAll()
        self.parent.devices[dmmName][1].configureAll()
        #starts feedthrough zero
        self.Dmm = self.parent.devices[dmmName][0]
        target_position = float(self.electrode_pos_var.get())
        setFeedthrough = Thread(target = lambda: self.moveFeedthrough(target_position), daemon= True)
        setFeedthrough.start()
        while not self.isFeedthroughset.is_set():
            time.sleep(1)
        #waits until feedthrough is set to configure power supply.
        #Initilize threads to configure pyvisa devices
        dmmcfg = Thread(target = lambda: self.configureDMM(dmmName))
        pwrcfg = Thread(target = lambda: self.configurePower(pwrName))
        configurationThreads = [dmmcfg, pwrcfg]
        #Start configuration threads and wait for them to complete before continuing
        for thread in configurationThreads:
            self.log_message(thread, level,f"starting {thread} thread")
            thread.start()
        for thread in configurationThreads:
            thread.join()
        #Read Pressure
        self.log_message(thread, level, "Starting Continuous Pressure Reading")
        live_pressure = Thread(target = lambda: self.read_pressure(),daemon=True)
        live_pressure.start()
        #read voltage
        self.log_message(thread, level, "Starting Continuos Voltage Reading")
        live_dmm = Thread(target = lambda: self.readDmm(), daemon=True)
        live_dmm.start()
        #thread increases voltage at set rate 0.5V/3s
        init_v = float(self.init_v_var.get())
        init_c = float(self.init_current_var.get())
        v_increase = Thread(target = lambda: self.increase_voltage(init_v, init_c))
        v_increase.start()
        
    def configurePower(self, pwrName):
        thread = "CFG-PWR"
        level = "INFO"
        self.log_message(thread, level, f"configuring{pwrName}")
        self.Pwr = self.parent.devices[pwrName][0]
        self.Pwr.open_device()
        self.Pwr.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
        self.Pwr.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")
        self.Pwr.close_device()
        self.log_message(thread, level, f"{pwrName} Successfully Confirgured")
        self.isPowerConfigured.set()
        
    def configureDMM(self, dmmName):
        thread = "CFG-DMM"
        level = "INFO"
        self.log_message(thread, level, f"configuring{dmmName}")
        
        
        self.Dmm.open_device()
        self.Dmm.resource.write("*RST")
        self.Dmm.resource.write(f":SENS:FUNC '{self.Dmm.options['Function'][0]}'")
        func = self.Dmm.options['Function'][0][:4]
        self.Dmm.resource.write(f"SENS:{func}:RANG:AUTO {self.auto_range}")
        self.Dmm.resource.write(f":SENS:{func}:NPLC 1") #Default 1
        self.Dmm.resource.write(f":SENS:{func}:LINE:SYNC OFF") #Default OFF
        self.Dmm.resource.write(f"SENS:{func}:AZER ON")#Default ON
        
        self.Dmm.resource.write(f"CALC2:{func}:LIM1:STAT {self.Dmm.options['Limit'][0]}") #Default OFF
        self.Dmm.resource.write(f"CALC2:{func}:LIM1:CLE:AUTO {self.Dmm.options['Limit'][0]}") #Limit Number in GUI is 1 (LIM_), Default ON
        self.Dmm.resource.write(f"CALC2:{func}:LIM1:LOW {self.Dmm.options['Lower Limit'][0]}") #Because the voltage limit is disabled this should not be needed but may as well include it because maybe one day we do
        self.Dmm.resource.write(f"CALC2:{func}:LIM1:UPP {self.Dmm.options['Upper Limit'][0]}")
        self.Dmm.resource.write(f"TRAC:FILL:MODE CONT, '{self.Dmm.options['Reading Buffer'][0]}'") #continuous fill
        self.Dmm.resource.write(f"TRAC:POIN {self.Dmm.options['Buffer Size'][0]}, '{self.Dmm.options['Reading Buffer'][0]}'") #Buffer Size 10
        
        self.Dmm.close_device()
        self.log_message(thread, level, f"{dmmName} Successfully Configured")
        self.isDmmConfigured.set()

    def readDmm(self):
        thread = "DMM"
        level = "INFO"
        self.Dmm.open_device()
        #self.Dmm.resource.write(':SENS:FUNC "VOLT:DC"')
        while(self.isExperimentStarted.is_set() & self.StopALL.is_set() == False):
            voltage = self.Dmm.resource.query(':READ?')
            self.parent.after(1, lambda: self.voltage_out_var.set(voltage))
        if(self.StopALL.is_set()):
            return
        
    def moveFeedthrough(self, target):
        #x is electrode postion * 3200 revolutions
        thread = 'FDTHR'
        level = "INFO"
        self.log_message(thread, level, "Zeroing Feedthrough")
        
        #dmmName = self.dmm_cbox.get()
        #self.auto_range="ON" ##comment out when implemented into regular operation
        #self.parent.devices[dmmName][1].configureAll()
        #self.configureDMM(dmmName)
        self.Dmm.open_device()
        self.Dmm.resource.write(':SENS:FUNC "CONT"')
        ohm = float(self.Dmm.resource.query(":READ?"))

        with nidaqmx.Task() as do_task:
            do_task._do_channels.add_do_chan("NI_DAQ/port0/line0")
            do_task._do_channels.add_do_chan("NI_DAQ/port0/line1")
            do_task.write([False,True],auto_start=True,timeout=10) 
            time.sleep(0.5)
            while ohm > 500:
                do_task.write([True,True],auto_start=True,timeout=10)
                time.sleep(.0000025)
                do_task.write([False,True],auto_start=True,timeout=10)
                time.sleep(0.0000025)
                #print("Direction Down")
                ohm = float(self.Dmm.resource.query(":READ?"))
            #switch direction
            do_task.write([False,False],auto_start=True,timeout=10) 
            time.sleep(0.5)
            for x in np.arange(0,target*3200,1):
                do_task.write([True,False],auto_start=True,timeout=10)
                time.sleep(.0000025)
                do_task.write([False,False],auto_start=True,timeout=10)
                time.sleep(0.0000025)
                #print("Direction Up")
                ohm = float(self.Dmm.resource.query(":READ?"))
        self.Dmm.close_device()
        self.isFeedthroughset.set()

    def increase_voltage(self, init_v: int, init_c: int):
        thread = "PWR"
        level = "INFO"
        self.Pwr.open_device()
        self.Pwr.resource.write("OUTP:STAT:IMM ON")
        voltage_step = float(self.Pwr.options["Voltage Step Size"][0])
        self.Pwr.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {init_c}")
        while(self.StopALL.is_set() == False & (float(self.Pwr.resource.query("SOUR:VOLT:LEV:IMM:AMPL?"))<600)):
            self.Pwr.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {init_v}")
            self.parent.after(1, lambda: self.PS_voltage_var.set(self.Pwr.resource.query("SOUR:VOLT:LEV:IMM:AMPL?")))
            self.parent.after(1, lambda: self.PS_current_var.set(self.Pwr.resource.query("SOUR:CURR:LEV:IMM:AMPL?")))
            if(self.StopALL.is_set()):
                self.parent.after(1, self.PS_voltage_var.set(self.Pwr.resource.query("MEAS:SCAL:VOLT:DC?")))
                self.parent.after(1, self.PS_current_var.set(self.Pwr.resource.query("MEAS:SCAL:CURR:DC?")))
                self.log_message(thread, level, f"Stopping DEMO")
                break
            init_v += voltage_step
            time.sleep(3)
        if((float(self.Pwer.resource.query("SOUR:VOLT:LEV:IMM:AMPL?")) >= 600) & self.StopALL.is_set() == False):
            for i in range(15):
                self.parent.after(1, self.PS_voltage_var.set(self.Pwr.resource.query("MEAS:SCAL:VOLT:DC?")))
                self.parent.after(1, self.PS_current_var.set(self.Pwr.resource.query("MEAS:SCAL:CURR:DC?")))
                if(self.StopALL.is_set()):
                    break
                time.sleep(1)
        self.log_message(thread, level, f"Stopping Thread and Voltage Output")
        self.Pwr.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
        self.Pwr.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")
        self.Pwr.resource.write("OUTP:STAT:IMM OFF")

    def read_pressure(self):
        pressureSensor = DAQDevice("Pressure")
        pressureSensor.task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=1, max_val=8, terminal_config=TerminalConfiguration.RSE)
        pressureSensor.task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
        while self.isExperimentStarted.is_set():
                pressure_sensor_voltage = np.array(pressureSensor.task.read(100))
                unfiltered_avg = np.median(pressure_sensor_voltage)
                true_pressure = 10**(unfiltered_avg - 5)
                #with pressure_lock:
                self.parent.after(1, lambda: self.pressure_var.set(true_pressure))
                if(self.StopALL.is_set()):
                    self.log_message("Pressure", "INFO", f"Stopping Thread")
                    pressureSensor.task.close()
                    return

if __name__ == "__main__":
    #Automatically creates chamebr app and imports experiment
    #For this to work you will need to write in the file location of the current file as well as the file location of the configuration files
    chamber = ChamberApp()

    chamber.menubar.load_experiment("./BeAMED/BeAMED_Packet/Demo.py")
    
    for config in ["Power_TR.config", "Digital_Multimeter.config"]:
        file = "./BeAMED/BeAMED_Packet/" + config
        chamber.generate_configuration_frame(filepath = file)

    chamber.mainloop()