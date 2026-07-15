#beamed_v3/threadcontroller.py

import threading
import queue
import logging
import time
from typing import Any
from equipment.baseequipment import Equipment
from datatypes import ConnectResult, ActionResult, DisconnectResult, DischargeMeta, RunData, ExperimentParams, DischargeComplete, DischargeData, DischargeSkipped, PressureTimeseries, MFCTimeseries
from hdf5_writer import HDF5Writer
from process import ExperimentProcess
import os
from pathlib import Path


class Controller:
    '''
    Controls sequencing and independent operations of each instrument and information queue
    '''
    def __init__(self):
        self.logger = logging.getLogger("BeAMED.controller")
        self.registry: dict[str, Equipment] = {}
        self.queue: queue.Queue = queue.Queue()
        self.event_abortAll = threading.Event()
        self.writer = HDF5Writer(self.queue)
        self.process = ExperimentProcess(self, self.writer)
        self.current_run: RunData | None = None
        self.process_params: ExperimentParams | None = None

    def register(self, key: str, equipment: Equipment):
        '''
        Adds an instrument to the controller registry.
        '''
        self.registry[key] = equipment
        self.logger.info(f"Registered equipment: {key} ({type(equipment).__name__})")

    def get(self, key: str) -> Equipment:
        if key not in self.registry:
            raise KeyError(f"No equipment registered under '{key}")
        return self.registry[key]
    
    def connect_all(self):
        '''
        Connects all registered equipment, assigining each one a custom thread.
        '''
        threads = []
        for key, equipment in self.registry.items():
            t = threading.Thread(target = self._connect_instrument,
                                 args=(key,equipment),
                                 daemon=True
                                 )
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=10)

    def connect(self, key:str):
        equipment = self.get(key)
        t = threading.Thread(target=self._connect_instrument, args=(key,equipment), daemon=True, name=f"Connect {key}")
        t.start()

    def _connect_instrument(self, key:str, equipment: Equipment):
        try:
            self.logger.info(f"Connecting {key}...")
            equipment.connect()
            self.queue.put(ConnectResult(key=key, success=True))
        except Exception as e:
            self.logger.exception(f"Failed to connect {key}")
            self.queue.put(ConnectResult(key=key, success=False, error=str(e)))

    def disconnect_all(self):
        for key, equipment in self.registry.items():
            if equipment.isConnected():
                self._disconnect_instrument(key,equipment)

    def disconnect(self, key:str):
        equipment = self.get(key)
        t = threading.Thread(target=self._disconnect_instrument, args=(key,equipment), daemon=True, name=f"Disconnect {key}")
        t.start()
    
    def _disconnect_instrument(self, key: str, equipment: Equipment):
        try:
            equipment.disconnect()
            self.logger.info(f"Disconnected {key}")
            self.queue.put(DisconnectResult(key=key, success=True))
        except Exception as e:
            self.logger.exception(f"Error disconnecting {key}")
            self.queue.put(DisconnectResult(key=key, success=False, error=str(e)))

    def run(self, action: str, target: str, method: str, **kwargs):
        '''
        Calls equipment action on a thread
        '''
        threading.Thread(target = self._run,
                         name=action,
                         args=(action, target, method),
                         kwargs=kwargs,
                         daemon=True).start()
        
    def _run(self, action: str, target: str, method: str, **kwargs):
        try:
            equipment = self.get(target)
            result = getattr(equipment, method)(**kwargs)
            self.queue.put(ActionResult(
                key = target,
                action=action,
                success = True,
                data={"result":result}
            ))
        except Exception as e:
            self.logger.exception(f"Action '{action}' failed")
            self.queue.put(ActionResult(
                key = target,
                action=action,
                success = False,
                error = str(e)
            ))

    def configure_process(self, process: ExperimentParams):
        self.process_params = process
        if self.writer.is_open:
            self.writer.close()
        if os.path.exists(self.writer._save_dir/Path(process.save_path)):
            self.logger.debug(f"opening file: {self.writer._save_dir/Path(process.save_path)}")
            prev_params = self.writer.import_file(process.save_path)
            if not process.issameparams(prev_params):
                self.logger.warning("Configured process inputs different from currently selected save file. Are you sure you want to continue?")
        else:
            self.writer.new_file(process.save_path, process.to_meta())
        self.logger.debug(f"Process Configured. Params: {process}")

    def start_run(self, meta: DischargeMeta):
        if self.current_run is not None:
            self.logger.warning("start_run called while run active - overwriting")

        run = RunData(
            meta=meta,
            t_start = time.perf_counter()
        )
        run.meta.index = self.writer.next_discharge_index()
        self.current_run = run

        nidaq = self.registry.get('nidaq')
        if nidaq:
            nidaq.pressure.series = run.pressure
            nidaq.mfc.series = run.mfc

        dmm = self.registry.get("dmm")
        if dmm:
            dmm.series = run.dmm

        psu = self.registry.get("pwr")
        if psu:
            psu.series = run.power_supply

        scope = self.registry.get("osc")
        if scope:
            scope.series = run.waveform

    def end_run(self, run_id, discharge_result: DischargeComplete | DischargeSkipped) -> RunData:
        completed = self.current_run
        self.current_run = None
        nidaq = self.registry.get('nidaq')
        if nidaq:
            nidaq.pressure.series = PressureTimeseries()
            nidaq.mfc.series = MFCTimeseries()

        dmm = self.registry.get("dmm")
        if dmm:
            dmm.series = None

        psu = self.registry.get("pwr")
        if psu:
            psu.series = None

        scope = self.registry.get("osc")
        if scope:
            scope.series = None

        self.logger.info(f"Run ended: {run_id}")

        completed.meta.trigger_source = discharge_result.source
        if isinstance(discharge_result, DischargeSkipped):
            return
        
        discharge_data = DischargeData(
            gap_cm = completed.meta.gap_cm,
            pressure_kjl = discharge_result.pressure_kjl,
            pressure_mks = discharge_result.pressure_mks,
            voltage_pwr = discharge_result.voltage,
            current_pwr = discharge_result.current,
            voltage_dmm = completed.dmm.samples_voltage[-1][1],
            source = discharge_result.source
            )
        discharge_data.calculate_errors()
        completed.critical_data = discharge_data

        return completed
    
    def stamp_trigger(self, source: str):
        if self.current_run is None:
            self.logger.warning("stamp_trigger called but no run active")
            return
        t = time.perf_counter()
        run_var = self.current_run
        for series in (run_var.pressure, run_var.mfc, run_var.dmm, run_var.power_supply, run_var.waveform):
            if series is not None:
                series.t_trigger = t
                series.trigger_source = source
        self.logger.info(f"Trigger stamped: source={source} t={t:.6f}")


    def start_process(self):
        if self.process_params:
            params = self.process_params
            t = threading.Thread(
                target=self.process.start,
                args = (params,),
                name="ExperimentSeries",
                daemon=True
            )   
            t.start()
        else:
            self.logger.warning("Process cannot be started, not configured.")

    def stop_process(self):
        self.process.stop()

    def shutdown(self):
        self.logger.info("Shutting down. Closing all open threads...")
        self.event_abortAll.set()
        self.disconnect_all()