import sys
import time
from typing import Literal

import numpy as np
import pyvisa
from dataclasses import dataclass

from equipment.visaequipment import VisaEquipment

class KeithleyDMM6500(VisaEquipment):
    def __init__(self, manager: pyvisa.ResourceManager, name: str = "dmm", resource_id: str = "USB0::0x05E6::0x6500::04386498::0::INSTR"):
        super().__init__(name, manager, resource_id)
    
    def configure(self):
        self.write("*RST")
        self.write("*RST")
        self.write(f":SENS:FUNC 'VOLT:DC'")
        self.write(f"SENS:VOLT:RANG:AUTO ON")
        self.write(f":SENS:VOLT:NPLC 1") #Default 1
        self.write(f":SENS:VOLT:LINE:SYNC OFF") #Default OFF
        self.write(f"SENS:VOLT:AZER ON")#Default ON
        
        self.write(f"CALC2:VOLT:LIM1:STAT OFF") #Default OFF
        self.write(f"CALC2:VOLT:LIM1:CLE:AUTO ON") #Limit Number in GUI is 1 (LIM_), Default ON
        self.write(f"CALC2:VOLT:LIM1:LOW 0") #Because the voltage limit is disabled this should not be needed but may as well include it because maybe one day we do
        self.write(f"CALC2:VOLT:LIM1:UPP 0")
        self.write(f"TRAC:FILL:MODE CONT, 'defbuffer1'") #continuous fill
        self.write(f"TRAC:POIN 'defbuffer1'") #Buffer Size 10

    def func_select(self, func:str = "VOLT:DC"):
        self.write(f':SENS:FUNC "{func}"')

    def getStatus(self):
        base = super().get_status()
        if self._connected:
            base["func"] = self.query(":FUNC?")
            base["value"] = self.query(":READ?")
        return base
    

