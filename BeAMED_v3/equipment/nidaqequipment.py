import time
import threading
import logging
import numpy as np
import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
from nidaqmx.stream_readers import AnalogMultiChannelReader
import nidaqmx.constants
from typing import Literal

from datatypes import PressureTimeseries, MFCTimeseries
from equipment.baseequipment import Equipment

class NIDAQEquipment(Equipment):
    def __init__(self, name: str = "nidaq", device_id="NI_DAQ", kp: float = 1.0, ki: float = 0.1, abort_event: threading.Event | None = None):
        super().__init__(name, abort_event)
        self.logger = logging.getLogger("BeAMED.nidaq")
        self.device_id = device_id
        self._task_lock = threading.Lock()
        self._abort_event = abort_event
        self.tasks: dict[str, nidaqmx.Task] = {}
        self._connected = False

        # subsystems
        self.pressure = subsystemPressure(self)
        self.mfc = subsystemMFC(self, ki, kp)
        self.valves = subsystemValve(self)
        self.feedthrough = subsystemFeedthrough(self)

    def connect(self):
        if self._connected:
            self.logger.warning("connect() called but already connected")
            return
        else:
            self.logger.info("Starting NIDAQ tasks")

            ai_cont = nidaqmx.Task()
            ai_cont.ai_channels.add_ai_voltage_chan(f"{self.device_id}/ai0",
                                                    name_to_assign_to_channel="KJL_pressure",
                                                    min_val=0,
                                                    max_val=10,
                                                    terminal_config=TerminalConfiguration.DIFF
                                                    )
            ai_cont.ai_channels.add_ai_voltage_chan(f"{self.device_id}/ai1",
                                                    name_to_assign_to_channel="MKS_pressure",
                                                    min_val=0,
                                                    max_val=10,
                                                    terminal_config=TerminalConfiguration.DIFF
                                                    )
            ai_cont.ai_channels.add_ai_voltage_chan(f"{self.device_id}/ai3",
                                                    name_to_assign_to_channel="MFC_flow",
                                                    min_val=0,
                                                    max_val=5,
                                                    terminal_config=TerminalConfiguration.DIFF
                                                    )
            self.tasks["ai_continuous"] = ai_cont

            ao = nidaqmx.Task()
            ao.ao_channels.add_ao_voltage_chan(f"{self.device_id}/ao1",
                                            name_to_assign_to_channel="MFC_setpoint",
                                            min_val=0,
                                            max_val=5
                                            )
            self.tasks["ao"] = ao

            self._connect_valves()

            self._connected = True
            self.logger.info("NIDAQ tasks configured")

    def _connect_valves(self):
        do_valves = nidaqmx.Task()
        do_valves.do_channels.add_do_chan(f"{self.device_id}/port0/line1", name_to_assign_to_lines="Vent")
        do_valves.do_channels.add_do_chan(f"{self.device_id}/port0/line0", name_to_assign_to_lines="MainPump")
        do_valves.do_channels.add_do_chan(f"{self.device_id}/port0/line2", name_to_assign_to_lines="SmallPump")
        self.tasks["do_valves"] = do_valves

    def _connect_feedthrough(self):
        do_feedthrough = nidaqmx.Task()
        do_feedthrough.do_channels.add_do_chan(f"{self.device_id}/port1/line3", name_to_assign_to_lines="PUL")
        do_feedthrough.do_channels.add_do_chan(f"{self.device_id}/port1/line2", name_to_assign_to_lines="DIR")
        self.tasks["do_feedthrough"] = do_feedthrough

    def _disconnect_valves(self):
        if self.tasks["do_valves"]:
            self.tasks["do_valves"].close()
            self.tasks.pop("do_valves")

    def _disconnect_feedthrough(self):
        if self.tasks["do_feedthrough"]:
            self.tasks["do_feedthrough"].close()
            self.tasks.pop("do_feedthrough")

    def disconnect(self):
        self.pressure.stop()
        self.mfc.stop_pi()
        try:
            self.valves.close_all()
        except KeyError:
            pass
        for name, task in self.tasks.items():
            try:
                task.close()
                self.logger.info(f"Closed task: {name}")
            except Exception as e:
                self.logger.exception(f"Error closing task {name}")
        self.tasks.clear()
        self._connected = False

    def getStatus(self) -> dict:
        p1, p2 = self.pressure.latest
        return {
            "Connected": self._connected,
            "KJL_pressure": p1,
            "MKS_pressure": p2,
            "MFC_flow": self.mfc.read_flow() if 'ai_poll' in self.tasks else None,
            "valve_states": self.valves.states,
            "feedthrough": self.feedthrough.get_status()
        }


    # Pressure Subsystem Wrappers
    def start_pressure_acquisition(self, stop_event: threading.Event | None = None, target_: float | None = None, target_trigger: Literal['rising', 'falling'] | None = None):
        self.pressure.start(stop_event=stop_event, target_=target_, target_trigger=target_trigger)

    def stop_pressure_acquisition(self):
        self.pressure.stop()

    def clear_pressure_buffer(self):
        self.pressure.clear_buffer()

    # MFC Subsystem Wrappers
    def set_flow(self, setpoint_volts: float):
        self.mfc.set_flow(setpoint_volts)

    def set_PI(self, kp:float, ki:float,pressure_torr:float):
        self.mfc.set_PI(kp, ki, pressure_torr)

    def start_PI(self, settled_event: threading.Event | None = None):
        self.mfc.start_pi(settled_event =settled_event)

    def stop_PI(self):
        self.mfc.stop_pi()

    # Feedthrough Subsystem Wrappers
    def step_feedthrough_cm(self, dir_: bool, cm: float, trigger_event: threading.Event | None = None, stop_event: threading.Event | None = None):
        self.feedthrough._step_for_cm(dir_, cm, trigger_event, stop_event)

    def step_feedthrough(self, dir_: bool):
        self.feedthrough._step(dir_)

    def start_feedthrough(self, dir_: bool, stop_event: threading.Event):
        self.feedthrough._step_until(dir_ = dir_, stop_event=stop_event)

    # Valve Subsystem Wrappers
    def open_valve(self, valve: int):
        self.valves.close_all()
        self.valves.open(valve)

    def close_valves(self):
        self.valves.close_all()

