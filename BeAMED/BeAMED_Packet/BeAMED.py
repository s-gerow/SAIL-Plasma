from ChamberGUIBuilder import *

        
class Experiment():
    def __init__(self, parent: ChamberApp):
        
        parent.protocol('WM_DELETE_WINDOW', lambda: self.clean_exit()) 
        #The lambda: function allows the return of this function to be returned "implicitely", 
        #ie. self.clean_exit() will not be traditionally called until the root protocol is met
        #_________________Attributes of Experiment__________________________________#
            #The parent attribute represents the ChamberApp which is needed to import this experiment
            #The logger is the custom debug logger I built to output errors and information as the experiment runs
            #The rm is the resource manager which comes from the parent and is used in pyvisa to communicate with devices
            #Dmm,Osc/Pwr are None-objects at start until they are properly imported, these attributes should be a pyvisa-object from ChamberApp.py
            #cont_acq, v_out, auto_range are variables to store the value of the associated buttons to initlize experiment
        self.parent = parent
        self.logger = logging.getLogger('BeAMED')
        self.rm = parent.rm
        self.Dmm = None
        self.Osc = None
        self.Pwr = None
        self.cont_acq = None
        self.v_out = None
        self.auto_range = None

        self.DY = 0

        #_________________Experiment Data Storage___________________________________#
        self.ExperimentOutputHeader = ['Time', 'D_Y(Osc)', 'V_in', 'V(Volts)', 'Current (Amp)', 'p_Exact(Torr)', 'p_Predict(Torr)', 'dis (cm)', 'd(V)', 'd(p)', 'd(d)', 'd(pd)']
        self.experimentOutputDataFrame = pd.DataFrame(columns=self.ExperimentOutputHeader)
        self.ExperimentRunValues = [[]] 
        self.SaveFileType = None
        self.isSaved = Event()

        #_________________Experiment Events_________________________________________#
            #Each of these events represent an important benchmark in the setup of the experiment. 
        self.isOscConfigured = Event()
        self.isDmmConfigured = Event()
        self.isPowerConfigured = Event()
        self.isPressureReading = Event()
        self.isTargetPressure = Event()
        self.isFeedthroughset = Event()
        self.isExperimentStarted = Event()
        self.StopALL = Event()

        class experimentEvent(Event):
            '''A custom Event class to store wether the experiment is triggered or not as well as store and output the relavent output data.'''
            def __init__(self):
                super().__init__()
                self.pressure = ""
                self.ps_voltage = ""
                self.ps_current = ""
                self.dmm_voltage = ""

            def getExperimentOutput(self):
                if(self.is_set):
                    output = [self.pressure, self.ps_current, self.ps_voltage, self.dmm_voltage]
                    return output
                else:
                    print("Event not triggered")
        self.isDischargeTriggered = experimentEvent()
        
        #***************************************************************************#
        #All sections here until the end of the __init__ method are specfically formating frames and widgets for user input.
        #If you need to access any of this information, a tkinter variable will be named "self.var_name". This variable is how you access 
        #the data from these inputs. If you want to add a new feild you do not need to label the label, input box, and variable with "self.", 
        #only the variable.
        #_________________Configure Experiment Frame________________________________#
            #Splits the Experiment Frame of the Chamber app into two frames for input and output
        parent.experimentFrame.grid_columnconfigure(0, weight=1)
        parent.experimentFrame.grid_columnconfigure(1, weight=1)
        parent.experimentFrame.grid_rowconfigure(0, weight=1)
        #Frame to contain input settings for the experiment
        IOFrame = tk.LabelFrame(parent.experimentFrame, text="Input Settings")
        IOFrame.grid(row=0, column=0, sticky='nsew')
        DisplayFrame = tk.LabelFrame(parent.experimentFrame, text="Experiment Output")
        DisplayFrame.grid(row=0, column=1, sticky='nsew')
        
        #_________________Input Device Frame________________________________________#
            #A frame to contain dropdowns to select devices from the pyvisa resource menu
        device_opt_frame = tk.Frame(IOFrame)
        device_opt_frame.grid(row=0, column=0)
        
        tk.Label(device_opt_frame, text = 'VISA Power').grid(row=0, column=0)
        self.pwr_cbox = ttk.Combobox(device_opt_frame, state = 'readonly', values = self.check_IO())
        self.pwr_cbox.bind('<<ComboboxSelected>>', lambda event: self.update_combo_box(event, self.pwr_cbox))
        self.pwr_cbox.grid(row =0, column=1)
        
        tk.Label(device_opt_frame, text = 'VISA DMM').grid(row=1,column=0)
        self.dmm_cbox = ttk.Combobox(device_opt_frame, state = 'readonly', values = self.check_IO())
        self.dmm_cbox.bind('<<ComboboxSelected>>', lambda event: self.update_combo_box(event, self.dmm_cbox))
        self.dmm_cbox.grid(row=1,column=1)

        tk.Label(device_opt_frame, text = 'VISA O-Scope').grid(row=2,column=0)
        self.osc_cbox = ttk.Combobox(device_opt_frame, state = 'readonly', values = self.check_IO())
        self.osc_cbox.bind('<<ComboboxSelected>>', lambda event: self.update_combo_box(event, self.osc_cbox))
        self.osc_cbox.grid(row=2,column=1)
        
        #_________________Frame for CheckBox Settings at Experiment Startup_________#
            #Frame holding checkboxes for configurations
        enabledisable_frame = tk.Frame(IOFrame)
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
        
        self.cont_osc_var = tk.StringVar(value = "Disable")
        tk.Label(enabledisable_frame, text='Enable Continuous Acquisition O-Scope (T: Enable)').grid(row=0 )
        self.cont_button = tk.Checkbutton(enabledisable_frame, 
                                text = 'T: Enable',
                                variable=self.cont_osc_var,
                                image = self.false_image, 
                                selectimage = self.true_image, 
                                indicatoron = False, 
                                compound= 'left',
                                onvalue="Enable",
                                offvalue="Disable",
                                command = lambda: self.toggle_check_btn(self.cont_button, self.cont_osc_var))
        self.cont_button.grid(row=1 )
        
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

        tk.Label(enabledisable_frame, text = 'Power Supply Output Mode', font = ('Times New Roman', 14, 'bold')).grid(row=6 )
        self.cv_var = tk.IntVar()
        tk.Checkbutton(enabledisable_frame, 
                                text = "CV Mode", 
                                image = self.false_image, 
                                selectimage = self.true_image, 
                                indicatoron = False, 
                                compound= 'left',
                                onvalue = 1, 
                                offvalue = 0,
                                variable = self.cv_var).grid(row=7)
        self.cc_var = tk.IntVar()
        tk.Checkbutton(enabledisable_frame, 
                                text = "CC Mode", 
                                image = self.false_image,
                                selectimage = self.true_image, 
                                indicatoron = False, 
                                compound ='left',
                                onvalue = 1, 
                                offvalue = 0,
                                variable = self.cc_var).grid(row=8)
        
        #_________________Frame for Experiment Condition Settings___________________#
        experimentCondysFrame = tk.Frame(IOFrame)
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
        tk.Label(experimentCondysFrame,
                text = "Position Set-Up",
                font = ('Times New Roman', 14, 'bold')
                ).grid(row=5)
        self.plate_pos_var = tk.StringVar()
        ttk.Spinbox(experimentCondysFrame,
                    from_=-10,
                    to=10,
                    textvariable=self.plate_pos_var,
                    state='disabled'
                    ).grid(row=7)
        tk.Label(experimentCondysFrame,
                                text = "Plate Position").grid(row=6)
        tk.Label(experimentCondysFrame,
                text = "Electrode Position").grid(row=8)
        self.electrode_pos_var = tk.StringVar(value=0)
        ttk.Spinbox(experimentCondysFrame,
                    from_=-10,
                    to=10,
                    increment=0.5,
                    textvariable=self.electrode_pos_var
                    ).grid(row=9)

            #Target Pressure
        self.init_pressure = tk.StringVar()
        tk.Label(experimentCondysFrame,
                    text = "Target Pressure",
                    font = ('Times New Roman', 14, 'bold')
                    ).grid(row=10)
        tk.Spinbox(experimentCondysFrame,
                    from_=0,
                    to = 800,
                    textvariable=self.init_pressure
                    ).grid(row=11)
        
        #configure button
        ttk.Button(IOFrame,
                       text="Configure Experiment",
                       command=self.run_experiment_configuration).grid(column=3,row=0)
        experiment_text = (
                            "This is the procedure for using BeAMED.py to perform automated glow discharges.\n"
                            "1. Starting with the input settings panel, select the power multimeter, and oscilloscope from the drop down. If you cannot find a device, ensure it is turned on and then select the refresh button.\n"
                            "2. Despite the appearence of the buttons, the 3 enable buttons to the right of the dropdows are disabled by default, they must be turned on prior to starting the experiment.\n"
                            "*Note: Power supply output mode buttons do not actually change anything about the experiment.\n"
                            "3. Set the input voltage to 5~10V below the expected breakdown. Use previous testing data to guage. If there is no known data start at 27V.\n"
                            "4. Set Current Level to 0.5A\n"
                            "5. Set the desired electrode distance.\n"
                            "6. Set the Target Pressure in Torr.\n"
                            "7. Turn on the power supply connected to the feedthrough to provide the needed 22V\n"
                            "7. Click Configure Experiment and follow the popup prompts"
        )
        procedure = tk.Text(IOFrame, wrap=tk.WORD, height=25, width=50)
        procedure.insert(tk.END, experiment_text)
        procedure.config(state=tk.DISABLED)
        procedure.grid(columnspan=2,column=3, row=1)
        #_________________Frame for Experiment Control_______________________________#
        experimentControlFrame = tk.Frame(DisplayFrame)
        experimentControlFrame.grid(row=1, column=0)

        #Start/Stop Buttons
        ttk.Button(experimentControlFrame, text = 'START', command=self.run_experiment).grid(row=0)
        ttk.Button(experimentControlFrame, text = 'STOP',command=self.clean_exit).grid(row=1)

        self.triggered_var = tk.IntVar()
        tk.Label(experimentControlFrame,
                    text = "Triggered\nEvent").grid(row=3)
        tk.Checkbutton(experimentControlFrame, 
                        text = "Event Triggered?", 
                        image = self.trig_false_image, 
                        selectimage = self.trig_true_image, 
                        indicatoron = False, 
                        onvalue = 1, 
                        offvalue = 0, 
                        command = lambda: self.test_trigger_experiment(),
                        variable = self.triggered_var).grid(row=4)

        
        #_________________Frame for Experiment Output Graph_________________________#
        experimentGraphFrame = tk.Frame(DisplayFrame)
        experimentGraphFrame.grid(row=0, columnspan=2)

        figure = Figure(dpi=75)
        self.figure_canvas = FigureCanvasTkAgg(figure, experimentGraphFrame)
        NavigationToolbar2Tk(self.figure_canvas,experimentGraphFrame).pack(side='top')
        self.axes = figure.add_subplot()
        self.axes.set_title('Discharge Plot')
        self.axes.set_ylabel('Voltage')
        self.axes.set_xlabel('Time')
        self.figure_canvas.get_tk_widget().pack(side='top')

        #_________________Frame for Experiment Output_______________________________#
        experimentOutputFrame = tk.Frame(DisplayFrame)
        experimentOutputFrame.grid(row=1, column=1)

        tk.Label(experimentOutputFrame,
                            text = "Power Supply Voltage").grid(row = 0, column=0)
        tk.Label(experimentOutputFrame,
                             text = "Power Supply Current").grid(row=1, column = 0)
        tk.Label(experimentOutputFrame,
                        text = "Voltage Output").grid(row=2, column=0)
        tk.Label(experimentOutputFrame,
                        text = "Pressure (Torr)").grid(row=3, column=0)
        self.PS_voltage_var = tk.DoubleVar()
        tk.Spinbox(experimentOutputFrame,
                        from_=0,
                        to = 800,
                        textvariable=self.PS_voltage_var
                        ).grid(row=0, column=1)
        self.PS_current_var = tk.DoubleVar()
        tk.Spinbox(experimentOutputFrame,
                        from_=0,
                        to = 800,
                        textvariable=self.PS_current_var
                        ).grid(row=1, column=1)
        self.voltage_out_var = tk.DoubleVar()
        tk.Spinbox(experimentOutputFrame,
                        from_=0,
                        to = 800,
                        textvariable=self.voltage_out_var
                        ).grid(row=2, column=1)
        self.pressure_var = tk.DoubleVar()
        tk.Spinbox(experimentOutputFrame,
                        from_=0,
                        to = 800,
                        textvariable=self.pressure_var
                        ).grid(row=3, column=1)
        
        tk.Label(experimentOutputFrame, text="Save to:").grid(column=2, row=0)
        self.SaveFile = tk.StringVar()
        self.saveOptionBox = tk.Spinbox(experimentOutputFrame, state='readonly', textvariable=self.SaveFile).grid(row=0, column=4)
        
        
        #_________________Create New Dropdown Options_________________________#
        

        self.parent.menubar.devMenu.add_command(label = "Test Trigger", command= self.test_trigger_experiment)

        self.parent.menubar.devMenu.add_command(label="Get Plot", command = self.osc_plot)
        self.parent.menubar.devMenu.add_command(label = "Zero Feedthrough", command = Thread(target = lambda: self.moveFeedthrough(float(self.electrode_pos_var.get())), daemon= True).start)
        self.parent.menubar.devMenu.add_command(label = "Set Chamber Pressure", command = Thread(target = lambda: self.runMFC(float(self.init_pressure.get())), daemon=True).start)
        self.parent.menubar.fileMenu.add_command(label ="Import Data", command=self.open_save_file)
        self.parent.menubar.fileMenu.add_command(label = "Save Data", command=self.save_to_current)
        self.exportMenu = tk.Menu(self.parent.menubar, tearoff=0)
        self.parent.menubar.fileMenu.add_cascade(label = "Export As...", menu=self.exportMenu)
        self.exportMenu.add_command(label = "Excel", command=self.open_export_panel)
        self.exportMenu.add_command(label = "CSV")
        self.parent.menubar.fileMenu.add_separator()
        self.parent.menubar.fileMenu.add_command(label="Exit", command = self.clean_exit)
        
    def clean_exit(self):
        '''clean_exit() is used by the parent menu to intercept the "X' button at the top right and ensure that all 
        threads and open processes are closed before the UI quits'''
        level = "INFO"
        thread = "MAIN"
        self.log_message(thread, level, f"Quitting Application. Cleaning up loose threads.")
        for i in [self.Dmm, self.Osc, self.Pwr]:
            if isinstance(i, VisaDevice):
                self.log_message(thread, level, f"Closing {i.name}")
                if i.name == "Power_TL":
                    i.open_device()
                    i.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
                    i.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")
                i.close_device()
        self.parent.destroy()


    def toggle_check_btn(self, btn, var):
        '''toggle_check_btn allows the check buttons to change their text when they are activated by clicking'''
        if var.get() == "Enable":
            btn.configure(text='T: Enable')
        elif var.get() == "Disable":
            btn.configure(text='F: Disable')

    
    def start_log(self):
        '''start_log() initlizes the logger into a file called debug.log which will record events for the experiment'''
        handler = logging.FileHandler('debug.log', mode = 'w')
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self.log_message("MAIN", "INFO", f"BeAMED Plasma Chamber debug log started")

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
            self.osc_cbox['values'] = IO_opts
            self.dmm_cbox['values'] = IO_opts
            cbox_name.set("")
        else:
            self.parent.generate_configuration_frame(filename= cbox_name.get())
    
    def test_trigger_experiment(self):
        '''test method which will trigger the event without external input'''
        if self.triggered_var.get() == 0:
            self.isDischargeTriggered.set()
            self.triggered_var.set(1)
            print(self.isDischargeTriggered.is_set())
            self.log_message("MAIN", "INFO", "Discharge Triggered")
        else:
            self.isDischargeTriggered.clear()
            self.triggered_var.set(0)
            print(self.isDischargeTriggered.is_set())

    def run_experiment_configuration(self):
        '''This is the first method which configures the experiment. It runs threads to zero the feedthrough, run the MFC and get to target pressure, and configure each device. 
        This must be done before the experiment start button is clicked'''
        thread = "MAIN"
        level = "INFO"
        
        #start the debug log and clear the oscilloscope plot for a new experiment
        self.start_log()
        self.axes.clear()
        self.triggered_var.set(0)
        #Reset the discharge Event and set the experiment event in order to signify the experiment has started to other threads
        self.isDischargeTriggered.clear()
        self.isExperimentStarted.set()
        self.isFeedthroughset.clear()
        #initilize each object from the dropdown boxes
        oscName = self.osc_cbox.get()
        dmmName = self.dmm_cbox.get()
        pwrName = self.pwr_cbox.get()
        #use the chamber_app parent to configure above devices with the values stored in the configuration frames of the chamberApp
        self.parent.devices[pwrName][1].configureAll()
        self.parent.devices[oscName][1].configureAll()
        self.parent.devices[dmmName][1].configureAll()
        #Check to enable auto range and continuous acquisition
        if self.cont_osc_var.get() == "Enable":
            self.cont_acq = "NORM"
        else:
            self.cont_acq = "AUTO"
        if self.auto_range_var.get() == "Enable":
            self.auto_range = "ON"
        else:
            self.auto_range = "OFF"
        #initilize DMM then zero feedthrough
        self.Dmm = self.parent.devices[dmmName][0]
        target_position = float(self.electrode_pos_var.get())
        setFeedthrough = Thread(target = lambda: self.moveFeedthrough(target_position), daemon= True)
        setFeedthrough.start()
        while not self.isFeedthroughset.is_set():
            time.sleep(1)
        #Initilize threads to configure pyvisa devices
        osccfg = Thread(target = lambda: self.configureOscilloscope(oscName))
        dmmcfg = Thread(target = lambda: self.configureDMM(dmmName))
        pwrcfg = Thread(target = lambda: self.configurePower(pwrName))
        configurationThreads = [ osccfg, dmmcfg, pwrcfg]
        #Start configuration threads and wait for them to complete before continuing
        for thread in configurationThreads:
            self.log_message(thread, level,f"starting {thread} thread")
            thread.start()
        for thread in configurationThreads:
            thread.join()

    def run_experiment(self, event = None):
        thread = "MAIN"
        level = "INFO"
        '''This is the main experiment logic. In order to run, all configurations must be complete as declared by an event flag in run_experiment_configuration'''
        #First check to ensure voltage output is enabled and do not start the experiment if it is disabled
        if self.v_out_var.get() == "Disable":
            messagebox.showerror("Experiment Initilization Error", "Voltage Output Disabled.\nPlease enable voltage output then try again", icon=messagebox.ERROR)
            return
        for i in [self.isDmmConfigured.is_set(), self.isPowerConfigured.is_set(), self.isOscConfigured.is_set()]:
            if not i:
                messagebox.showerror("One or more devices are not configured. Configrue experiment, then run again")
                return
        #print(self.isDmmConfigured.is_set(), self.isPowerConfigured.is_set(), self.isOscConfigured.is_set())
        #all previous threads should be done at this point
        #thread starts recording pressure continuouslly until the end of the experiment
        #pressure_lock = Lock() #this is to allow the live_pressure and MFcpressure to access the same variables without hanging the application
        self.log_message(thread, level, "Starting Continuous Pressure Reading")
        live_pressure = Thread(target = lambda: self.read_pressure(),daemon=True)
        live_pressure.start()
    

        #thread starts reading DMM
        self.log_message(thread, level, "Starting Continuos Voltage Reading")
        live_dmm = Thread(target = lambda: self.readDmm(), daemon=True)
        live_dmm.start()
        #thread monitors oscilliscope for trigger
        live_osc = Thread(target = lambda: self.readOsc(), daemon = True)
        live_osc.start()
        #thread increases voltage at set rate 0.5V/3s
        init_v = float(self.init_v_var.get())
        init_c = float(self.init_current_var.get())
        v_increase = Thread(target = lambda: self.increase_voltage(init_v, init_c))
        v_increase.start()
        #all threads stop action and send values to excel sheet
        

    

    def configureOscilloscope(self, oscName):
        thread = "CFG-OSC"
        level = "INFO"
        self.log_message(thread, level, f"configuring{oscName}")
        self.Osc = self.parent.devices[oscName][0]
        
        self.Osc.open_device()
        if self.Osc.options['Reset'][0] == "True":
            self.Osc.resource.write("*RST")
        self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:ATTN {self.Osc.options['Attenuation'][0]}")
        self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:OFST {self.Osc.options['Vertical Offset'][0]}")
        self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:VDIV {self.Osc.options['Voltage Division'][0]}")
        self.Osc.resource.write(f"TDIV {self.Osc.options['Time Division'][0]}")
        self.Osc.resource.write(f"HPOS {self.Osc.options['Horizontal Position'][0]}")
        self.Osc.resource.write(f"TRMD {self.cont_acq}")
        self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:TRSL {self.Osc.options['Trigger Slope'][0]}")
        self.Osc.resource.write(f"TRSE EDGE,SR,{self.Osc.options['Channel'][0]},HT,TI,HV,{self.Osc.options['Holdoff'][0]}")
        self.Osc.resource.write(f"{self.Osc.options['Channel'][0]}:TRLV {self.Osc.options['Trigger Level'][0]}")
        self.Osc.close_device()
        self.log_message(thread, level, f"{oscName} Successfully Configured")
        self.isOscConfigured.set()

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

    def read_pressure(self):
        pressureSensor = DAQDevice("Pressure")
        pressureSensor.task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=1, max_val=8, terminal_config=TerminalConfiguration.RSE)
        pressureSensor.task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
        self.isPressureReading.set()
        while self.isExperimentStarted.is_set():
                pressure_sensor_voltage = np.array(pressureSensor.task.read(100))
                unfiltered_avg = np.median(pressure_sensor_voltage)
                true_pressure = 10**(unfiltered_avg - 5)
                #with pressure_lock:
                self.parent.after(1, lambda: self.pressure_var.set(true_pressure))
                if(self.isDischargeTriggered.is_set()):
                    self.isDischargeTriggered.pressure = true_pressure
                    self.log_message("Pressure", "INFO", f"Discharge Triggered at {true_pressure} Torr")
                    pressureSensor.task.close()
                    return

    def readDmm(self):
        thread = "DMM"
        level = "INFO"
        self.Dmm.open_device()
        #self.Dmm.resource.write(':SENS:FUNC "VOLT:DC"')
        while(self.isExperimentStarted.is_set() & self.isDischargeTriggered.is_set() == False):
            voltage = self.Dmm.resource.query(':READ?')
            self.parent.after(1, lambda: self.voltage_out_var.set(voltage))
        if(self.isDischargeTriggered.is_set()):
            self.isDischargeTriggered.dmm_voltage = voltage
            self.log_message(thread, level, f"Discharge Triggered at {voltage} V")
            return
        
    def readOsc(self):
        self.Osc.open_device()
        
        while(self.isExperimentStarted.is_set()& self.isDischargeTriggered.is_set() == False):
            VPP = self.Osc.resource.query(f"{self.Osc.options['Channel'][0]}:PARAMETER_VALUE? PKPK")
            if VPP[13:-1] == "****":
                VPP_num = 0
            else:
                VPP_num = float(VPP[13:-2])
            if VPP_num > 0:
                self.isDischargeTriggered.set()
                self.triggered_var.set(1)
                self.Osc.resource.write("STOP")
                self.log_message("OSC", "INFO", "Discharge Detected")
                self.osc_plot()
                self.Osc.close_device()
                return
        self.Osc.close_device()
        time.sleep(5)

    def runMFC(self, target_pressure):
        pressureSensor = DAQDevice("Pressure")
        pressureSensor.task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=1, max_val=8, terminal_config=TerminalConfiguration.RSE)
        pressureSensor.task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
        MFC = DAQDevice("MFC")
        MFC.task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao0", min_val=0,max_val=5)
        MFC.task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao1", min_val=0, max_val=5)
        #get target pressure
        #set min pressure always 20mTorr
        min_pressure = 2#0.020
        #measure pressure drop until at min pressure
        pressure_sensor_voltage = np.array(pressureSensor.task.read(100))
        unfiltered_avg = np.median(pressure_sensor_voltage)
        true_pressure = 10**(unfiltered_avg - 5)
        while true_pressure > min_pressure:
            self.parent.after(1, lambda: self.pressure_var.set(true_pressure))
            pressure_sensor_voltage = np.array(pressureSensor.task.read(100))
            unfiltered_avg = np.median(pressure_sensor_voltage)
            true_pressure = 10**(unfiltered_avg - 5)
            MFC.task.write([[0],[0]],auto_start=True, timeout=10)
        result = messagebox.showinfo(title="Turn Off Pump", message="Chamber at target minimum pressure, turn off the pump and open the gas tank before clicking okay.")
        while true_pressure < target_pressure:
            self.parent.after(1, lambda: self.pressure_var.set(true_pressure))
            pressure_sensor_voltage = np.array(pressureSensor.task.read(100))
            unfiltered_avg = np.median(pressure_sensor_voltage)
            true_pressure = 10**(unfiltered_avg - 5)
            if true_pressure >= target_pressure:
                MFC.task.write([[0],[0]],auto_start=True, timeout=10)
                break
            MFC.task.write([[5],[3]],auto_start=True, timeout=10)
        if true_pressure >= target_pressure:
            MFC.task.write([[0],[0]],auto_start=True, timeout=10)
        
        #popup notification to turn off pump then hit okay.
        #turn on mfc
        #monitor pressure until at target
        #turn off mfc.
        #ready to start experiment
        


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
        print("done")
        
    
    def increase_voltage(self, init_v: int, init_c: int):
        thread = "PWR"
        level = "INFO"
        self.Pwr.open_device()
        self.Pwr.resource.write("OUTP:STAT:IMM ON")
        voltage_step = float(self.Pwr.options["Voltage Step Size"][0])
        self.Pwr.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {init_c}")
        while self.isDischargeTriggered.is_set() == False:
            self.Pwr.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {init_v}")
            self.parent.after(1, lambda: self.voltage_out_var.set(self.Pwr.resource.query("SOUR:VOLT:LEV:IMM:AMPL?")))
            if(self.isDischargeTriggered.is_set()):
                self.parent.after(1, self.PS_voltage_var.set(self.Pwr.resource.query("MEAS:SCAL:VOLT:DC?")))
                self.parent.after(1, self.PS_current_var.set(self.Pwr.resource.query("MEAS:SCAL:CURR:DC?")))
                self.log_message(thread, level, f"Discharge Triggered at {self.Pwr.resource.query('MEAS:SCAL:CURR:DC?')} A")
                self.log_message(thread, level, f"Discharge Triggered at {self.Pwr.resource.query('MEAS:SCAL:VOLT:DC?')} V")
            init_v += voltage_step
            time.sleep(3)
        self.parent.after(1, self.PS_voltage_var.set(self.Pwr.resource.query("MEAS:SCAL:VOLT:DC?")))
        self.parent.after(1, self.PS_current_var.set(self.Pwr.resource.query("MEAS:SCAL:CURR:DC?")))
        self.log_message(thread, level, f"Discharge Triggered at {self.Pwr.resource.query('MEAS:SCAL:CURR:DC?')} A")
        self.log_message(thread, level, f"Discharge Triggered at {self.Pwr.resource.query('MEAS:SCAL:VOLT:DC?')} V")
        self.Pwr.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
        self.Pwr.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")
        self.Pwr.resource.write("OUTP:STAT:IMM OFF")

    def osc_plot(self):
        self.axes.clear()
        self.Osc.resource.write('DATASOURCE CHANNEL1')
        self.Osc.resource.write('DATA:ENCDG SRI')
        self.Osc.resource.write('DATA:WIDTH 2')
        self.Osc.resource.write('DATA:START 0')
        self.Osc.resource.write('DATA: STOP 1000')
        
        sample_rate = self.Osc.resource.query("SARA?")
        time_inter = 1/float(sample_rate[5:-5])
        tdiv = float(self.Osc.resource.query("TDIV?")[5:-2])
        offset = float(self.Osc.resource.query("C1:OFST?")[8:-2])
        vdiv = float(self.Osc.resource.query("C1:VDIV?")[8:-2])
        self.Osc.resource.write("C1:WF? DAT2")
        wf = self.Osc.resource.read_raw()
        self.Osc.close_device()
        wf = wf[16:-2]

        hgrid = 14

        decimal = []
        for i,byte in enumerate(wf):
            decimal.append(int.from_bytes(wf[i:i+1], byteorder=sys.byteorder))
        data = np.array(decimal)
        time = np.flip(np.array([(tdiv*hgrid)-(idx*time_inter) for idx in range(0,data.size) ]))

        voltage_data = np.array([int(code)*(vdiv/25)-offset if int(code) < 127 else (int(code)-256)*(vdiv/25)-offset for code in data])
        
        self.DY = voltage_data.max()
        self.axes.plot(time, voltage_data)
        self.axes.set_title('Discharge Plot')
        self.axes.set_ylabel('Voltage (V)')
        self.axes.set_xlabel('Time (s)')

        self.figure_canvas.draw()
        self.save_experiment_to_local()

    def save_experiment_to_local(self):
        current_run = ["NaN","NaN", "NaN", "NaN","NaN", "NaN", "NaN","NaN", "NaN", "NaN","NaN", "NaN"]
        dt = datetime.now()
        current_run[0] =  f"{dt.month}/{dt.day}/{dt.year} {dt.hour}:{dt.minute}" #Time is set at end of experiment
        current_run[1] = self.DY#" #Need to find how to get DY from osc
        current_run[2] = float(self.PS_voltage_var.get()) #power supply voltage output
        current_run[3] = float(self.voltage_out_var.get()) #read voltage out from dmm
        current_run[4] = float(self.PS_current_var.get()) #power supply current output
        current_run[5] = float(self.pressure_var.get()) #pressure read by pressure sensor
        current_run[6] = float(self.init_pressure.get()) #target pressure
        current_run[7] = float(self.electrode_pos_var.get()) #distance
        current_run[8] = float(self.voltage_out_var.get())*0.000001 #uncertainty in measured voltage
        current_run[9] = float(self.pressure_var.get())*0.1 #uncertainty in measured pressure
        current_run[10] = 0.1
        current_run[11] = (float(self.pressure_var.get())*float(self.electrode_pos_var.get()))*(((float(self.pressure_var.get())*0.1)/float(self.pressure_var.get()))+(0.1/float(self.electrode_pos_var.get())))
        
        self.ExperimentRunValues[0] = current_run
        newdataframe = pd.DataFrame(self.ExperimentRunValues, columns=self.ExperimentOutputHeader)
        self.experimentOutputDataFrame = pd.concat([newdataframe, self.experimentOutputDataFrame])
        self.isSaved.clear()
        print(self.experimentOutputDataFrame)

    def save_to_new(self):
        filename = f"{datetime.now().year}{datetime.now().month}{datetime.now().day}_BeAMED_Output.csv"
        try:
            self.experimentOutputDataFrame.to_csv(filename, mode='x', index=False)
            self.SaveFileType = "CSV"
            self.SaveFile.set(filename)
            self.isSaved.set()
            self.experimentOutputDataFrame.iloc[0:0]
        except FileExistsError:
            output = messagebox.askokcancel("File Already Exists", "A file with today's date already exists. This action will overide the file. Do you want to continue?")
            if output == True:
                self.experimentOutputDataFrame.to_csv(filename, mode='w', index=False)
                self.SaveFileType = "CSV"
                self.SaveFile.set(filename)
                self.isSaved.set()
                self.experimentOutputDataFrame.iloc[0:0]
            else:
                return

    def save_to_current(self):
        if self.SaveFile.get() == "":
            response = messagebox.askokcancel(title="Save As?", message="You have not selected a file to save to. This will create a new save file? Is that okay?")
            if response == True:
                self.save_to_new()
            else: return
        elif self.SaveFileType == "CSV":
            filename = self.SaveFile.get()
            self.experimentOutputDataFrame.to_csv(filename, mode = 'a', header= False, index = False)
            self.isSaved.set()
            self.experimentOutputDataFrame.iloc[0:0]

    def open_save_file(self):
        filepath = fd.askopenfilename(title="Open...", filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlxs")])
        if filepath:
            if filepath.endswith(".csv"):
                self.SaveFile.set(os.path.basename(filepath))
                self.SaveFileType = "CSV"
            elif filepath.endswith(".xlxs"):
                messagebox.showwarning("Excel Files Invalid", "Excel Files are currently not supported. Use CSV")

    def export_to_csv(self):
        pass

    def export_to_excel(self):
        pass

    def open_export_panel(self):
        pass


        

    



if __name__ == "__main__":
    #Automatically creates chamebr app and imports experiment
    #For this to work you will need to write in the file location of the current file as well as the file location of the configuration files
    chamber = ChamberApp()

    chamber.menubar.load_experiment("./BeAMED/BeAMED_Packet/BeAMED.py")
    
    for config in ["Oscilloscope.config", "Digital_Multimeter.config", "Power_TR.config"]:
        file = "./BeAMED/BeAMED_Packet/" + config
        chamber.generate_configuration_frame(filepath = file)

    chamber.mainloop()