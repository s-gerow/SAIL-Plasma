import sys
import time
from typing import Literal
import threading

import numpy as np
import pyvisa

from equipment.visaequipment import VisaEquipment
from datatypes import PowerSeries

class Keithley2260B_800_1(VisaEquipment):
    def __init__(self, manager: pyvisa.ResourceManager, name: str = "pwr",  resource_id: str = "ASRL3::INSTR", abort_event:threading.Thread|None=None):
        super().__init__(name, manager, resource_id, abort_event=abort_event)
        self._enabled = False
        self._output = False
        self._lock = threading.Lock()
        self._thread = None
        self.series = PowerSeries()

    def configure(self):
        with self._lock:
            self.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
            self.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")

    def stop(self):
        with self._lock:
            self.write(f"SOUR:CURR:LEV:IMM:AMPL {0}")
            self.write(f"SOUR:VOLT:LEV:IMM:AMPL {0}")
            self.write(f"OUTP:STAT:IMM OFF")

    def enable_output(self):
        self._enabled = True

    def disable_output(self):
        self._enabled = False

    def set_voltage(self, voltage: float | str):
        with self._lock:
            self.write(f"SOUR:VOLT:LEV:IMM:AMPL {voltage}")
        self.logger.info(f"Voltage output set to {voltage:.3f} | Output enabled: {self._output}")

    def set_current(self, current: float | str):
        with self._lock:
            self.write(f"SOUR:CURR:LEV:IMM:AMPL {current}")
        self.logger.info(f"Current output set to {current:.3f} | Output enabled: {self._output}")

    def start_output(self):
        if not self._enabled:
            self.logger.warning("Power output not enabled, cannot start output")
            return
        if self._output:
            self.logger.warning("Power output already on, cannot start output")
            return
        self._output = True
        with self._lock:
            self.write("OUTP:STAT ON")
        self._thread = threading.Thread(target=self._monitor,
                                        daemon=True,
                                        name="pwr_monitor")
        self._thread.start()
        self.logger.warning("CAUTION: HIGH VOLTAGE ON")
    
    def stop_output(self):
        self._output = False
        with self._lock:
            self.write("OUTP:STAT OFF")
        if self._thread:
            self._thread.join(timeout=2)
        self.logger.warning("HIGH VOLTAGE OFF")

    def _monitor(self):
        while self._output:
            try:
                if not self._connected:
                    break
                t = time.perf_counter()
                with self._lock:
                    voltage = float(self.query("MEAS:VOLT?"))
                    current = float(self.query("MEAS:CURR?"))

                if self.series is not None:
                    self.series.samples_voltage.append((t, voltage))
                    self.series.samples_current.append((t, current))

            except RuntimeError:
                break
            except Exception as e:
                self.logger.exception("PSU monitor error")
                break

    def getStatus(self):
        base = super().get_status()
        if self._connected:
            with self._lock:
                base["voltage"] = self.query("MEAS:SCAL:VOLT:DC?")
                base["current"] = self.query("MEAS:SCAL:CURR:DC?")
        return base
    
    @property
    def latest(self) -> tuple[float, float]:
        if self._connected:
            volt = self.series.samples_voltage[-1][1] if self.series.samples_voltage else 0.0
            curr = self.series.samples_current[-1][1] if self.series.samples_current else 0.0
        return volt, curr