#import system default packages
import sys
import subprocess
import importlib.metadata
import tkinter as tk
from tkinter import ttk
import time
from threading import Thread, Event
import logging

# Define additional required packages
required = {'pyvisa', 'matplotlib', 'numpy', 'nidaqmx'}
# Get installed packages
installed = {pkg.metadata['Name'].lower() for pkg in importlib.metadata.distributions()}
# Find missing packages
missing = required - installed
if missing:
    # Upgrade pip
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    # Install missing packages
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])


#Interface for Plasma Chamber
import pyvisa
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import numpy as np
import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType

#Matplotlib Config
matplotlib.use('TkAgg')

#Initialize Visa Resource Manager to Communicate with Oscilliscope
#We are using SIGLENT SDS1204X-E, commands can be found in the SDS1202X-E Programming Manual
rm = pyvisa.ResourceManager()

#Create GUI Window
root = tk.Tk()

#Logging
beamed_logger = logging.getLogger('BeAMED')
def start_log():
    handler = logging.FileHandler('debug.log', mode = 'w')
    handler.setLevel(logging.DEBUG)
    beamed_logger.addHandler(handler)
    beamed_logger.setLevel(logging.DEBUG)
    log_message("MAIN", "INFO", f"BeAMED Plasma Chamber debug log started")

def log_message(thread, level, message):
    beamed_logger.debug(f"{thread}: {time.strftime('%X', time.localtime())} - {level} - {message}")

#This intercepts the X button to guarentee when we close the app it properly ends threads and closes communication with devices to avoid causing IO and memory issues in the future.
def clean_exit():
    level = "INFO"
    thread = "MAIN"
    log_message(thread, level, "Cleaning up...")
    stop_all_event.set()
    rm.close()
    log_message(thread, level, "Quitting")
    root.destroy()

root.protocol('WM_DELETE_WINDOW', clean_exit) 


#Configure Window
root.title("Plasma Chamber 1.0")
scrnwidth = root.winfo_screenwidth()
scrnheight = root.winfo_screenheight()
root.geometry("%dx%d" % (scrnwidth,scrnheight))
root.pack_propagate(0)

#Threading Events
'''These events are for the start function to know when the threads have finished and it can move on to the next step.'''
class ExperimentEvent(Event, ):
    def __init__(self, pressure="", ps_voltage="", ps_current="", voltage_out=""):
        super().__init__()
        self.pressure = pressure
        self.ps_voltage = ps_voltage
        self.ps_current = ps_current
        self.voltage_out = voltage_out
    def experiment_output(self):
        output = [self.pressure, self.ps_voltage, self.ps_current, self.voltage_out]
        return output

discharge_event = ExperimentEvent()
stop_all_event = Event() #event for the stopping of functions manually. called by clicking the stop button
osc_configured = Event() #event to confirm oscilloscope has been configured
pwr_configured = Event()
pressure_configured =Event()
DMM_configured = Event()
visa_error = Event() #event to identify problems with pyvisa and related hardware
config_error = Event() #event to identify errors with the configuration of a device, primarily to locate incorrectly defined config settings


def check_events():
    '''Daemon thread to check for events in the backgournd to handle'''
    while not stop_all_event.is_set() and not discharge_event.is_set():
        thread = "EVENT"
        if visa_error.is_set():
            level = "ERROR"
            log_message(thread, level, "unable to find device, stopping process.")
            stop_all_event.set()
            visa_error.clear()


#Functions
def get_resource(alias):
    for resource_tuple in rm.list_resources_info().values():
        if alias in resource_tuple:
            return resource_tuple[3]