class subsystemPressure:
    def __init__(self, parent:NIDAQEquipment):
        self._parent = parent
        self.logger = logging.getLogger("BeAMED.nidaq.pressure")
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        self.pressure_min = 0.11 #Torr #MKS Sensor
        self.pressure_max = 10 #Torr #MKS Sensor

        
        self.series = PressureTimeseries()

    def start(self, sample_rate: float = 1000.0, stop_event: threading.Event | None = None, target_: float | None = None, target_trigger: Literal['falling', 'rising'] | None = None):
        if self._running:
            self.logger.warning("Pressure acquisition thread already runnning")
            return
        task = self._parent.tasks["ai_continuous"]

        task.in_stream.input_buf_size = 100000

        task.timing.cfg_samp_clk_timing(rate=sample_rate,
                                        sample_mode=AcquisitionType.CONTINUOUS,
                                        samps_per_chan=10000
                                        )
        self._running = True
        self._sample_rate = sample_rate
        self._thread = threading.Thread(target=self._acquire,
                                        name="pressure_acquisition",
                                        daemon=True,
                                        kwargs={
                                                'stop_event': stop_event,
                                                'target_': target_,
                                                'target_trigger': target_trigger,
                                                }
                                        )
        self._thread.start()
        self.logger.info(f"Pressure acquisition started at {sample_rate} Hz")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        task = self._parent.tasks['ai_continuous']
        task.stop()
        self.logger.info("Pressure acquisition stopped")
    
    def _acquire(self, stop_event: threading.Event | None, target_: float | None, target_trigger: Literal['rising', 'falling']):
        task = self._parent.tasks["ai_continuous"]

        n_channels = 3
        chunk_size = 100
        buffer = np.empty((n_channels, chunk_size), dtype=np.float64)
        reader = AnalogMultiChannelReader(task.in_stream)

        task.start()
        settle_time_start = None

        self._sample_index = 0

        while self._running:
            if self._parent._abort_event.is_set():
                break
            try:
                n=chunk_size
                reader.read_many_sample(
                    buffer,
                    number_of_samples_per_channel=n,
                    timeout=1
                )

                dt = 1.0 / self._sample_rate
                t_end = time.perf_counter()
                t0 = t_end - n*dt
                times= (t0 + (self._sample_index + np.arange(n)) * dt)
                
                self._sample_index += n

                kjl = 10**(buffer[0, :n] - 5)
                mks = (buffer[1, :n]/10)*(self.pressure_max-self.pressure_min)+self.pressure_min
                mfc = self._parent.mfc.volts2sccm(buffer[2, :n])
            
                with self._lock:
                    self.series.samples_kjl.extend(
                       zip(times, kjl)
                    )
                    self.series.samples_mks.extend(
                        zip(times, mks)
                    )
                    self._parent.mfc.series.samples_readback.extend(
                        zip(times, mfc)
                    )
                if target_:
                    match target_trigger:
                        case 'falling':
                            if mks[-1] <= target_:
                                
                                self._running = False
                                #self.logger.info(f"Target pressure hit with falling trigger. Running status: {self._running}")
                                stop_event.set()
                                break
                        case 'rising':
                            if kjl[-1] >= target_:
                                self._running = False
                                stop_event.set()
                                break
                if self._parent.mfc._running:
                    if self._parent.mfc._settled_event and not self._parent.mfc._settled_event.is_set():
                        #self.logger.debug(f"Settled event waiting. Low end: {(self._parent.mfc._tolerance-self._parent.mfc._setpoint)} ; High end: {(self._parent.mfc._tolerance+self._parent.mfc._setpoint)}")
                        if (mks[-1] >= (self._parent.mfc._setpoint-self._parent.mfc._tolerance)) and (mks[-1] <= (self._parent.mfc._tolerance+self._parent.mfc._setpoint)):
                            if settle_time_start:
                                settle_time = time.perf_counter()-settle_time_start
                                self.logger.debug(f"settle_time: {settle_time} s")
                                if settle_time >= self._parent.mfc._settle_time:
                                    self._parent.mfc._settled_event.set()
                            else:
                                settle_time_start = time.perf_counter()
                    output = self._parent.mfc.PI(mks[-1], n*dt)
                    # self.logger.debug(f"calculated set point: {output}")
                    self._parent.mfc.set_flow(output)
                
            except nidaqmx.errors.DaqError as e:
                self.logger.exception("Error reading pressure")
                break
        task.stop()
        self.logger.info(f"Pressure acquisition stopped. ")#Running status: {self._running}")

    @property
    def latest(self) -> tuple[float, float]:
        with self._lock:
            p_kjl = self.series.samples_kjl[-1][1] if self.series and self.series.samples_kjl else 0.0
            p_mks = self.series.samples_mks[-1][1] if self.series and self.series.samples_mks else 0.0
        return p_kjl, p_mks

    def clear_buffer(self):
        with self._lock:
            self.series.samples_kjl.clear()
            self.series.samples_mks.clear()

