#Beamed_v3/process.py

from __future__ import annotations
import time
import threading
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from threadcontroller import Controller  # only imported for type hints, not at runtime
from datatypes import (
    RunData,
    DischargeMeta,
    ExperimentMeta,
    ExperimentParams,
    DischargeComplete,
    DischargeSkipped,
    ExperimentFailed,
    ExperimentComplete,
    PressureTimeseries,
    MFCTimeseries,
    DMMSeries,
    PowerSeries,
    Waveform
)
from npz_writer import NPZWriter    

class ExperimentProcess:
    def __init__(self, controller: 'Controller', writer: NPZWriter):
        self.controller = controller
        self.writer = writer
        self.logger = logging.getLogger("BeAMED.experiment")
        self._abort = threading.Event()
        self._thread: threading.Thread | None = None

        self.pi_settled_event = threading.Event()
        self.pressure_min_event = threading.Event()
        self.feedthrough_ground_event = threading.Event()
        self.feedtrhough_gap_set_event = threading.Event()
        self.power_trigger = threading.Event()
        self.oscope_trigger = threading.Event()
        

    def start(self, params: ExperimentParams):
        if self._thread and self._thread.is_alive():
            self.logger.warning("Experiment already running")
            return
        self._abort.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(params,),
            daemon=True,
            name="experiment_series"
        )
        self._thread.start()
        self.logger.info(f"Experimert series started from {params.start_pressure} Torr to {params.stop_pressure} Torr")

    def stop(self):
        self._abort.set()
        self.logger.warning("Experiment abort requested")

    def _run(self, params: ExperimentParams):
        try:
            self._execute(params)
        except Exception as e:
            self.logger.exception("Experiment Failed")
            self.controller.queue.put(
                ExperimentFailed(reason=str(e))
            )

    def _execute(self, params: ExperimentParams):
        nidaq = self.controller.get("nidaq")
        pwr = self.controller.get("pwr")
        scope = self.controller.get("osc")
        dmm = self.controller.get("dmm")

        ## Experiment series ordering
        # read params:
        # pressure array = params.pressures()
        # start first discharge
        # reset abort-event
        # reset stop_event
        # i = 0
        # set target pressure pressures[i]
        # open pump valve
        # wait until P = 0.9
        # enable PI controller to get to target pressure
        # when P ~= target pressure for settle time
        # start dmm in continuity mode
        # start grounding the electrode
        # wait until R < x
        # reverse electrode
        # set distance cm
        # when electrode set
        # configure dmm in voltage mode
        # set power supply enabled
        # configure oscope
        # start new pressure series, dmm series, power series
        # start voltage increase
        # check for abort, stop, or trigger
        # save all series, etc
        # save to file
        # i + 1
        # open vent valve
        # start back at line 4



        # configure the oscilloscope
        scope.configure()

        for i, pressure in enumerate(params.pressures):
            if self._abort.is_set() or self.controller.event_abortAll.is_set():
                self.logger.warning(f"Aborted before discharge {i+1}")
                break
            
            self.logger.info(f"Discharge {i+1}/{params.n_discharges} - target pressure {pressure:.3f} Torr")
            skipped = self._run_discharge(i, pressure, params, nidaq, pwr, scope, dmm)

            if skipped:
                continue

            self.logger.info("Venting chamber to atmosphere")
            self._wait_for_atmosphere(nidaq, timeout=300)

        self._finish(nidaq, pwr, dmm)
        self.controller.queue.put(
            ExperimentComplete(
                n_discharges=len(params.pressures),
                filepath=str(self.writer.filepath)
            )
        )

    def _run_discharge(self, index, pressure, params, nidaq, pwr, scope, dmm) -> bool:
        # starting at atmosphere


        self.controller.run("nidaq_set_pi", nidaq, "set_PI", kp = 0.1, ki=0.005, pressure_torr = pressure)
        self.controller.run("nidaq_start_pi", nidaq, "start_PI")