def read_pressure(event: stop_all_event):
    '''Thread to continuously read pressure voltages and convert to real pressure.'''
    thread = "PRESSURE"
    level = "INFO"
    log_message(thread, level, "starting continuous pressure reading")
    with nidaqmx.Task() as task:
        ai_channel = task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=1, max_val=8, terminal_config=TerminalConfiguration.RSE)
        task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
        
        while not event.is_set():
            pressure_sensor_voltage = np.array(task.read(100))
            unfiltered_avg = np.median(pressure_sensor_voltage)
            true_pressure = 10**(unfiltered_avg - 5)
            root.after(0, lambda: pressure_var.set(true_pressure))
            if event.is_set():
                level = "WARN"
                log_message(thread, level, "stop all event triggered")
                log_message(thread, level, f"Stopped Reading Pressure. Last Reading: {true_pressure}")
            if discharge_event.is_set():
                level = "INFO"
                log_message(thread, level, "discharge event triggered")
                discharge_event.pressure = true_pressure
                log_message(thread, level, f"Stopped Reading Pressure. Last Reading: {discharge_event.pressure}")
                break

def MFC_start():
    '''Function will run on MAIN after all external systems are configured. Function checks the pressure and activates MFC based on gas/target pressure settings to backfill chamber before experiment begins.'''
    #target_min_pressure.set(100)
    #target_exp_pressure.set(700)
    run_bool = True
    gas = "gas"
    state = 0

    with nidaqmx.Task() as task:
        ao_channel0 = task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao0", min_val=0,max_val=5)
        ao_channel1 = task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao1", min_val=0, max_val=5)
        if gas != "air":
            while run_bool:
                match state:
                    case 0:
                        print("case 0")
                        #if pressure.get() > target_min_pressure.get():
                        #    task.write([[0],[0]],auto_start=True, timeout=10)
                        #else:
                        #    state = 1
                    case 1:
                        print("case 1")
                        #if pressure.get() < target_exp_pressure.get():
                        #    task.write([[5],[3]],auto_start=True, timeout=10)
                        #else:
                        #    task.write([[0],[0]],auto_start=True, timeout=10)
                        #    state = 2
                    case 2:
                        print("case 2")
                        print("begin dischage")
                        time.sleep(2)
                        case = 0
                        run_bool = False
                        break

def configure_power():
    '''Thread to configure power supply. Non-daemonic, non-looping.'''
    thread = "PWR CFG"
    level = "INFO"

def configure_oscilloscope():
    '''Thread to configure oscilloscope. this is a non-daemonic, non-looping thread so it does can not be interrupted by the stop all function. '''
    thread = "OSC CFG"
    level = "INFO"
    osc_name = get_resource(osc_cbox.get())
    try: 
        osc = rm.open_resource(osc_name)
    except pyvisa.errors.VisaIOError:
        level = "ERROR"
        log_message(thread, level, "VisaIOError excepted: cannot continue until oscilloscope connected")
        visa_error.set()
        while visa_error.is_set():
            time.sleep(2)
    osc = rm.open_resource(osc_name)
    log_message(thread, level, f"connected to {osc.query('*IDN?')}")
    channel = channel_var.get()[0]+channel_var.get()[-1]
    log_message(thread, level, f"setting oscilloscope to channel {channel}")
    osc.write(channel+":ATTN 1")
    log_message(thread, level, f"setting vertical offset to {vert_off_var.get()} mV")
    osc.write(channel+":OFST "+vert_off_var.get()+"mV")
    log_message(thread, level, f"setting vertical range to {vert_range_var.get()} V")
    osc.write(channel+":VDIV "+vert_range_var.get()+"V")
    log_message(thread, level, f"setting timebase to {timebase_var.get()} S")
    osc.write("TDIV "+timebase_var.get()+"S")
    osc.write("HPOS 0S")
    if cont_osc_var.get() == "Enable":
        mode = "NORM"
    else:
        mode = "AUTO"
    log_message(thread, level, f"setting trigger mode to {mode}")
    osc.write("TRMD "+mode)
    log_message(thread, level, f"setting trigger level to {trigger_lvl_var.get()}V")
    log_message(thread, level, f"setting trigger edge slope to {trigger_slope_var.get()}")
    log_message(thread, level, f"setting trigger holdoff to {holdoff_var.get()}S")
    osc.write("TRSE EDGE,SR,"+channel+",HT,TI,HV,"+holdoff_var.get()+"S")
    osc.close()
    log_message(thread, level, "Oscilloscope Configured Successfully")