class subsystemMFC:
    VOLUME = 45.30695

    def __init__(self, parent:NIDAQEquipment, kp: float, ki: float, v_per_sccm:float = 0.05):
        self._parent = parent
        self.logger = logging.getLogger("BeAMED.nidaq.mfc")
        self.kp = kp
        self.ki = ki
        self.kd = 0
        self.v_per_sccm = v_per_sccm

        self._running = False
        self._target = False
        self._integral = 0
        self._error = 0
        self._settled_event: threading.Event | None = None
        self._settled_since: float | None = None
        self._tolerance = 0.1
        self._settle_time = 5.0
        self._setpoint = 1.0

        self.series = MFCTimeseries()
        self._lock = threading.Lock()

    def PI(self, prev_val: float, dt:float):
        with self._lock:
            prev_err = self._error
            integral = self._integral
            kp = self.kp
            ki = self.ki
            kd = self.kd
            setpoint_torr = self._setpoint
        error = setpoint_torr - prev_val
        integral += error*dt
        derivative = (error - prev_err) / dt
        control = (kp * error) + (ki * integral) + (kd * derivative)
        control_mod = (control*self.VOLUME)*(1.333224)*(1/0.0168875)*(5/100) #V
        control_clamp = max(0.0, min((5.0, control_mod)))
        with self._lock:
            self._error = error
            self._integral = integral
        return control_clamp

    def set_PI(self, kp: float, ki: float, setpoint_torr: float):
        with self._lock:
            self.kp = kp
            self.ki = ki
            self._setpoint = setpoint_torr
        self.logger.info(f"Pressure target set to {setpoint_torr:.3f}")

    def get_PI(self) -> tuple[float, float]:
        return (self.kp, self.ki)
    
    def set_flow(self, volts: float):
        with self._parent._task_lock:
            self._parent.tasks["ao"].write(volts)
        sccm = volts/self.v_per_sccm
        if self._running:
            t=time.perf_counter()
            with self._lock:
                self.series.samples_setpoint.append((t,sccm))
        #self.logger.debug(f"MFC setpoint: {sccm} sccm ({volts:.3f} V)")

    # def read_flow(self) -> float:
    #     with self._parent._task_lock:
    #         volts = self._parent.tasks["ai_poll"].read()
    #     sccm = volts /self.v_per_sccm
    #     if self._running:
    #         t = time.perf_counter()
    #         with self._lock:
    #             self.samples_readback.append((t,sccm))
    #     return sccm
    
    def start_pi(self, settled_event: threading.Event | None = None,
                 tolerance: float = 0.05, settle_time: float=30.0):
        if self._running:
            self.logger.warning("PI control loop already runnning")
            return
        self._settled_event = settled_event
        self._settle_time = settle_time
        self._tolerance = tolerance
        self._running = True
        self._integral = 0.0
        self.logger.info(f"PI control loop started with target: {self._setpoint} Torr")

    def stop_pi(self):
        if not self._running:
            return
        self._running = False
        self._integral = 0.0
        self._setpoint = 0.0
        self._settled_since = None
        self.set_flow(0)
        self.logger.info(f"PI control loop stopped")

    def volts2sccm(self, volts: float) -> float:
        return volts /self.v_per_sccm
    
    @property
    def latest(self) -> tuple[float, float]:
        with self._lock:
            setpoints = self.series.samples_setpoint[-1][1] if self.series and self.series.samples_setpoint else 0.0
            readouts = self.series.samples_readback[-1][1] if self.series and self.series.samples_readback else 0.0
        return setpoints, readouts

