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

#Labels
title_font = ("Times New Roman", 18, 'bold')
label_font = ('Times New Roman', 12, 'bold')
    #Config Labels
Config_Title = tk.Label(Config_Frame, text = "Configurations", font = title_font).place(relx=0.45,rely=0)
    #IO Labels
IO_Title = tk.Label(IO_Frame, text = "Input/Output Settings", font = title_font).place(relx=0.37,rely=0)
    
    #Display Labels
Display_Title = tk.Label(Disp_Frame, text = "Display", font = title_font).place(relx = 0.45, rely = 0)

#Buttons, Displays, and Configs
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
pwr_out_label = tk.Label(IO_Frame, text = 'Power Supply Output Mode', font = ('Times New Roman', 14, 'bold')).place(x=550, y=47)

    #Start/Stop Buttons
start_button = ttk.Button(Disp_Frame, text = 'START').place(x=25, y=390, width=200, height=100)
stop_button = ttk.Button(Disp_Frame, text = 'STOP').place(x=250, y=390, width=200, height=100)
    
    #Oscilloscope Plot
figure = Figure(dpi=100)
figure_canvas = FigureCanvasTkAgg(figure, Plot_Frame)
NavigationToolbar2Tk(figure_canvas,root)
axes = figure.add_subplot()
axes.set_title('Discharge Event Voltage vs Time')
axes.set_ylabel('Voltage')
axes.set_xlabel('Time')
figure_canvas.get_tk_widget().place(x=0,y=0, relheight=1, relwidth=1)


#Functions



root.mainloop()