def configure_dmm():
    thread = "DMM CFG"
    level = "INFO"
    dmm_name = get_resource(dmm_cbox.get())
    log_message(thread, level, dmm_name)
    '''
    try: 
        dmm = rm.open_resource(dmm_name)
    except pyvisa.errors.VisaIOError:
        level = "ERROR"
        log_message(thread, level, "VisaIOError excepted: cannot continue until dmm connected")
        visa_error.set()
        while visa_error.is_set():
            time.sleep(2)
    dmm = rm.open_resource(dmm_name)
    log_message(thread, level, f"connected to {dmm.query('*IDN?')}")
    log_message(thread, level, f"configuring digital multimeter to defaults")
    #The following lines mirror the configuration in Labview
    dmm.write("RST")
    dmm.write(':SENS:FUNC "VOLT:DC"')
    dmm.write("SENS:VOLT:RANG:AUTO ON")
    #dmm.write(':SENS:VOLT:NPLC 1') #Default 1
    #dmm.write(':SENS:VOLT:LINE:SYNC OFF') #Default OFF
    #dmm.write("SENS:VOLT:AZER ON")#Default ON
    dmm.write('CALC:VOLT:LIM1:STAT OFF') #Default OFF
    dmm.write('CACL:VOLT:LIM1:CLE:AUTO OFF') #Limit Number in GUI is 1 (LIM_), Default ON
    dmm.write('CALC:VOLT:LIM1:LOW 0') #Because the voltage limit is disabled this should not be needed but may as well include it because maybe one day we do
    dmm.write('CALC:VOLT:LIM1:UPP 0')
    dmm.write('TRAC:FILL:MODE "defbuffer1"') #continuous fill
    dmm.write('TRAC:POIN "defbuffer1"') #Buffer Size 10\
    dmm.close()
    log_message(thread, level, f"dmm successfuly configured")
    '''

def start():
    '''This function defines the START Button which sets the configuartions for each device then begins the experiment.'''
    thread = "MAIN"
    level = "INFO"
    log_message(thread, level, "start input received. starting chamber process")
    stop_all_event.clear()
    Thread(target=check_events, daemon=True).start()
    global live_pressure
    live_pressure = Thread(target = read_pressure, args = (stop_all_event,))
    configure = Thread(target=configure_oscilloscope)
    configure.start()
    configure = Thread(target=configure_dmm)
    configure.start()
    live_pressure.start()


def stop_all():
    '''This function is attached to the STOP button and kills all threads and processes.'''
    thread = "MAIN"
    level = "WARN"
    log_message(thread, level, "stop input received")
    stop_all_event.set()
    log_message(thread, level, "stop event set, waiting for threads to finish")


def toggle_check_btn(btn, var):
    if var.get() == "Enable":
        btn.configure(text='T: Enable')
    elif var.get() == "Disable":
        btn.configure(text='F: Disable')

#Build Framwork
IO_Frame = tk.Frame(root, relief = "sunken", borderwidth=10)
IO_Frame.place(relx=0,rely=0, relwidth=0.45, relheight=0.5)

Disp_Frame = tk.Frame(root,relief='sunken', borderwidth=10)
Disp_Frame.place(relx = 0.45, rely = 0, relwidth=0.55, relheight=0.5)
Plot_Frame = tk.Frame(Disp_Frame, relief = 'raised', borderwidth=10)
Plot_Frame.place(relx=0.45, rely=0.3, relwidth=0.55, relheight=0.7)

