import pyvisa
import tkinter as tk
from threading import Thread
import numpy as np
import time

root = tk.Tk()

rm = pyvisa.ResourceManager()
DMM_name = 'USB0::0x05E6::0x6500::04386498::0::INSTR'
PWR_name = 'ASRL3::INSTR'

init_voltage = 0
volt_step = 0.5
max_volt = 20

dmm = rm.open_resource(DMM_name)
pwr = rm.open_resource(PWR_name)

print(pwr.query("*IDN?"))

pwr.write(f"SOUR:CURR:PROT:LEV {1}")
pwr.write("SOUR:VOLT:PROT:LEV 20")
pwr.write("SOUR:CURR:LEV:IMM:AMPL 0.5")

#The following lines mirror the configuration in Labview
dmm.write("*RST")
dmm.write(':SENS:FUNC "VOLT:DC"')
dmm.write(":SENS:VOLT:RANG:AUTO ON")
##dmm.write(':SENS:VOLT:NPLC 1') #Default 1
##dmm.write(':SENS:VOLT:LINE:SYNC OFF') #Default OFF
##dmm.write("SENS:VOLT:AZER ON")#Default ON
dmm.write(':CALC2:VOLT:LIM1:STAT OFF') #Default OFF
dmm.write(':CALC2:VOLT:LIM1:CLE:AUTO OFF') #Limit Number in GUI is 1 (LIM_), Default ON
dmm.write(':CALC2:VOLT:LIM1:LOW 0') #Because the voltage limit is disabled this should not be needed but may as well include it because maybe one day we do
dmm.write(':CALC2:VOLT:LIM1:UPP 0')
dmm.write(':TRAC:FILL:MODE CONT, "defbuffer1"') #continuous fill
dmm.write(':TRAC:POIN 10, "defbuffer1"') #Buffer Size 10


def increase_voltage():
    pwr.write("OUTP:STAT:IMM ON")
    for i in np.arange(0,5,0.25):
        pwr.write(f"SOUR:VOLT:LEV:IMM:AMPL {i}")
        root.after(0, lambda: voltage_level_var.set(pwr.query("SOUR:VOLT:LEV:IMM:AMPL?")))
        #root.after(0, lambda: voltage_level_var.set(i))
        root.after(0, lambda: dmm_reading_var.set(dmm.query(":READ?")))
        time.sleep(0.5)
    for i in np.flip(np.arange(0, 5, 0.25)):
        pwr.write(f"SOUR:VOLT:LEV:IMM:AMPL {i}")
        root.after(0, lambda: voltage_level_var.set(pwr.query("SOUR:VOLT:LEV:IMM:AMPL?")))
        #root.after(0, lambda: voltage_level_var.set(i))
        root.after(0, lambda: dmm_reading_var.set(dmm.query(":READ?")))
        time.sleep(0.5)
    pwr.write("SOUR:VOLT:LEV:IMM:AMPL 0")
    pwr.write("OUTP:STAT:IMM OFF")
    dmm.close()
    pwr.close()
    rm.close()
    root.destroy()

voltage_thread = Thread(target=increase_voltage, daemon = True)

voltage_level_var = tk.StringVar()
tk.Label(root, text = "voltage output").grid(row = 1, column = 1, padx = 5, pady = 5)
tk.Spinbox(root,
           textvariable=voltage_level_var).grid(row = 1, column = 2, padx = 5, pady = 5)

dmm_reading_var = tk.StringVar()
tk.Label(root, text = "dmm voltage reading").grid(row = 2, column = 1, padx=5, pady=5)
tk.Spinbox(root,
           textvariable=dmm_reading_var).grid(row = 2, column = 2, padx = 5, pady = 5)

start = tk.Button(text = "start", command = voltage_thread.start).grid(row=3, column = 1, padx = 5, pady = 5)


def clean_exit():
    pwr.write("ABOR")
    pwr.write("SOUR:VOLT:LEV:IMM:AMPL 0")
    pwr.write("OUTP:STAT:IMM OFF")
    dmm.close()
    pwr.close()
    rm.close()
    root.destroy()

root.protocol('WM_DELETE_WINDOW', clean_exit) 

root.mainloop()