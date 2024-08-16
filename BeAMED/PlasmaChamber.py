def read_pressure(event: stop_all_event):
    '''Thread to continuously read pressure voltages and convert to real pressure.'''
    thread = "PRESSURE"
    level = "INFO"
    while True:
        with nidaqmx.Task() as task:
            ai_channel = task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val = 1, max_val = 8, terminal_config=TerminalConfiguration.RSE)
            task.timing.cfg_samp_clk_timing(rate = 1000, sample_mode=AcquisitionType.FINITE,samps_per_chan=100)
            pressure_sensor_voltage=np.array(task.read(100))
            #sos = signal.butter(2, 1, btype = "lowpass", analog = True, output='sos')
            #filtered = signal.sosfilt(sos, pressure_sensor_voltage)
            #filtered_avg = np.median(filtered)
            unfiltered_avg = np.median(pressure_sensor_voltage)
            true_pressure = 10**(unfiltered_avg-5)
            pressure_var.set(true_pressure)
        if event.is_set():
            level = "WARN"
            log_message(thread, level, "stop all event triggered")
            log_message(thread, level, f"Stopped Reading Pressure. Last Reading: {true_pressure}")
            break

def configure_power(ID, event: stop_all_event):
    '''Thread to read through '''
    thread = "PWR CFG"
    level = "INFO"
def configure_oscilloscope(event: stop_all_event):
    '''Thread to configure oscilloscope this is a non-daemonic, non-looping thread so it does can not be interrupted by the stop all function. '''
    thread = "OSC CFG"
    level = "INFO"
    try: 
        osc = rm.open_resource(osc_cbox.get())
    except pyvisa.errors.VisaIOError:
        level = "ERROR"
        log_message(thread, level, "VisaIOError excepted: stopping process")
        stop_all_event.set()
        return
    osc = rm.open_resource(osc_cbox.get())
    print(osc.query('*IDN?'))
    return

def start():
    '''This function defines the START Button which sets the configuartions for each device then begins the experiment.'''
    stop_all_event.clear()
    start_log()
    live_pressure = Thread(target = read_pressure, args = (stop_all_event,), daemon=True)
    configure = Thread(target=configure_oscilloscope, args = (stop_all_event,))
    configure.start()
    live_pressure.start()
    
    #if reset_opt.getvar != "Disable":
    #   raise ValueError("oscilloscope reset is enabled")


def stop_all():
    '''This function is attached to the STOP button and kills all threads and processes.'''
    thread = "MAIN"
    level = "WARN"
    print(f"{active_count()}")
    log_message(thread, level, "stop input received, stopping daemonic threads")
    stop_all_event.set()
    print(f"{active_count()}")
    log_message(thread, level, "waiting for non-daemonic threads to finish")
    while active_count() !=1:
        print(f"{active_count()}")
        for thread in threading.enumerate():
            print(thread.name)
        print(f"{stop_all_event.is_set()}")
        time.sleep(3)
    log_message(thread, level, "all other threads stopped")