Config_Frame = tk.Frame(root, relief = 'sunken', borderwidth=10)
Config_Frame.place(relx=0, rely=0.5, relwidth=1, relheight=0.5)
Config1_Frame = tk.Frame(Config_Frame, relief = 'sunken', borderwidth=10)
Config1_Frame.place(relx=0,rely=.07,relwidth=0.2,relheight=0.93)
Config2_Frame = tk.Frame(Config_Frame, relief = 'sunken', borderwidth=10)
Config2_Frame.place(relx=0.2,rely=.07,relwidth=0.2,relheight=0.93)
Config3_Frame = tk.Frame(Config_Frame, relief = 'sunken', borderwidth=10)
Config3_Frame.place(relx=0.4,rely=.07,relwidth=0.2,relheight=0.93)
Config4_Frame = tk.Frame(Config_Frame, relief = 'sunken', borderwidth=10)
Config4_Frame.place(relx=0.6,rely=.07,relwidth=0.2,relheight=0.93)
Config5_Frame = tk.Frame(Config_Frame, borderwidth=10)
Config5_Frame.place(relx=0.8,rely=.07,relwidth=0.2,relheight=0.93)

serial_config_frame = tk.Frame(Config2_Frame, relief = 'sunken', borderwidth=10, bg='dark grey')
serial_config_frame.place(x=75,y=75,width=200,height=275)

#Labels
title_font = ("Times New Roman", 18, 'bold')
label_font = ('Times New Roman', 12, 'bold')
    #Config Labels
Config_Title = tk.Label(Config_Frame, text = "Configurations", font = title_font).place(relx=0.45,rely=0)
Osc_config_title = tk.Label(Config1_Frame, text = "Configuration for O-Scope", font = title_font).place(relx=0.1,rely=0)
Osc_config_title = tk.Label(Config2_Frame, text = "Configuration for Power", font = title_font).place(relx=0.12,rely=0)
Osc_config_title = tk.Label(Config3_Frame, text = "Configuration for DMM", font = title_font).place(relx=0.15,rely=0)
Osc_config_title = tk.Label(Config4_Frame, text = "Configuration for Pressure", font = title_font).place(relx=0.1,rely=0)
    #IO Labels
IO_Title = tk.Label(IO_Frame, text = "Input/Output Settings", font = title_font).place(relx=0.37,rely=0)
    #Display Labels
Display_Title = tk.Label(Disp_Frame, text = "Experiment Output", font = title_font).place(relx = 0.45, rely = 0)

#Buttons, Displays, and Configs
true_image = tk.PhotoImage(width=15, height=15)
false_image = tk.PhotoImage(width=15, height = 15)
true_image.put(("lime"), to=(0,0,14,14))
false_image.put(("green"), to=(0,0,14,14))

trig_true_image = tk.PhotoImage(width=50, height=50)
trig_false_image = tk.PhotoImage(width=50, height=50)
trig_true_image.put(("lime"), to=(0,0,49,49))
trig_false_image.put(("green"), to=(0,0,49,49))

#I/O selection for Oscilloscope, Power, and Digital Multimeter
def check_IO():
    IO_opts = ["Refresh"]
    for i in rm.list_resources():
        if rm.list_resources_info()[i][4] == None:
            IO_opts.append(i)
        else:
            IO_opts.append(rm.list_resources_info()[i][4])
    return IO_opts

def update_combo_box(event, cbox_name):
    IO_opts = check_IO()
    # Update the combo box with new resources
    if cbox_name.get() == "Refresh":
        pwr_cbox['values'] = IO_opts
        osc_cbox['values'] = IO_opts
        dmm_cbox['values'] = IO_opts
        cbox_name.set("")

pwr_io_label = tk.Label(IO_Frame, text = 'VISA Power', font = label_font).place(x=25, y=50)
pwr_cbox = ttk.Combobox(IO_Frame, state = 'readonly', values = check_IO(),)
pwr_cbox.bind('<<ComboboxSelected>>', lambda event: update_combo_box(event, pwr_cbox))
pwr_cbox.place(x=25, y=75)

dmm_io_label = tk.Label(IO_Frame, text = 'VISA DMM', font = label_font).place(x=25, y=150)
dmm_cbox = ttk.Combobox(IO_Frame, state = 'readonly', values = check_IO())
dmm_cbox.bind('<<ComboboxSelected>>', lambda event: update_combo_box(event, dmm_cbox))
dmm_cbox.place(x=25, y=175)

