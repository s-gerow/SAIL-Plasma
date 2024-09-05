import pyvisa
import matplotlib as plt
import numpy as np 

def osc_cmd_builder(function, channel, values):
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
    return command_string

values = ["Channel 1", 1]

print(osc_cmd_builder("ATTN", "Channel 1", values))
print(osc_cmd_builder("OFST", "Channel 1", [0]))
print(osc_cmd_builder("VDIV", "Channel 1", [1]))
print(osc_cmd_builder("TDIV", "Channel 1", [5E-4]))
print(osc_cmd_builder("HPOS", "Channel 1", [0]))
print(osc_cmd_builder("TRMD", "Channel 1", ["NORM"]))
print(osc_cmd_builder("TRSE", "Channel 1", ["EDGE", "TI", 2E-8]))





































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