import time
import threading
import logging

from threadcontroller import Controller
from datatypes import (
    ExperimentParams,
    DischargeComplete,
    DischargeSkipped,
    ExperimentFailed,
    ExperimentComplete,
)
    
class ExperimentProcess:
    def __init__(self, controller: Controller):
        self.controller = controller
        self.logger = logging.getLogger("BeAMED.experiment")
        self._abort = threading.Event()
        self._thread: threading.Thread | None = None

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

        self.logger.info("Arming oscilloscope")
        scope.arm_trigger()

        for i, pressure in enumerate(params.pressures):
            if self._abort.is_set() or self.controller.event_abortAll.is_set():
                self.logger.warning(f"Aborted before discharge {i+1}")
                break
            
            self.logger.info(f"Discharge {i+1}/{params.n_discharges} - target pressure {pressure:.3f} Torr")
            self._run_discharge(i, pressure, params, nidaq, pwr, scope, dmm)

        self._finish(nidaq, pwr)

    def _run_discharge(self, index, pressure, params, nidaq, pwr, scope, dmm):
        pass