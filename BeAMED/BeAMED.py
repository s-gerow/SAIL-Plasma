from ChamberGUIBuilder import *

class Experiment():
    def __init__(self, parent: ChamberApp):

        #_________________Attributes of Experiment__________________________________#
        self.parent = parent
        self.logger = logging.getLogger('BeAMED')
        self.rm = parent.rm

        #_________________Configure Experiment Frame________________________________#
        parent.experimentFrame.grid_columnconfigure(0, weight=1)
        parent.experimentFrame.grid_columnconfigure(1, weight=1)
        parent.experimentFrame.grid_rowconfigure(0, weight=1)
        #Frame to contain input settings for the experiment
        IOFrame = tk.LabelFrame(parent.experimentFrame, text="Input Settings")
        IOFrame.grid(row=0, column=0, sticky='nsew')
        DisplayFrame = tk.LabelFrame(parent.experimentFrame, text="Experiment Output")
        DisplayFrame.grid(row=0, column=1, sticky='nsew')

        #_________________Input Device Frame________________________________________#
        device_opt_frame = tk.Frame(IOFrame)
        device_opt_frame.pack(side="left")
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
        enabledisable_frame = tk.Frame(IOFrame)
        enabledisable_frame.pack(side="left")
        #Button appearance
        self.true_image = tk.PhotoImage(width=15, height=15)
        self.false_image = tk.PhotoImage(width=15, height = 15)
        self.true_image.put(("lime"), to=(0,0,14,14))
        self.false_image.put(("green"), to=(0,0,14,14))

        trig_true_image = tk.PhotoImage(width=50, height=50)
        trig_false_image = tk.PhotoImage(width=50, height=50)
        trig_true_image.put(("lime"), to=(0,0,49,49))
        trig_false_image.put(("green"), to=(0,0,49,49))

        cont_osc_var = tk.StringVar()
        tk.Label(enabledisable_frame, text='Enable Continuous Acquisition O-Scope (T: Enable)').grid(row=0 )
        tk.Checkbutton(enabledisable_frame, 
                                text = 'T: Enable',
                                variable=cont_osc_var,
                                image = self.false_image, 
                                selectimage = self.true_image, 
                                indicatoron = False, 
                                compound= 'left',
                                onvalue="Enable",
                                offvalue="Disable").grid(row=1 )

        auto_range_var = tk.StringVar()
        tk.Label(enabledisable_frame, text = 'Auto Range DMM (T: Enable)').grid(row=2 )
        tk.Checkbutton(enabledisable_frame, 
                                    text = 'T: Enable',
                                    variable=auto_range_var,
                                    image = self.false_image, 
                                    selectimage = self.true_image, 
                                    indicatoron = False, 
                                    compound= 'left',
                                    onvalue="Enable",
                                    offvalue="Disable").grid(row=3 )

        v_out_var = tk.StringVar()
        tk.Label(enabledisable_frame, text = 'Enable V-Output Power (T: Enable)').grid(row=4 )
        tk.Checkbutton(enabledisable_frame, 
                                text = 'T:Enable',
                                image = self.false_image, 
                                selectimage = self.true_image, 
                                indicatoron = False, 
                                compound= 'left',
                                variable = v_out_var,
                                onvalue="Enable",
                                offvalue="Disable").grid(row=5 )
        tk.Label(enabledisable_frame, text = 'Power Supply Output Mode', font = ('Times New Roman', 14, 'bold')).grid(row=6 )
        cv_var = tk.IntVar()
        tk.Checkbutton(enabledisable_frame, 
                                text = "CV Mode", 
                                image = self.false_image, 
                                selectimage = self.true_image, 
                                indicatoron = False, 
                                compound= 'left',
                                onvalue = 1, 
                                offvalue = 0,
                                variable = cv_var).grid(row=7)
        cc_var = tk.IntVar()
        tk.Checkbutton(enabledisable_frame, 
                                text = "CC Mode", 
                                image = self.false_image,
                                selectimage = self.true_image, 
                                indicatoron = False, 
                                compound ='left',
                                onvalue = 1, 
                                offvalue = 0,
                                variable = cc_var).grid(row=8)
        
        #_________________Frame for Experiment Condition Settings___________________#
        experimentCondysFrame = tk.Frame(IOFrame)
        experimentCondysFrame.pack(side = "left")

        init_v_var = tk.StringVar()
        tk.Label(experimentCondysFrame,
                text = "Input Voltage (V)",
                ).grid(row=0)
        ttk.Spinbox(experimentCondysFrame,
                    from_ = 0,
                    to = 100000,
                    textvariable=init_v_var
                    ).grid(row=1)

        current_var = tk.StringVar()
        tk.Label(experimentCondysFrame,
                text = "Current Level (0.5A)").grid(row=2)
        ttk.Spinbox(experimentCondysFrame,
                    from_ = 0,
                    to = 1000000,
                    textvariable = current_var
                    ).grid(row=4)

        #Position of the plates
        position_title = tk.Label(experimentCondysFrame,
                                text = "Position Set-Up",
                                font = ('Times New Roman', 14, 'bold')
                                ).grid(row=5)
        plate_pos_label = tk.Label(IO_Frame,
                                text = "Plate Position",
                                font = label_font
                                ).place(x=550, y=275)
        electrode_pos_label = tk.Label(IO_Frame,
                                    text = "Electrode Position",
                                    font = label_font
                                    ).place(x=550,y=325)
        plate_pos_var = tk.StringVar()
        electrode_pos_var = tk.StringVar()
        plate_spinbox = ttk.Spinbox(IO_Frame,
                                    from_=-10,
                                    to=10,
                                    textvariable=plate_pos_var
                                    ).place(x=552,y=300,width=125)
        electrode_spinbox = ttk.Spinbox(IO_Frame,
                                        from_=-10,
                                        to=10,
                                        textvariable=electrode_pos_var
                                        ).place(x=552,y=350,width=125)

            #Target Pressure
        init_pressure = tk.StringVar()
        pressure_title = tk.Label(IO_Frame,
                                text = "Target Pressure",
                                font = ('Times New Roman', 14, 'bold')
                                ).place(x=550,y=400)
        pressure_spinbox = tk.Spinbox(IO_Frame,
                                    from_=0,
                                    to = 800,
                                    textvariable=init_pressure
                                    ).place(x=552, y=425, width=125)

    def toggle_check_btn(btn, var):
        if var.get() == "Enable":
            btn.configure(text='T: Enable')
        elif var.get() == "Disable":
            btn.configure(text='F: Disable')

    
    def start_log(self):
        handler = logging.FileHandler('debug.log', mode = 'w')
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self.log_message("MAIN", "INFO", f"BeAMED Plasma Chamber debug log started")

    def log_message(self, thread, level, message):
        self.logger.debug(f"{thread}: {time.strftime('%X', time.localtime())} - {level} - {message}")

    #I/O selection for Oscilloscope, Power, and Digital Multimeter
    def check_IO(self):
        IO_opts = ["Refresh"]
        for i in self.rm.list_resources():
            if self.rm.list_resources_info()[i][4] == None:
                IO_opts.append(i)
            else:
                IO_opts.append(self.rm.list_resources_info()[i][4])
        return IO_opts

    def update_combo_box(self, event, cbox_name):
        IO_opts = self.check_IO()
        # Update the combo box with new resources
        if cbox_name.get() == "Refresh":
            self.pwr_cbox['values'] = IO_opts
            self.osc_cbox['values'] = IO_opts
            self.dmm_cbox['values'] = IO_opts
            cbox_name.set("")
        else:
            self.parent.generate_configuration_frame(filename= cbox_name.get())
    
    def run_experiment(self, event = None):
        print("Running BeAMED Experiment")
        print(self.rm.list_opened_resources())
        #thread configures oscilliscope (thread 1)
        #thread configures dmm (thread 2)
        #thread configures power (thread 3)
        #thread configures DAQ connection (thread 4)
        #all previous threads should be done at this point
        #thread starts recording pressure (thread 5)
        #automated feedthrough grounds the nodes and sets to value (wait until done)
        #notification to start pumping to vacuum (10sec)
        #thread monitors pressure to turn on MFC (thread 6)
        #thread stops mfc at target pressure. 
        #thread starts reading DMM (thread 7)
        #thread monitors oscilliscope for trigger (thread 8)
        #thread increases voltage at set rate (thread 9)
        
        #thread 8 catches trigger and queries osc to  run/stop and for waveform
        #thread 8 sends message to stop all other threads and retreive last measured values
        #all threads stop action and send values to excel sheet