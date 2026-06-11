import sys
import time
import numpy as np
from dataclasses import dataclass
from equipment.visaequipment import VisaEquipment
import pyvisa

@dataclass
class Waveform:
    '''
    structured result from querying waveform from oscilloscope
    '''
    voltage: np.ndarray
    time: np.ndarray
    dy: float
    t_discharge: float
    vdiv: float
    tdiv: float
    tinter: float
    samplerate: float
    offset: float

class SiglentSDS1204XE(VisaEquipment):
    '''
    Siglent SDS1204X-E Oscilloscope
    '''
    def __init__(self, name:str = "Oscilloscope", resource_id:str = "USB0::0xF4EC::0xEE38::SDSMMFCD4R9625::INSTR", manager: pyvisa.ResourceManager = None):
        super().__init__(name, resource_id, manager)

    def configure(self, channel: str = "C1", vdiv: float = 1.0, tdiv: float=1e-3, trigger_level:float=0.5, trigger_slope:str="POS"):
        self.write("CHDR OFF")
        self.write(f"{channel}:VDIV {vdiv}")
        self.write(f"TDIV {tdiv}")
        self.write(f"{channel}:TRLV {trigger_level}")
        self.write(f"{channel}:TRSL {trigger_slope}")

    def arm_trigger(self):
        self.write("TRMD SINGLE")

    def wait_for_trigger(self, poll_interval: float = 0.05,
                         stop_event=None, abort_event=None) -> bool:
        """
        Blocks until scope triggers, stop_event fires, or abort_event fires.
        Returns True if triggered, False if stopped/aborted.
        This runs on its own thread — never call from GUI thread.
        """
        while True:
            if abort_event and abort_event.is_set():
                return False
            if stop_event and stop_event.is_set():
                return False
            status = self.query("SAST?")
            if "Stop" in status:
                return True
            time.sleep(poll_interval)

    def capture(self, channel: str = "C1") -> Waveform:
        """Fetch waveform data from scope after trigger. Returns structured result."""
        self.write("CHDR OFF")
        self.write(f"DATASOURCE {channel}")
        self.write("DATA:ENCDG SRI")
        self.write("DATA:WIDTH 2")
        self.write("DATA:START 0")
        self.write("DATA:STOP 1000")

        sample_rate = float(self.query("SARA?"))
        time_interval = 1 / sample_rate
        tdiv  = float(self.query("TDIV?"))
        offset = float(self.query(f"{channel}:OFST?"))
        vdiv  = float(self.query(f"{channel}:VDIV?"))

        self.write(f"{channel}:WF? DAT2")
        raw = self.read_raw()[16:-2]

        codes = np.frombuffer(raw, dtype=np.uint8).astype(np.int16)
        voltage = np.where(codes < 127,
                           codes * (vdiv / 25) - offset,
                           (codes - 256) * (vdiv / 25) - offset)
        n = len(voltage)
        time_axis = np.array([(tdiv * 14) - i * time_interval for i in range(n)])

        return Waveform(
            voltage=voltage,
            time_axis=time_axis,
            dy=float(np.max(voltage) - np.min(voltage)),
            t_discharge=time.perf_counter(),
            vdiv=vdiv,
            tdiv=tdiv,
        )

    def stop(self):
        self.write("STOP")

    def getStatus(self) -> dict:
        base = super().get_status()
        if self._connected:
            base["trigger_status"] = self.query("SAST?").strip()
        return base