osc_io_label = tk.Label(IO_Frame, text = 'VISA O-Scope', font = label_font).place(x=25, y=100)
osc_cbox = ttk.Combobox(IO_Frame, state = 'readonly', values = check_IO())
osc_cbox.bind('<<ComboboxSelected>>', lambda event: update_combo_box(event, osc_cbox))
osc_cbox.place(x=25, y=125)


cont_osc_var = tk.StringVar()
cont_osc_label = tk.Label(IO_Frame, text='Enable Continuous Acquisition O-Scope (T: Enable)', font = label_font).place(x=200, y=100)
cont_osc = ttk.Checkbutton(IO_Frame, 
                           text = 'T: Enable',
                           variable=cont_osc_var,
                           onvalue="Enable",
                           offvalue="Disable",
                           command= lambda: toggle_check_btn(cont_osc, cont_osc_var))
cont_osc.place(x=200, y=125)

auto_range_var = tk.StringVar()
auto_range_label = tk.Label(IO_Frame, text = 'Auto Range DMM (T: Enable)', font = label_font).place(x=200, y=150)
auto_range = ttk.Checkbutton(IO_Frame, 
                             text = 'T: Enable',
                             variable=auto_range_var,
                             onvalue="Enable",
                             offvalue="Disable",
                             command = lambda: toggle_check_btn(auto_range, auto_range_var))
auto_range.place(x=200, y=175)

v_out_var = tk.StringVar()
v_out_label = tk.Label(IO_Frame, text = 'Enable V-Output Power (T: Enable)', font = label_font).place(x=200, y=50)
v_out = ttk.Checkbutton(IO_Frame, 
                        text = 'T:Enable',
                        variable = v_out_var,
                        onvalue="Enable",
                        offvalue="Disable",
                        command= lambda: toggle_check_btn(v_out, v_out_var),
                        )
v_out.place(x=200, y=75)

    #Power Supply Out Settings
#Are CV mode and CC Mode mutually exclusive?
#Debug Command
def pwrbuttondebug():
    print(f"cv ={cv_var.get()},cc = {cc_var.get()}")
pwr_out_label = tk.Label(IO_Frame, text = 'Power Supply Output Mode', font = ('Times New Roman', 14, 'bold')).place(x=550, y=47)
cv_var = tk.IntVar()
CV_button = tk.Checkbutton(IO_Frame, 
                           text = "CV Mode", 
                           image = false_image, 
                           selectimage = true_image, 
                           indicatoron = False, 
                           onvalue = 1, 
                           offvalue = 0,
                           variable = cv_var, 
                           command = pwrbuttondebug
                           ).place(x=550, y=72)
CV_label = tk.Label(IO_Frame, text = "CV Mode", font = label_font).place(x=575, y=72)
cc_var = tk.IntVar()
CC_button = tk.Checkbutton(IO_Frame, 
                           text = "CC Mode", 
                           image = false_image,
                           selectimage = true_image, 
                           indicatoron = False, 
                           onvalue = 1, 
                           offvalue = 0,
                           variable = cc_var, 
                           command = pwrbuttondebug
                           ).place(x=685, y=72)
CC_label = tk.Label(IO_Frame, text = "CC Mode", font = label_font).place(x=710, y=72)
init_v_var = tk.StringVar()
initial_voltage_spinbox = ttk.Spinbox(IO_Frame,
                                      from_ = 0,
                                      to = 100000,
                                      textvariable=init_v_var
                                      ).place(x=550,y=150, width=100)
init_v_label = tk.Label(IO_Frame,
                        text = "Input Voltage (V)",
                        font = label_font
                        ).place(x=550, y=125)
current_var = tk.StringVar()
current_spinbox = ttk.Spinbox(IO_Frame,
                              from_ = 0,
                              to = 1000000,
                              textvariable = current_var
                              ).place(x=700, y=150, width=100)
