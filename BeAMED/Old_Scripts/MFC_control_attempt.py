# coding: utf-8
import nidaqmx
ao_task = nidaqmx.Task()
ai_task = nidaqmx.Task()
do_task = nidaqmx.Task()
ao_task.ao_channels.add_ao_voltage_chan("NI_DAQ/ao1", name_to_assign_to_channel="SetPointInput", min_val=0, max_val=5)
ai_task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai3", name_to_assign_to_channel="ValveTestPoint", min_val=0, max_val=5, terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
ai_task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai7", name_to_assign_to_channel="FlowSignal", min_val=0, max_val=5, terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
do_task.do_channels.add_do_chan("NI_DAQ/port1/line0", name_to_assign_to_lines="ValveOpen")
do_task.do_channels.add_do_chan("NI_DAQ/port1/line1", name_to_assign_to_lines="ValveClose")
do_task.do_channels[0].name
valve_open_chan = do_task.do_channels[0]
valve_close_chan = do_task.do_channels[1]
valve_close_chan.get_do_output_drive_type(valve_close_chan._handle, valv_close_chan.name)
do_task.channels.DOChannel(valve_open_chan._handle, valve_open_chan.name)
do_task.DOChannel(valve_open_chan._handle, valve_open_chan.name)
do_task.channels(valve_open_chan._handle, valve_open_chan.name)
do_task.channels.do_output_drive_type
do_task.channels.do_output_drive_type.get()
do_task.channels.do_output_drive_type = nidaqmx.constants.DigitalDriveType.OPEN_COLLECTOR
do_task.channels.do_output_drive_type
do_task.channels
do_task.channels[0]
do_task.channels.ValveOpen
do_task.channels("ValveOpen")
valve_open_chan.do_output_drive_type
valve_close_chan.do_output_drive_type
valve_close_chan.do_output_drive_type=nidaqmx.constants.DigitalDriveType.ACTIVE_DRIVE
valve_close_chan.do_output_drive_type
valve_open_chan.do_output_drive_type
valve_close_chan.do_output_drive_type=nidaqmx.constants.DigitalDriveType.OPEN_COLLECTOR
do_task.channels.do_output_drive_type
ai_task.read()
do_task.channels
do_task.write([True, False], auto_start = True, timeout = 3)
ai_task.read()
do_task.write([False, True], auto_start = True, timeout = 3)
ai_task.read()
ao_task.write(2.5, auto_start=True)
ai_task.read()
do_task.write([False, True], auto_start = True, timeout = 3)
ao_task.write(5, auto_start=True)
ai_task.read()
ai_task.read()
ai_task.read()
ao_task.write(0, auto_start=True)
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.channls
ai_task.channels
do_task.write([True, False], auto_start = True, timeout = 3)
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
ai_task.read()
do_task.write([False, True], auto_start = True, timeout = 3)
ai_task.read()
ai_task.read()
ao_task.write(2.5, auto_start=True)
ai_task.read()
ai_task.read()
