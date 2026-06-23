import time
import threading
import logging
import numpy as np
import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType

from equipment.baseequipment import Equipment

class NIDAQEquipment(Equipment):
    def __init__(self, name: str = "nidaq", device_id="NI_DAQ", kp: float = 1.0, ki: float = 0.1):
        super().__init__(name)
        self.logger = logging.getLogger("BeAMED.nidaq")
        self.device_id = device_id
        self._task_lock = threading.Lock()
        self._abort_event = threading.Event()
        self.tasks: dict[str, nidaqmx.Task] = {}

        # subsystems
        self.pressure = subsystemPressure(self)
        self.mfc = subsystemMFC(self, ki, kp)
        self.valves = subsystemValve(self)
        self.feedthrough = subsystemFeedthrough(self)

    def connect(self):
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
        self.tasks["ai_continuous"] = ai_cont

        ai_poll = nidaqmx.Task()
        ai_poll.ai_channels.add_ai_voltage_chan(f"{self.device_id}/ai3",
                                                name_to_assign_to_channel="MFC_flow",
                                                min_val=0,
                                                max_val=5,
                                                terminal_config=TerminalConfiguration.DIFF
                                                )
        self.tasks["ai_poll"] = ai_poll

        ao = nidaqmx.Task()
        ao.ao_channels.add_ao_voltage_chan(f"{self.device_id}/ao1",
                                           name_to_assign_to_channel="MFC_setpoint",
                                           min_val=0,
                                           max_val=5
                                           )
        self.tasks["ao"] = ao

        do_valves = nidaqmx.Task()
        do_valves.do_channels.add_do_chan(f"{self.device_id}/port0/line1", name_to_assign_to_lines="Vent")
        do_valves.do_channels.add_do_chan(f"{self.device_id}/port0/line0", name_to_assign_to_lines="MainPump")
        do_valves.do_channels.add_do_chan(f"{self.device_id}/port0/line2", name_to_assign_to_lines="SmallPump")
        self.tasks["do_valves"] = do_valves

        do_feedthrough = nidaqmx.Task()
        do_feedthrough.do_channels.add_do_chan(f"{self.device_id}/port1/line2", name_to_assign_to_lines="PUL")
        do_feedthrough.do_channels.add_do_chan(f"{self.device_id}/port1/line1", name_to_assign_to_lines="DIR")
        self.tasks["do_feedthrough"] = do_feedthrough

        self.logger.info("NIDAQ tasks configured")

    def disconnect(self):
        self.pressure.stop()
        self.mfc.stop_pi()
        self.valves.close_all()
        for name, task in self.tasks.items():
            try:
                task.close()
                self.logger.info(f"Closed task: {name}")
            except Exception as e:
                self.logger.exception(f"Error closing task {name}")
        self.tasks.clear()

    def getStatus(self) -> dict:
        p1, p2 = self.pressure.latest
        return {
            "KJL_pressure": p1,
            "MKS_pressure": p2,
            "MFC_flow": self.mfc.read_flow() if 'ai_poll' in self.tasks else None,
            "valve_states": self.valves.states,
            "feedthrough": self.feedthrough.get_status()
        }
        

class subsystemPressure:
    def __init__(self, parent:NIDAQEquipment):
        self._parent = parent
        self.logger = logging.getLogger("BeAMED.nidaq.pressure")
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        self.samples_kjl: list[tuple[float, float]] = [] #(t, value)
        self.samples_mks: list[tuple[float, float]] = []

    def start(self, sample_rate: float = 1000.0):
        if self._running:
            self.logger.warning("Pressure acquisition thread already runnning")
            return
        task = self._parent.tasks["ai_continuous"]
        task.timing.cfg_samp_clk_timing(rate=sample_rate,
                                        sample_mode=AcquisitionType.CONTINUOUS,
                                        samps_per_chan=1000
                                        )
        self._running = True
        self._thread = threading.Thread(target=self._acquire,
                                        name="pressure_acquisition",
                                        daemon=True,
                                        )
        self._thread.start()
        self.logger.info(f"Pressure acquisition started at {sample_rate} Hz")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.logger.info("Pressure acquisition stopped")
    
    def _acquire(self):
        task = self._parent.tasks["ai_continuous"]
        task.start()
        while self._running:
            if self._parent._abort_event.is_set():
                break
            try:
                data = task.read(
                    number_of_samples_per_channel=100,
                    timeout=1
                )
                t=time.perf_counter()
                with self._lock:
                    self.samples_kjl.extend(
                        [(t+i/1000, v) for i, v in enumerate(data[0])]
                    )
                    self.samples_mks.extend(
                        [(t+i/1000, v) for i, v in enumerate(data[1])]
                    )
            except nidaqmx.errors.DaqError as e:
                self.logger.exception("Error reading pressure")
                break
        task.stop()

    @property
    def latest(self) -> tuple[float, float]:
        with self._lock:
            p_kjl = self.samples_kjl[-1][1] if self.samples_kjl else 0.0
            p_mks = self.samples_mks[-1][1] if self.samples_mks else 0.0
        return p_kjl, p_mks

    def clear_buffer(self):
        with self._lock:
            self.samples_kjl.clear()
            self.samples_mks.clear()

class subsystemMFC:
    def __init__(self, parent:NIDAQEquipment, kp: float, ki: float, v_per_sccm:float = 0.05):
        self._parent = parent
        self.logger = logging.getLogger("BeAMED.nidaq.mfc")
        self.kp = kp
        self.ki = ki
        self.v_per_sccm = v_per_sccm

        self._pi_thread = None
        self._pi_running = False
        self._integral = 0

        self.samples_readback: list[tuple[float, float]] = []
        self.samples_setpoint: list[tuple[float, float]] = []
        self._lock = threading.Lock()

    def set_PI(self, kp: float, ki: float):
        self.kp = kp
        self.ki = ki

    def get_PI(self) -> tuple[float, float]:
        return (self.kp, self.ki)
    
    def set_flow(self, sccm: float):
        volts = sccm*self.v_per_sccm
        t=time.perf_counter()
        with self._parent._task_lock:
            self._parent.tasks["ao"].write(volts)
        with self._lock:
            self.samples_setpoint.append((t,sccm))
        self.logger.info(f"MFC setpoint: {sccm} sccm ({volts:.3f} V)")

    def read_flow(self) -> float:
        with self._parent._task_lock:
            volts = self._parent.tasks["ai_poll"].read()
        sccm = volts /self.v_per_sccm
        t = time.perf_counter()
        with self._lock:
            self.samples_readback.append((t,sccm))
        return sccm
    
    def start_pi(self, target_sccm:float, settled_event: threading.Event,
                 tolerance: float = 1.0, settle_time: float=5.0):
        if self._pi_running:
            self.logger.warning("PI control loop already runnning")
            return
        self._pi_running = True
        self._integral = 0.0
        self._pi_thread = threading.Thread(target=self._pi_loop,
                                           args=(target_sccm, settled_event, tolerance, settle_time),
                                           daemon=True,
                                           name="mfc_pi_control"
                                           )
        self._pi_thread.start()
        self.logger.info(f"PI control loop started with target: {target_sccm}")

    def _pi_loop(self):
        self.logger.warning(f"PI control loop not implemented properly, come back and change to pressure input rather than sccm input")

    def stop_pi(self):
        self.logger.warning(f"PI control loop not implemented properly, come back and change to pressure input rather than sccm input")

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

    def get_status(self):
        return False

