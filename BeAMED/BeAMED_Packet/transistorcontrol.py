from ChamberGUIBuilder import *

class Experiment():
    def __init__(self, parent: ChamberApp):
        self.parent = parent
        self.rm = parent.rm #this is a the resource manager. Used to
        self.PWR = None
        self.experiment_online = Event()
        self.visa_lock = threading.Lock()
        parent.protocol('WM_DELETE_WINDOW', lambda: self.clean_exit()) 

        self.do_task = None
        self.ao_task = None
        self.ai_task = None
        self.di_task = None

        self.DAQ_Frame = tk.Frame(self.parent.experimentFrame, width=550, height = 450, relief='sunken')
        self.DAQ_Frame.grid(column=0, row=0, sticky = 'nw')

        self.LED_ON = tk.PhotoImage(width=13, height=13)
        self.LED_OFF = tk.PhotoImage(width=13, height=13)
        self.LED_ON.put(("lime"), to=(0,0,12,12))
        self.LED_OFF.put(("red"), to=(0,0,12,12))
        self.DAQ_PIN = tk.PhotoImage(file='./BeAMED/DAQ_Pinout.PNG')

        self.enabled_do_channels = []
        self.enabled_ao_channels = []
        self.enabled_di_channels = []
        self.enabled_ai_channels = []
        self.daq_line_labels = ['/0', '/ai0', '/ai4', '/0', '/ai1', '/ai5', '/0', '/ai2', '/ai6', '/0', '/ai3', '/ai7', '/0', '/ao0', '/ao1', '/0',
                           '/port0/line0', '/port0/line1', '/port0/line2', '/port0/line3', '/port0/line4', '/port0/line5', '/port0/line6', '/port0/line7',
                           '/port1/line0', '/port1/line1', '/port1/line2', '/port1/line3', '/port2/line0', '/0', '/0', '/0']
        analog_output_row = 0
        digital_output_row = 447
        analog_enable_row = 20
        digital_enable_row = 427
        label_row = 40
        label = ttk.Label(self.DAQ_Frame, image = self.DAQ_PIN)
        label.place(x=label_row,y=0)

        self.output_bool_vars = [tk.BooleanVar() for _ in range(32)]
        self.output_buttons = [tk.Checkbutton(self.DAQ_Frame, 
                        image = self.LED_OFF, 
                        selectimage = self.LED_ON, 
                        indicatoron = False, 
                        onvalue = True, 
                        offvalue = False, 
                        variable = self.output_bool_vars[i],
                        state = "disabled" if self.daq_line_labels[i]=='/0' else "normal",
                        command = lambda j=i: self.pin_output(j),
                        borderwidth=0) for i in range(32)]
        self.enable_var = [tk.IntVar() for _ in range(32)]
        self.enable_checkboxes = [tk.Checkbutton(self.DAQ_Frame,
                                                  variable = self.enable_var[i],
                                                  onvalue = 1,
                                                  offvalue = 0,
                                                  highlightthickness=0,
                                                  bd=0,
                                                  state = "disabled" if self.daq_line_labels[i]=='/0' else "normal",
                                                  command = lambda j=i: self.pin_enable(j),
                                                  ) for i in range(32)]
        start_y = 99
        for i in range(16):
            self.output_buttons[i].place(x=analog_output_row,y=start_y)
            self.output_buttons[i+16].place(x=digital_output_row, y=start_y)
            self.enable_checkboxes[i].place(x=analog_enable_row,y=start_y-1)
            self.enable_checkboxes[i+16].place(x=digital_enable_row,y=start_y-1)
            start_y += 16

        device_opt_frame = tk.LabelFrame(self.parent.experimentFrame, relief='sunken',text="VISA Control")
        device_opt_frame.grid(row=1, column=0, sticky='nsew')
        tk.Label(device_opt_frame, text = 'VISA Power').grid(row=0, column=0)
        self.pwr_cbox = ttk.Combobox(device_opt_frame, state = 'readonly', values = self.check_IO())
        self.pwr_cbox.bind('<<ComboboxSelected>>', lambda event: self.update_combo_box(self.pwr_cbox))
        self.pwr_cbox.grid(row =0, column=0)
        self.pwr_configured_var = tk.BooleanVar()
        pwr_configured_indicator = tk.Checkbutton(device_opt_frame, 
                        image = self.LED_OFF, 
                        selectimage = self.LED_ON, 
                        indicatoron = False, 
                        onvalue = True, 
                        offvalue = False, 
                        variable = self.pwr_configured_var,
                        state = "disabled",
                        borderwidth=0)
        pwr_configured_indicator.grid(row = 0, column = 1)
        pwr_configure = tk.Button(device_opt_frame, text = "Configure Output", command = lambda: self.configurePower())
        pwr_configure.grid(row=0, column=2)
        self.pwr_voltage = tk.DoubleVar()
        self.pwr_current = tk.DoubleVar()
        pwr_current_out = tk.Spinbox(device_opt_frame, state="readonly", textvariable = self.pwr_current)
        pwr_voltage_out = tk.Spinbox(device_opt_frame, state="readonly", textvariable = self.pwr_voltage)
        tk.Label(device_opt_frame, text="Current (A)").grid(row=0,column=3)
        tk.Label(device_opt_frame, text="Voltage (V)").grid(row=0,column=4)
        pwr_current_out.grid(row=1, column=3)
        pwr_voltage_out.grid(row=1,column=4)
        pwr_output_button = tk.Button(device_opt_frame, text = "Set Output", command = lambda: self.set_pwr_output())
        pwr_output_button.grid(row=2,column=2)
        valve_opt_frame = tk.LabelFrame(self.parent.experimentFrame, relief='sunken', text="Valve Control")
        valve_opt_frame.grid(row=2,column=0, sticky = 'nsew')
        tk.Label(valve_opt_frame, text="Valve 1").grid(row=0, column=0)
        tk.Label(valve_opt_frame, text="Valve 2").grid(row=0, column=1)

        self.valve_daq_pin = [tk.StringVar() for _ in range(2)]
        valve_opt = [ttk.Combobox(valve_opt_frame, 
                                  state='readonly', 
                                  values=self.daq_line_labels[16:29],
                                  textvariable = self.valve_daq_pin[i]) for i in range(2)]
        for i in range(2):
            valve_opt[i].grid(row=1,column=i)

        self.power_output_var = tk.BooleanVar()
        power_output_indicator = tk.Checkbutton(device_opt_frame, 
                        image = self.LED_OFF, 
                        selectimage = self.LED_ON, 
                        indicatoron = False, 
                        onvalue = True, 
                        offvalue = False, 
                        variable = self.power_output_var,
                        command= lambda: self.start_power_output(),
                        borderwidth=0)
        power_output_indicator.grid(row=2,column=1)
        self.voltage_set = tk.StringVar()
        self.current_set = tk.StringVar()
        ttk.Spinbox(device_opt_frame,
                    from_=0,
                    to=700,
                    textvariable=self.voltage_set,
                    ).grid(row=2,column=4)
        ttk.Spinbox(device_opt_frame,
                    from_=0,
                    to=2,
                    textvariable=self.current_set,
                    ).grid(row=2,column=3)
        
        self.valve_selected_var = [tk.BooleanVar() for _ in range(2)]

        for i in range(2):
            valve_rb = tk.Checkbutton(valve_opt_frame, text=f"Valve {i+1}", variable=self.valve_selected_var[i], command = lambda idx=i: self.on_valve_check(idx))
            valve_rb.grid(row=2,column=i)

        self.pin_monitor_frame = tk.LabelFrame(self.parent.experimentFrame, relief='sunken', text='Pin Maintenence Frame')
        self.pin_monitor_frame.grid(column=1, row=0, rowspan=3,sticky='nsew')
        tk.Button(self.pin_monitor_frame, text="Add Pin", command=self.add_pin_monitor).pack()
        self.pin_frames = {'Pin ID', ('Pin Frame', 'Pin Index')}

    class PinFrame(tk.LabelFrame):
        def __init__(self, parent, experiment, pin_id = None, relief = None, pin_type = None):
            self.experiment = experiment
            super().__init__(parent, text=pin_id, relief=relief)
            self.pin_id = tk.StringVar(pin_id)
            self.pin_type = tk.StringVar(pin_type)
            self.pin_value_options = {'do': self.experiment.enabled_do_channels,
                                      'di': self.experiment.enabled_di_channels,
                                      'ao': self.experiment.enabled_ao_channels,
                                      'ai': self.experiment.enabled_ai_channels,
                                      '': ['no type selected']
            }
            self.pin_type_cbox = ttk.Combobox(self, textvariable=self.pin_type, values=['do', 'di', 'ao', 'ai'])
            self.pin_type_cbox.pack(anchor='n')
            self.pin_id_cbox = ttk.Combobox(self, textvariable=self.pin_id, values=self.pin_value_options[self.pin_type.get()])
            self.pin_id_cbox.pack()
            tk.Button(self, text='delete', command=self.destroy).pack(anchor='w')
            tk.Button(self, text = 'refresh', command=self.refresh_enabled_pins).pack(anchor='e')

        def refresh_enabled_pins(self):
            self.pin_id_cbox['values'] = self.pin_value_options[self.pin_type.get()]
    def add_pin_monitor(self):
        frame = self.PinFrame(self.pin_monitor_frame, experiment=self)
        frame.pack()
        


    def on_valve_check(self, idx):
        if self.pwr_voltage.get() < 26.8:
            self.valve_selected_var[idx].set(False)
            messagebox.showerror("No Power", "Insuffieicent Power to Valve PCB. Please Enable at least 27V to the board to continue")
            return
        if self.valve_selected_var[idx].get()==True:
            for i, var in enumerate(self.valve_selected_var):
                chan_name = self.valve_daq_pin[i].get()
                chan_index = self.daq_line_labels.index(chan_name)
                if i != idx:
                    var.set(False)
                    self.output_bool_vars[chan_index].set(False)
                elif i == idx:
                    if self.enable_var[chan_index].get() == False:
                        self.valve_selected_var[idx].set(False)
                        print(f"ERROR: output for {self.daq_line_labels[chan_index]} not enabled.")
                    else:
                        self.output_bool_vars[chan_index].set(True)
        elif self.valve_selected_var[idx].get()==False:
            chan_name = self.valve_daq_pin[idx].get()
            chan_index = self.daq_line_labels.index(chan_name)
            self.output_bool_vars[chan_index].set(False)

    def clean_exit(self):
        '''clean_exit() is used by the parent menu to intercept the "X' button at the top right and ensure that all 
        threads and open processes are closed before the UI quits'''
        if isinstance(self.PWR, VisaDevice):
            if self.PWR.name == "Power_TL":
                self.PWR.open_device()
                self.PWR.resource.write("OUTP:STAT:IMM OFF")
                self.PWR.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
                self.PWR.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")
            self.PWR.close_device()
        for task in (self.do_task, self.ao_task, self.di_task, self.ai_task):
            if isinstance(task, nidaqmx.Task):
                    task.close()
        self.experiment_online.clear()
        self.parent.destroy()

    def configurePower(self):
        pwrName = self.pwr_cbox.get()
        if pwrName == "":
            messagebox.showerror("No Device Connected", "Power Device is not selected. Please select a power supply and try again")
            return
        else:
            self.PWR = self.parent.devices[pwrName][0]
            self.PWR.open_device()
            with self.visa_lock:
                self.PWR.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
                self.PWR.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")
            self.pwr_configured_var.set(True)
            self.experiment_online.set()
            print(self.PWR)
            pwr_read = Thread(target= lambda: self.measurePower(), daemon= True)
            pwr_read.start()
            #self.PWR.close_device() 

    def measurePower(self):
        if(self.pwr_configured_var.get()==True):
            print("Thread Starting")
            while(self.experiment_online.is_set()):
                with self.visa_lock:
                    self.parent.after(1, self.pwr_voltage.set(self.PWR.resource.query("MEAS:SCAL:VOLT:DC?")))
                    self.parent.after(1, self.pwr_current.set(self.PWR.resource.query("MEAS:SCAL:CURR:DC?")))
                time.sleep(1)
        
    def check_IO(self):
        '''This method adds the resources from the pyvisa resource manager to the dropdown boxes'''
        IO_opts = ["Refresh"]
        for i in self.rm.list_resources():
            if self.rm.list_resources_info()[i][4] == None:
                IO_opts.append(i)
            else:
                IO_opts.append(self.rm.list_resources_info()[i][4])
        return IO_opts

    def update_combo_box(self, cbox_name):
        '''When a dropdown box is set to refresh, it will refresh all of the dropdown boxes to new values using check_IO()'''
        IO_opts = self.check_IO()
        # Update the combo box with new resources
        if cbox_name.get() == "Refresh":
            self.pwr_cbox['values'] = IO_opts
            cbox_name.set("")
        else:
            self.parent.generate_configuration_frame(filename= cbox_name.get())
    
    def pin_output(self, i):
        
        print(self.output_bool_vars[i].get())
        if self.enable_var[i].get() == False:
            print(f"ERROR: output for {self.daq_line_labels[i]} not enabled.")
            self.output_bool_vars[i].set(0)
        else:
            if i > 15:
                self.daq_do_output()
                     
    def daq_do_output(self):
        output_bool_list = [False for _ in range(len(self.enabled_do_channels))]
        for j in range(16,28):
            chan_name = self.daq_line_labels[j]
            try:
                enabled_index = self.enabled_do_channels.index(chan_name)
                if self.output_bool_vars[j].get() == 1:
                    #print(f"{self.daq_line_labels[j]} output started")
                    output_bool_list[enabled_index]=True
                elif self.output_bool_vars[j].get() == 0:
                    #print(f"{self.daq_line_labels[j]} output stopped")
                    pass     
            except ValueError:
                pass
        #print(output_bool_list)
        self.do_task.write(output_bool_list, auto_start=True, timeout=3)

    def pin_enable(self, i):
        if self.enable_var[i].get() == False:
            self.output_bool_vars[i].set(0)
            print(f"{self.daq_line_labels[i]} disabled")
            if i in range(16,28):
                #do output/input pins
                self.daq_do_output()
                self.enabled_do_channels.remove(self.daq_line_labels[i])
            elif i in range(13,15):
                self.enabled_ao_channels.remove(self.daq_line_labels[i])
            elif i in range(0,13):
                self.enabled_ai_channels.remove(self.daq_line_labels[i])
        elif self.enable_var[i].get() == True:
            print(f"{self.daq_line_labels[i]} enabled")
            if i in range(16,28):
                #do output/input pins
                self.enabled_do_channels.append(self.daq_line_labels[i])
            elif i in range(13,15):
                self.enabled_ao_channels.append(self.daq_line_labels[i])
            elif i in range(0,13):
                self.enabled_ai_channels.append(self.daq_line_labels[i])
            
        if i > 15:
            if isinstance(self.do_task, nidaqmx.Task):
                self.do_task.close()
            self.do_task = nidaqmx.Task()
            for chan in self.enabled_do_channels:
                self.do_task._do_channels.add_do_chan("NI_DAQ"+chan)
            print(self.do_task.do_channels.channel_names)
        elif i < 12:
            if isinstance(self.ai_task, nidaqmx.Task):
                self.ai_task.close()
            self.ai_task = nidaqmx.Task()
            for chan in self.enabled_ai_channels:
                self.ai_task.ai_channels.add_ai_voltage_chan("NI_DAQ"+chan)
            print(self.ai_task.ai_channels.channel_names)
        elif i in range(13,15):
            if isinstance(self.ao_task, nidaqmx.Task):
                self.ao_task.close()
            self.ao_task = nidaqmx.Task()
            for chan in self.enabled_ao_channels:
                self.ao_task.ao_channels.add_ao_voltage_chan("NI_DAQ"+chan)
            print(self.ao_task.ao_channels.channel_names)
    
    def set_pwr_output(self):
        if self.pwr_configured_var.get() == True:
            init_c = self.current_set.get()
            init_v = self.voltage_set.get()
            with self.visa_lock:
                self.PWR.resource.write(f"SOUR:CURR:LEV:IMM:AMPL {init_c}")
                self.PWR.resource.write(f"SOUR:VOLT:LEV:IMM:AMPL {init_v}")
        else:
            messagebox.showerror("No Device Connected", "Power Device is not configured. Please configure a power supply and try again")
            return

    def start_power_output(self):
        if self.pwr_configured_var.get() == True:
            if self.power_output_var.get() == True:
                with self.visa_lock:
                    self.PWR.resource.write("OUTP:STAT:IMM ON")
            elif self.power_output_var.get() == False:
                with self.visa_lock:
                    self.PWR.resource.write("OUTP:STAT:IMM OFF")
        else:
            messagebox.showerror("No Device Connected", "Power Device is not configured. Please configure a power supply and try again")
            return


if __name__ == "__main__":
    #Automatically creates chamebr app and imports experiment
    #For this to work you will need to write in the file location of the current file as well as the file location of the configuration files
    chamber = ChamberApp()

    chamber.menubar.load_experiment("./BeAMED/BeAMED_Packet/transistorcontrol.py")
    
    for config in ["Power_TL.config"]:
        file = "./BeAMED/BeAMED_Packet/" + config
        chamber.generate_configuration_frame(filepath = file)

    chamber.mainloop()