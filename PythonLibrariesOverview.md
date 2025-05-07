# Programming Lab Equipment with Python Overview
## Libraries:
* PyVISA
* nidaqmx
* tkinter
* threading

## PyVISA
The PyVISA library is a Python wrapper for the VISA library which already exists for C, Visual Basic, and G (LABVIEW). It allows you to communicate with instrumentation systems which use USB, ethernet, GPIB, VXI, PXI, or serial interfaces. While the specific programing commands will be dependent on the device, PyVISA provides a library to communicate with any devices which can be connected to the computer. For example, here is how you might communicate with a digital oscilloscope to read data.
```
rm = pyvisa.ResourceManager() 
osc = rm.open_resource("USB0::0xF4EC::0xEE38::SDSMMFCD4R9625::INSTR")
sample_rate = osc.query("SARA?")
time_inter = 1/float(sample_rate[0:-1])
tdiv = float(osc.query("TDIV?"))
offset = float(osc.query("C1:OFST?"))
vdiv = float(osc.query("C1:VDIV?"))
osc.write("C1:WF? DAT2")
wf = osc.read_raw()
osc.close()
```

## NI-DAQmx
The nidaqmx python package allows you to communicate with National Instruments (NI) Data Aquisition Devices (DAQs) through Python on Windows or Linux machines. It requires the computer to have the NI-DAQmx driver installed. If a physical or virtual NI-DAQ is connected to the computer then you are able to program it using Python. Here is an example of reading a differential analog signal from a pressure sensor.
```
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val=0, max_val=10, terminal_config=TerminalConfiguration.DIFF)
    task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai1", min_val=0, max_val=10, terminal_config=TerminalConfiguration.DIFF)

    task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
    
```