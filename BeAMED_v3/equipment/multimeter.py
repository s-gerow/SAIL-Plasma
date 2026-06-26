import sys
import time
from typing import Literal
import threading

import numpy as np
import pyvisa
from dataclasses import dataclass

from equipment.visaequipment import VisaEquipment
from datatypes import DMMSeries

class KeithleyDMM6500(VisaEquipment):
    def __init__(self, manager: pyvisa.ResourceManager, name: str = "dmm", resource_id: str = "USB0::0x05E6::0x6500::04470458::INSTR"):
        super().__init__(name, manager, resource_id)
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self.series = DMMSeries()
        self._mode = "VOLT:DC"

    def disconnect(self):
        if self._running:
            self.stop_continuous_measure()
        super().disconnect()
    
    def configure(self):
        with self._lock:
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
            self.write(f"TRAC:POIN 1000 'defbuffer1'") #Buffer Size 10
        self.logger.info("DMM buffer configured for continuous acquisition")

    def func_select(self, func:str = "VOLT:DC"):
        with self._lock:
            self.write(f':SENS:FUNC "{func}"')
        self._mode = func
    
    def measure(self):
        self._running = True
        with self._lock:
            read = self.query(":READ?")
        self._running = False
        return read
    
    def start_continuous_measure(self):
        if self._running:
            self.logger.warning("Continuous dmm acquisition thread already runnning")
            return
        with self._lock:
            self.write("INIT")
        time.sleep(0.1)
        self._running = True
        self._thread = threading.Thread(
            target = self._acquire,
            daemon=True,
            name = "dmm_acquisition"
        )
        self._thread.start()
        self.logger.info("DMM continuous acquisition started")

    def stop_continuous_measure(self):
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.logger.info("DMM continuous acquisition stopped")

    def enable_auto_range(self):
        with self._lock:
            self.write(f"SENS:{self._mode}:RANG:AUTO TRUE")

    def disable_auto_range(self):
        with self._lock:
            self.write(f"SENS:{self._mode}:RANG:AUTO FALSE")

    def _acquire(self):
        self._cursor = 1
        while self._running:
            try:
                if not self._connected:
                    break
                t = time.perf_counter()
                with self._lock:
                    values = float(self.query(":READ?"))
                readings = [(t, values)]

                if self.series is not None:
                    with self._lock:
                        if self._mode in ("VOLT:DC"):
                            self.series.samples_voltage.extend(readings)
                        elif self._mode in ("CONT"):
                            self.series.samples_resistance.extend(readings)
            except Exception as e:
                self.logger.exception("DMM acquisition error")
                break

    def getStatus(self):
        base = super().get_status()
        if self._connected:
            with self._lock:
                base["func"] = self.query(":FUNC?")
                base["value"] = self.query(":READ?")
        return base
    
    @property
    def latest(self) -> float:
        with self._lock:
            if self._mode in ("VOLT:DC"):
                read = self.series.samples_voltage[-1][1] if self.series.samples_voltage else 0.0
            elif self._mode in ("CONT"):
                read = self.series.samples_resistance[-1][1] if self.series.samples_resistance else 0.0
        return read
    