class subsystemValve:
    def __init__(self, parent:NIDAQEquipment):
        self._parent = parent
        self.logger = logging.getLogger("BeAMED.nidaq.valves")
        self._states = [False, False, False]

    def open(self, valve: int):
        self._set(valve, True)

    def close(self, valve: int):
        self._set(valve, False)

    def close_all(self):
        if self._parent.tasks["do_valves"]:
            for i in range(3):
                self._set(i, False)
    
    def _set(self, valve:int, state: bool):
        if not 0 <= valve < 3:
            raise ValueError("Valve index must be 0-2")
        self._states[valve] = state
        with self._parent._task_lock:
            self._parent.tasks['do_valves'].write(self._states)
        self.logger.info(f"Valve {valve} {'opened' if state else 'closed'}")

    @property
    def states(self) -> list[bool]:
        return list(self._states)

class subsystemFeedthrough:
    STEPS_PER_CM = 3200
    STEP_DELAY = 0.000005

    def __init__(self, parent:NIDAQEquipment):
        self._parent = parent

    def _step(self, dir_: bool = True):
        dir_state = dir_
        with self._parent._task_lock:
            self._parent.tasks['do_feedthrough'].write([False, dir_state], auto_start=True)
        time.sleep(0.00005)
        with self._parent._task_lock:
            self._parent.tasks['do_feedthrough'].write([True, dir_state], auto_start=True)
        time.sleep(self.STEP_DELAY)
        with self._parent._task_lock:
            self._parent.tasks['do_feedthrough'].write([False, dir_state], auto_start=True)
        time.sleep(self.STEP_DELAY)

    def _step_for_cm(self, dir_: bool = True, cm: float = 1.0, trigger_event: threading.Event | None = None, stop_event: threading.Event | None = None):
        direction_str = "Down" if dir_ else "Up"
        self._parent.logger.debug(f"Stepping feedthrough {cm} cm in direction {direction_str}")
        steps = int(cm*self.STEPS_PER_CM)
        dir_state = dir_
        with self._parent._task_lock:
            self._parent.tasks['do_feedthrough'].write([False, dir_state], auto_start=True)
        time.sleep(0.00005)
        for _ in range(0, steps,1):
            with self._parent._task_lock:
                self._parent.tasks["do_feedthrough"].write([True, dir_state], auto_start=True)
            time.sleep(self.STEP_DELAY)
            with self._parent._task_lock:
                self._parent.tasks["do_feedthrough"].write([False, dir_state], auto_start=True)
            time.sleep(self.STEP_DELAY)
            if self._parent._abort_event.is_set():
                self._parent.logger.warning("Abort Event detected. Stopping feedthrough.")
                if trigger_event:
                    trigger_event.set()
                return
            if stop_event and stop_event.is_set():
                self._parent.logger.warning("Stop Event detected. Stopping feedthrough.")
                return
        if trigger_event:
            trigger_event.set()
            
    def _step_until(self, stop_event: threading.Event, dir_: bool = True):
        direction_str = "Down" if dir_ else "Up"
        self._parent.logger.debug(f"Stepping feedthrough in direction {direction_str}")
        dir_state = dir_
        with self._parent._task_lock:
            self._parent.tasks['do_feedthrough'].write([False, dir_state], auto_start=True)
        time.sleep(0.00005)
        while not stop_event.is_set() and not self._parent._abort_event.is_set():
            with self._parent._task_lock:
                self._parent.tasks["do_feedthrough"].write([True, dir_state], auto_start=True)
            time.sleep(self.STEP_DELAY)
            with self._parent._task_lock:
                self._parent.tasks["do_feedthrough"].write([False, dir_state], auto_start=True)
            time.sleep(self.STEP_DELAY)
            if self._parent._abort_event.is_set():
                self._parent.logger.warning("Abort Event detected. Stopping feedthrough.")
                return
            if stop_event.is_set():
                self._parent.logger.warning("Stop Event detected. Stopping feedthrough.")
                return
            

    def get_status(self):
        return False

