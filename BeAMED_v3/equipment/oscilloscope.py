import sys
import time
from typing import Literal

import numpy as np
import pyvisa
from dataclasses import dataclass

from equipment.visaequipment import VisaEquipment

@dataclass
class Waveform:
    """
    Dataclass to store processed waveform data from oscilloscope and additional relevant parameters.

    Attributes
    __________
    voltage : np.ndarray
        Array of vertical axis values representing the voltage data.
    time : np.ndarray
        Array of horizontal axis values representing timeseries data.
    dy : float
        Floating point decimal value representing the magnitude of the voltage peak which triggered the discharge.
    t_discharge : float
        Floating point decimal result of time.time() call at the moment the discharge is detected by the oscilloscope.
    """
    voltage: np.ndarray
    time: np.ndarray
    dy: float
    t_discharge: float

class SiglentSDS1204XE(VisaEquipment):
    """
    Equipment object which controls the Siglent SDS1204X-E oscilloscope used by AMPS@SAIL to detect the current at the 
    moment of electrical discharge initialization.

    Parameters
    ----------
    manager : pyvisa.ResourceManager
        Pyvisa resource manager used to connect and communicate with devices which use VISA methods, this is None by default but must be supplied otherwise the device cannot be communicated with.
    name : str, optional
        Name of the oscilloscope as used in dictionaries, logs, and method calls. This is the readable interface by which this object is identified in interactions with other objects and the user, by default "Oscilloscope".
    resource_id : _type_, optional
        Resource identification string used by VISA inferfaces to connect and communication with the device, unique to each individual instrument, by default "USB0::0xF4EC::0xEE38::SDSMMFCD4R9625::INSTR".
    """
    def __init__(self,  manager: pyvisa.ResourceManager, name:str = "oscilloscope", resource_id:str = "USB0::0xF4EC::0xEE38::SDSMMFCD4R9625::INSTR"):
        """
        Initialize and return SiglentSDS1204XE object using default resource identification string

        Parameters
        ----------
        manager : pyvisa.ResourceManager
            Pyvisa resource manager used to connect and communicate with devices which use VISA methods, this is None by default but must be supplied otherwise the device cannot be communicated with.
        name : str, optional
            Name of the oscilloscope as used in dictionaries, logs, and method calls. This is the readable interface by which this object is identified in interactions with other objects and the user, by default "Oscilloscope".
        resource_id : _type_, optional
            Resource identification string used by VISA inferfaces to connect and communication with the device, unique to each individual instrument, by default "USB0::0xF4EC::0xEE38::SDSMMFCD4R9625::INSTR".
        """
        super().__init__(name, manager, resource_id)

    def configure(self, channel: str = "C1", vdiv: float = 1.0, tdiv: float=1e-3, trigger_level:float=0.5, trigger_slope:Literal["POS", "NEG", "WINDOW"] ="POS"):
        """
        Configure common oscillscope settings.

        Parameters
        ----------
        channel : str, optional
            Channel to read data and trigger on, by default "C1"
        vdiv : float, optional
            Voltage sensitivity in volts/division, by default 1.0
        tdiv : float, optional
            Horizontal scale per division of window in seconds, by default 1e-3
        trigger_level : float, optional
            Input voltage (volts) on the given channel required to activate the trigger, by default 0.5
        trigger_slope : Literal["POS", "NEG", &quot;WINDOW&quot;], optional
            Trigger slope of specified source, by default "POS"

        Notes
        _____
        This method can and should be overrriden/edited to add additional configurations if needed.
        Presently it only includes the parameters which need to be set to adjust the trigger and screen resolution.
        """
        # Turn of character headers. Changes command responses from TIME_DIV 1e-3S to 1e-3
        # This can also be set to TDIV 1e-3 but we dont want any characters in these responses, just numbers.
        self.write("CHDR OFF")
        self.write(f"{channel}:VDIV {vdiv}")
        self.write(f"TDIV {tdiv}")
        self.write(f"{channel}:TRLV {trigger_level}")
        self.write(f"{channel}:TRSL {trigger_slope}")

    def arm_trigger(self):
        """
        Set the trigger mode on a pre-specifed source, see configure(). Single mode will trigger on the next valid signal. 
        """
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
        self.logger.debug(f"Response: {len(raw)} bytes")
        codes = np.frombuffer(raw, dtype=np.uint8).astype(np.int16)
        voltage = np.where(codes < 127,
                           codes * (vdiv / 25) - offset,
                           (codes - 256) * (vdiv / 25) - offset)
        n = len(voltage)
        time_axis = np.array([(tdiv * 14) - i * time_interval for i in range(n)])

        return Waveform(
            voltage=voltage,
            time=time_axis,
            dy=float(np.max(voltage) - np.min(voltage)),
            t_discharge=time.perf_counter()
            )

    def stop(self):
        self.write("STOP")

    def getStatus(self) -> dict:
        base = super().get_status()
        if self._connected:
            base["trigger_status"] = self.query("SAST?").strip()
        return base