current_label = tk.Label(IO_Frame,
                         text = "Current Level (0.5A)",
                         font = label_font
                         ).place(x=700, y=125)

    #Position of the plates
position_title = tk.Label(IO_Frame,
                          text = "Position Set-Up",
                          font = ('Times New Roman', 14, 'bold')
                          ).place(x=550, y=250)
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
                              )
pressure_spinbox.place(x=552, y=425, width=125)



    #Start/Stop Buttons
start_button = ttk.Button(Disp_Frame, text = 'START', command=start).place(x=25, y=390, width=200, height=100)
stop_button = ttk.Button(Disp_Frame, text = 'STOP',command=stop_all).place(x=250, y=390, width=200, height=100)

    #Event Triggerd Button
def discharge_triggered():  
    thread = "MAIN"
    level = "INFO"
    log_message(thread, level, "Discahrge Event Triggered. stopping process")
    discharge_event.set()  

triggered_var = tk.IntVar()
triggered_button = tk.Checkbutton(Disp_Frame, 
                                  text = "Event Triggered?", 
                                  image = trig_false_image, 
                                  selectimage = trig_true_image, 
                                  indicatoron = False, 
                                  onvalue = 1, 
                                  offvalue = 0, 
                                  variable = triggered_var, 
                                  command = discharge_triggered
                                  ).place(x=40, y=315)
trigger_label = tk.Label(Disp_Frame,
                         text = "Triggered\nEvent",
                         font = title_font
                         ).place(x=110, y=315)

    #Oscilloscope Plot
figure = Figure(dpi=100)
figure_canvas = FigureCanvasTkAgg(figure, Plot_Frame)
NavigationToolbar2Tk(figure_canvas,Disp_Frame).place(relx=0.45,rely=0.23, relwidth=0.35, relheight=0.07)
axes = figure.add_subplot()
axes.set_title('Discharge Plot')
axes.set_ylabel('Voltage')
axes.set_xlabel('Time')
figure_canvas.get_tk_widget().place(x=0,y=0, relheight=1, relwidth=1)

    #Output Spinboxes
pwr_output_label = tk.Label(Disp_Frame,
                            text = "Power Supply Voltage",
                            font = label_font
                            ).place(x=250,y=175)
pwr_current_label = tk.Label(Disp_Frame,
                             text = "Power Supply Current",
                             font = label_font
                            ).place(x=250,y=225)
voltage_out_label = tk.Label(Disp_Frame,
                             text = "Voltage Output",
                             font = label_font,
                             ).place(x=250,y=275)
pressure_out_label = tk.Label(Disp_Frame,
                              text = "Pressure (Torr)",
                              font = label_font,
                              ).place(x=250,y=325)
PS_voltage_var = tk.IntVar()
pwr_output_spnbx = tk.Spinbox(Disp_Frame,
                              from_=0,
                              to = 800,
                              textvariable=PS_voltage_var
                              ).place(x=250, y=200, width=125)
PS_current_var = tk.IntVar()
pwr_current_spnbx = tk.Spinbox(Disp_Frame,
                              from_=0,
                              to = 800,
                              textvariable=PS_current_var
                              ).place(x=250, y=250, width=125)
voltage_out_var = tk.IntVar()
voltage_out_spnbx = tk.Spinbox(Disp_Frame,
                              from_=0,
                              to = 800,
                              textvariable=voltage_out_var
                              ).place(x=250, y=300, width=125)
pressure_var = tk.IntVar()
pressure_output_spnbx = tk.Spinbox(Disp_Frame,
                              from_=0,
                              to = 800,
                              textvariable=pressure_var
                              ).place(x=250, y=350, width=125)

#O-Scope Config Options
reset_var = tk.StringVar()
reset_label = tk.Label(Config1_Frame,
                       text = 'Reset (False)',
                       font = label_font,
                       ).place(x=50,y=30)
