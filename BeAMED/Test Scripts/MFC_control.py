# coding: utf-8
from nidaqmx import Task
do_task = Task()
ao_task = Task()
ao_task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao0", min_val=0,max_val=15)
do_task._do_channels.add_do_chan("NI_DAQ/port1/line0")
do_task._do_channels.add_do_chan("NI_DAQ/port1/line1")
do_task.write([True, False], auto_start = True, timeout =3)
do_task.write([False, True], auto_start = True, timeout =3)
ao_task.write(3, auto_start = True, timeout=3)
ao_task.write(0, auto_start = True, timeout=3)
do_task.write([True, False], auto_start = True, timeout =3)
do_task.close()
do_task.write([True, False], auto_start = True, timeout =3)
ao_task.close()
ao_task.write(0, auto_start = True, timeout=3)

