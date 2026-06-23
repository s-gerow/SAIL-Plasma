import sys
import time
from typing import Literal

import numpy as np
import pyvisa
from dataclasses import dataclass

from equipment.visaequipment import VisaEquipment

@dataclass
class PowerSeries:
    voltage: np.ndarray
    current: np.ndarray
    time: np.ndarray
    t_discharge: float

class Keithley2260B_800_1(VisaEquipment):
    def __init__(self, manager: pyvisa.ResourceManager, name: str = "PowerTopR",  resource_id: str = "ASRL4::INSTR"):
        super().__init__(name, manager, resource_id)

    def configure(self):
        self.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
        self.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")

    def stop(self):
        self.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
        self.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")
        self.write(f"OUTP:STAT:IMM OFF")

    def enable_output(self):
        self.write(f"OUTP:STAT:IMM ON")

    def

    def getStatus(self):
        base = super().get_status()
        if self._connected:
            base["voltage"] = self.query("MEAS:SCAL:VOLT:DC?")
            base["current"] = self.query("MEAS:SCAL:CURR:DC?")