reset_opt = ttk.Checkbutton(Config1_Frame, 
                            text="T: Enable",
                            variable=reset_var,
                            onvalue="Enable",
                            offvalue="Disable",
                            command= lambda: toggle_check_btn(reset_opt, reset_var))
reset_opt.place(x=50,y=60)
channel_var = tk.StringVar()
channel_label = tk.Label(Config1_Frame,
                         text = "Channel (1)",
                         font = label_font
                         ).place(x=200, y=30)
channel_spnbox = tk.Spinbox(Config1_Frame, 
                            values=['Channel 1', 'Channel 2', 'Channel 3', 'Channel 4'],
                            state='readonly',
                            textvariable = channel_var
                            )
channel_spnbox.place(x=200, y=60)
timebase_var = tk.StringVar()
timebase_label = tk.Label(Config1_Frame,
                          text = "Timebase (0.0005 s)",
                          font = label_font
                          ).place(x=50, y=80)
timebase_spnbox = tk.Spinbox(Config1_Frame,
                             textvariable=timebase_var,
                             from_=00,
                             to = 1,
                             increment=0.0001,
                             )
timebase_spnbox.place(x=50,y=105)
trigger_lvl_var = tk.StringVar()
trigger_lvl_label = tk.Label(Config1_Frame,
                             text = "Trigger Level (0.05 V)",
                             font = label_font
                             ).place(x=50, y=130)
trigger_lvl_spnbox = tk.Spinbox(Config1_Frame,
                                textvariable=trigger_lvl_var,
                                from_ = -1,
                                to = 1,
                                increment=0.001)
trigger_lvl_spnbox.place(x=50,y=155)
trigger_slope_var = tk.StringVar()
trigger_slope_label = tk.Label(Config1_Frame,
                               text = "Trigger Slope (0: Positive)",
                               font = label_font
                               ).place(x=50, y=180)
trigger_slope_spnbox = tk.Spinbox(Config1_Frame,
                                  textvariable=trigger_slope_var,
                                  values = ["Positive", "Negative", "Window"],
                                  state='readonly')
trigger_slope_spnbox.place(x=50, y=205)
timeout_var = tk.StringVar()
timeout_label = tk.Label(Config1_Frame,
                         text = "Timeout (600,000 ms)",
                         font = label_font
                         ).place(x=50, y=230)
timeout_spnbox = tk.Spinbox(Config1_Frame,
                            textvariable=timeout_var,
                           from_=0,
                           to = 10000000,
                           increment = 100
                           )
timeout_spnbox.place(x=50, y=255)
vert_off_var = tk.StringVar()
vert_off_label = tk.Label(Config1_Frame,
                          text = "Veritcal Offset (0 mV)",
                          font = label_font
                          ).place(x=50, y=280)
vert_off_spnbox = tk.Spinbox(Config1_Frame,
                             from_=0,
                             to=100,
                             textvariable=vert_off_var
                             )
vert_off_spnbox.place(x=50, y=305)
vert_range_var = tk.StringVar()
vert_range_label = tk.Label(Config1_Frame,
                            text = "Vertical Range (0.15 V)",
                            font = label_font
                            ).place(x=50,y=330)
vert_range_spnbox = tk.Spinbox(Config1_Frame,
                               textvariable=vert_range_var,
                               from_ =0,
                               to = 100,
                               increment=0.01)
vert_range_spnbox.place(x=50, y=355)
holdoff_var = tk.StringVar()
holdoff_label = tk.Label(Config1_Frame,
                         text = "Holdoff Value (1E-7 s)",
                         font = label_font
                         ).place(x=50, y=380)
holdoff_spnbox = tk.Spinbox(Config1_Frame,
                            textvariable=holdoff_var,
                            from_ = 0,
                            to=1,
                            increment=1e-8)
holdoff_spnbox.place(x=50, y=405)
#Power Config 
config_frame_label = tk.Label(Config2_Frame,
                              text = "Serial Configuration Power",
                              font = label_font
                              ).place(x=75,y=50)
    #Baud Rate
