#Interface for Plasma Chamber
import tkinter as tk
from tkinter import ttk
import pyvisa
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

#Matplotlib Config
matplotlib.use('TkAgg')

#Initialize Visa Resource Manager
rm = pyvisa.ResourceManager()

#Create GUI Window
root = tk.Tk()

#Configure Window
root.title("Plasma Chamber 1.0")
scrnwidth = root.winfo_screenwidth()
scrnheight = root.winfo_screenheight()
root.geometry("%dx%d" % (scrnwidth,scrnheight))
root.pack_propagate(0)

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
IO_opts = rm.list_resources()
pwr_io_label = tk.Label(IO_Frame, text = 'VISA Power', font = label_font).place(x=25, y=50)
pwr_cbox = ttk.Combobox(IO_Frame, state = 'readonly', values = IO_opts).place(x=25, y=75)
v_out_label = tk.Label(IO_Frame, text = 'Enable V-Output Power', font = label_font).place(x=200, y=50)
v_out = ttk.Checkbutton(IO_Frame, text = 'T:Enable').place(x=200, y=75)

osc_io_label = tk.Label(IO_Frame, text = 'VISA O-Scope', font = label_font).place(x=25, y=100)
osc_cbox = ttk.Combobox(IO_Frame, state = 'readonly', values = IO_opts).place(x=25, y=125)
cont_daq_label = tk.Label(IO_Frame, text='Enable Continuous Acquisition O-Scope', font = label_font).place(x=200, y=100)
cont_daq = ttk.Checkbutton(IO_Frame, text = 'T: Enable').place(x=200, y=125)

dmm_io_label = tk.Label(IO_Frame, text = 'VISA DMM', font = label_font).place(x=25, y=150)
dmm_cbox = ttk.Combobox(IO_Frame, state = 'readonly', values = IO_opts).place(x=25, y=175)
auto_range_label = tk.Label(IO_Frame, text = 'Auto Range DMM', font = label_font).place(x=200, y=150)
auto_range = ttk.Checkbutton(IO_Frame, text = 'T: Enable').place(x=200, y=175)

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
                              ).place(x=552, y=425, width=125)
    #Start/Stop Buttons
start_button = ttk.Button(Disp_Frame, text = 'START').place(x=25, y=390, width=200, height=100)
stop_button = ttk.Button(Disp_Frame, text = 'STOP').place(x=250, y=390, width=200, height=100)
    
    #Event Triggerd Button
def triggerdebug():
    print(triggered_var.get())
triggered_var = tk.IntVar()
triggered_button = tk.Checkbutton(Disp_Frame, 
                                  text = "Event Triggered?", 
                                  image = trig_false_image, 
                                  selectimage = trig_true_image, 
                                  indicatoron = False, 
                                  onvalue = 1, 
                                  offvalue = 0, 
                                  variable = triggered_var, 
                                  command = triggerdebug
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
pwr_supply_voltage = tk.StringVar()
pwr_supply_current = tk.StringVar()
voltage_output = tk.StringVar()
pressure_output = tk.StringVar()
pwr_output_label = tk.Label(Disp_Frame,
                            text = "Power Supply Voltage",
                            font = label_font
                            ).place(x=250,y=215)
pwr_current_label = tk.Label(Disp_Frame,
                             text = "Power Supply Current",
                             font = label_font
                            ).place(x=250,y=240)
voltage_out_label = tk.Label(Disp_Frame,
                             text = "Voltage Output",
                             font = label_font,
                             ).place(x=250,y=265)
pressure_out_label = tk.Label(Disp_Frame,
                              text = "Pressure (Torr)",
                              font = label_font,
                              ).place(x=250,y=340)


#Functions



root.mainloop()
