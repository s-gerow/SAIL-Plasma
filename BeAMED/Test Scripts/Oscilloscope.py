import pyvisa
import matplotlib as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import numpy as np 
import tkinter as tk
from tkinter import ttk
import sys


class Oscilloscope_Figure_Maker(tk.Tk):
    def __init__(self):
        super().__init__()

        self.rm = pyvisa.ResourceManager()

        self.geometry('600x600')
        self.title('Test Oscilloscope Get Waveform')

        self.button_frame = tk.Frame(self,relief='sunken')
        self.button_frame.pack(side = 'left')

        self.figure_frame = tk.Frame(self, relief='raised')
        self.figure_frame.pack(side='left')


        self.figure = Figure(dpi=100)
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self.figure_frame)
        NavigationToolbar2Tk(self.figure_canvas,self.figure_frame).pack(side='top')
        self.axes = self.figure.add_subplot()
        self.axes.set_title('Discharge Plot')
        self.axes.set_ylabel('Voltage')
        self.axes.set_xlabel('Time')
        self.figure_canvas.get_tk_widget().pack(side='top')

        device_opt_label = tk.Label(self.button_frame, text = 'Oscilloscope').pack(side = 'top')
        self.device_cbox = ttk.Combobox(self.button_frame, state = 'readonly', values = self.check_IO(),)
        self.device_cbox.bind('<<ComboboxSelected>>', lambda event: self.update_combo_box(event, self.device_cbox))
        self.device_cbox.pack(side = 'top')

        run_button = tk.Button(self.button_frame, text="Run", command=self.run_plot)
        run_button.pack(side='top')

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
            self.device_cbox['values'] = IO_opts
            cbox_name.set("")

    def get_resource(self, alias):
        for resource_tuple in self.rm.list_resources_info().values():
            if alias in resource_tuple:
                return resource_tuple[3]

    def osc_cmd_builder(self, function, channel, values):
        channel = channel[0]+channel[-1]
        match function:
            case "ATTN":
                '''values = [attenuation_factor,]'''
                command_string = channel+":"+function+":"+str(values[0])
            case "OFST":
                '''values = [voltage_offset]'''
                command_string = channel+":"+function+" "+str(values[0])+"V"
            case "VDIV":
                '''values = [vertical_sensitivity]'''
                command_string = channel+":"+function+" "+str(values[0])+"V"
            case "TDIV":
                '''values = [horizontal_scale'''
                command_string = function+" "+str(values[0])+"S"
            case "HPOS":
                '''values = [horizontal_position]'''
                command_string = function+" "+str(values[0])+"S"
            case "TRMD":
                '''values = [trigger_mode]'''
                command_string = function+" "+values[0]
            case "TRSE":
                '''values = [trigger_type, hold_type, hold_value]'''
                command_string = function+" "+values[0]+",SR,"+channel+",HT,"+values[1]+",HV,"+str(values[2])+"S"
            case "TRLV":
                command_string = channel+":"+function+" "+str(values[0])+"V"
        return command_string

    def run_plot(self):
        self.axes.clear()
        osc = self.rm.open_resource(self.get_resource(self.device_cbox.get()))

        osc.write(self.osc_cmd_builder("ATTN", "Channel 1", [1]))
        #osc.write(osc_cmd_builder("OFST", "Channel 1", [0]))
        osc.write(self.osc_cmd_builder("VDIV", "Channel 1", [0.15]))
        osc.write(self.osc_cmd_builder("TDIV", "Channel 1", [5E-4]))
        osc.write(self.osc_cmd_builder("HPOS", "Channel 1", [0]))
        #osc.write(osc_cmd_builder("TRMD", "Channel 1", ["NORM"]))
        #osc.write(osc_cmd_builder("TRLV", "Channel 1", [0.05]))
        #osc.write(osc_cmd_builder("TRSE", "Channel 1", ["EDGE", "TI", 1E-7]))

        osc.write('DATASOURCE CHANNEL1')
        osc.write('DATA:ENCDG SRI')
        osc.write('DATA:WIDTH 2')
        osc.write('DATA:START 0')
        osc.write('DATA: STOP 1000')

        
        sample_rate = osc.query("SARA?")
        time_inter = 1/float(sample_rate[0:-1])
        tdiv = float(osc.query("TDIV?"))
        offset = float(osc.query("C1:OFST?"))
        vdiv = float(osc.query("C1:VDIV?"))
        osc.write("C1:WF? DAT2")
        wf = osc.read_raw()
        osc.close()
        wf = wf[16:-2]

        hgrid = 14

        decimal = []
        for i,byte in enumerate(wf):
            decimal.append(int.from_bytes(wf[i:i+1], byteorder=sys.byteorder))
        data = np.array(decimal)
        time = np.flip(np.array([(tdiv*hgrid)-(idx*time_inter) for idx in range(0,data.size) ]))

        voltage_data = np.array([int(code)*(vdiv/25)-offset if int(code) < 127 else (int(code)-256)*(vdiv/25)-offset for code in data])

        self.axes.plot(time, voltage_data)

        self.figure_canvas.draw()








if __name__ == "__main__":
    app = Oscilloscope_Figure_Maker()
    app.mainloop()





































'''
rm = pyvisa.ResourceManager()
print(rm.list_resources())
try: 
    osc = rm.open_resource('USB0::0xF4EC::0xEE38::SDSMMFCD4R9625::INSTR')
except pyvisa.errors.VisaIOError:
    print("VISA IO Excepted Turn it on")
print(osc.query("C1:ATTN?"))
print(osc.query("C1:OFFSET?"))
print(osc.query("C1:VOLT_DIV?"))
print(osc.query("TIME_DIV?"))
print(osc.query("HOR_POSITION?"))
print(osc.query("ACQUIRE_WAY?"))
print(osc.query("TRIG_MODE?"))
print(osc.query("TRIG_SELECT?"))

osc.write('CHDR OFF')
print(osc.query('*IDN?'))
print(osc.query('GRID_DISPLAY?'))
osc.write('GRDS FULL')
print(osc.query('GRID_DISPLAY?'))
osc.write('TDIV 5E-4S')
print(osc.query('TIME_DIV?'))
print(osc.query('C1:TRIG_LEVEL?'))
print(osc.query('TRIG_SELECT?'))
osc.write('TRSE EDGE,SR,C1,HT,TI,HV,2E-8S')
print(osc.query('TRIG_SELECT?'))
print(osc.query('C1:TRIG_SLOPE?'))


osc.write('HORizontal:MAIn:SCAle 00.01')
osc.write('CH1:SCAle 0.2')
osc.write('DATASOURCE CHANNEL1')
osc.write('DATA:ENCDG SRI')
osc.write('DATA:WIDTH 2')
osc.write('DATA:START 0')
osc.write('DATA: STOP 1000')
data_ch1 = osc.query_ascii_values('CURVE?', container=np.array)


plt.figure(figsize=(10,6))
plt.plot(data_ch1)
plt.title('osc wave')
plt.xlabel('t')
plt.ylabel('v')
plt.grid(True)
plt.show()





osc.close()
rm.close()
'''