baud_rate_label = tk.Label(serial_config_frame,
                           text = "Baud Rate",
                           bg = 'dark grey'
                           ).place(x=0,y=0)
    #Flow Control
flow_control_label = tk.Label(serial_config_frame,
                              text = "Flow Control",
                              bg = 'dark grey'
                              ).place(x=0, y=50)
    #Parity
parity_label = tk.Label(serial_config_frame,
                        text = "Parity",
                        bg = 'dark grey'
                        ).place(x=0, y=100)
    #Data Bits
data_bits_label = tk.Label(serial_config_frame,
                           text = "Data Bits",
                           bg = 'dark grey'
                           ).place(x=0, y=150)
    #Stop Bits
stop_bits_label = tk.Label(serial_config_frame,
                           text = "Stop Bits",
                           bg = 'dark grey'
                           ).place(x=0, y=200)
    #Voltage Step Size
voltage_set_label = tk.Label(Config2_Frame,
                             text = "Voltage Step Size (0.5 V)",
                             font = label_font
                             ).place(x=75, y=350)

#Dmm Config
    #Function
function_label = tk.Label(Config3_Frame,
                          text = "Function (0: Voltage DC)",
                          font = label_font,
                          ).place(x=75,y=25)
    #Reading Buffer
reading_buffer_label = tk.Label(Config3_Frame,
                                text = "Reading Buffer (debugger1)",
                                font = label_font
                                ).place(x=75,y=75)
    #Buffer Size
buffer_size_label = tk.Label(Config3_Frame,
                             text = "Buffer Size (10)",
                             font = label_font
                             ).place(x=75, y=125)
    #Manual Range
manual_range_label = tk.Label(Config3_Frame,
                              text = "Manual Range (0)",
                              font = label_font
                              ).place(x=75, y=175)
    #Auto Zero
auto_zero_label = tk.Label(Config3_Frame,
                           text = "Auto Zero (0:Enable)",
                           font = label_font
                           ).place(x=75, y=225)
    #Limit Number
limit_num_label = tk.Label(Config3_Frame,
                            text = "Limit Number (1: Limit 1)",
                            font = label_font
                            ).place(x=75, y=275)
    #Enable Limit

    #Lower Limit
lower_lim_label = tk.Label(Config3_Frame,
                           text = "Lower Limit (0)",
                           font = label_font
                           ).place(x=75,y=375)
    #Upper Limit
upper_lim_label = tk.Label(Config3_Frame,
                           text = "Upper Limit (0)",
                           font = label_font
                           ).place(x=200, y=375)


#Pressure Config
    #PS initial Voltage
PS_init_v_label = tk.Label(Config4_Frame,
                           text = 'Initial Pressure Voltage',
                           font = label_font,
                           ).place(x=75, y=50)
    #PS Initial Torr
PS_init_torr_label = tk.Label(Config4_Frame,
                              text = "Initial Pressure Torr",
                              font = label_font,
                              ).place(x=75, y=100)
    #median PS voltage
PS_median_v = tk.Label(Config4_Frame, 
                       text = "Median Pressure Voltage",
                       font = label_font
                       ).place(x=75, y=150)
    #filter type
filter_type_label = tk.Label(Config4_Frame,
                             text = "Filter Type (LP)",
                             font = label_font
                             ).place(x=75, y=200)
    #sampling freq
sampling_freq = tk.Label(Config4_Frame,
                         text = "Sampling Freq (100.00)",
                         font = label_font
                         ).place(x=75, y=250)
    #HFC
HFC_label = tk.Label(Config4_Frame,
                     text = "HFC (25.00)",
                     font = label_font
                     ).place(x=75, y=300)
    #LFC
LFC_label = tk.Label(Config4_Frame,
                     text = "LFC (10.00)",
                     font = label_font
                     ).place(x=200,y=300)
    #number of samples
sample_number_label = tk.Label(Config4_Frame,
                               text = "Number of Samples (100)",
                               font = label_font
                               ).place(x=75, y=350)

start_log()
root.mainloop()