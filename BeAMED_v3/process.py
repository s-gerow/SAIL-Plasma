#Beamed_v3/process.py

from __future__ import annotations
import time
import threading
import logging
from typing import TYPE_CHECKING
from equipment.nidaqequipment import NIDAQEquipment
from equipment.oscilloscope import SiglentSDS1204XE
from equipment.multimeter import KeithleyDMM6500
from equipment.powersupply import Keithley2260B_800_1

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
        self._abort = controller.event_abortAll
        self._thread: threading.Thread | None = None

        self.pi_settled_event = threading.Event()
        self.pressure_min_event = threading.Event()
        self.pressure_atmosphere_set = threading.Event()
        self.feedthrough_ground_event = threading.Event()
        self.feedthrough_gap_set_event = threading.Event()
        self.power_trigger = threading.Event()
        self.oscope_trigger = threading.Event()       

    def start(self, params: ExperimentParams):
        if self._thread and self._thread.is_alive():
            self.logger.warning("Experiment already running")
            return
        self._abort.clear()
        self._run(params)
        self.logger.info(f"Experimert series started from {params.start_pressure} Torr to {params.stop_pressure} Torr")

    def stop(self):
        self._abort.set()
        self.logger.warning("Experiment abort requested")

    def _run(self, params: ExperimentParams):
        try:
            self._thread = threading.Thread(
            target=self._execute,
            args=(params,),
            daemon=True,
            name="experiment_series"
            )
            self._thread.start()
        except Exception as e:
            self.logger.exception("Experiment Failed")
            self.controller.queue.put(
                ExperimentFailed(reason=str(e))
            )

    def _execute(self, params: ExperimentParams):
        # clear events:
        self.pressure_atmosphere_set.clear()
        self.feedthrough_ground_event.clear()
        self.pressure_min_event.clear()
        self.pi_settled_event.clear()
        self.feedthrough_gap_set_event.clear()
        self.feedthrough_ground_event.clear()
        self.power_trigger.clear()
        self.oscope_trigger.clear()

        nidaq = self.controller.get("nidaq")
        pwr = self.controller.get("pwr")
        scope = self.controller.get("osc")
        dmm = self.controller.get("dmm")



        # configure the oscilloscope
        self.logger.debug("configuring oscilloscope")
        #scope.configure()
        self.logger.debug("configuring digital multimeter")
        #dmm.configure()
        self.logger.debug("configuring power supply")

        for i, pressure in enumerate(params.pressures):
            if self._abort.is_set() or self.controller.event_abortAll.is_set():
                self.logger.warning(f"Aborted before discharge {i+1}")
                break

            self.pressure_atmosphere_set.clear()
            self.feedthrough_ground_event.clear()
            self.pressure_min_event.clear()
            self.pi_settled_event.clear()
            self.feedthrough_gap_set_event.clear()
            self.feedthrough_ground_event.clear()
            self.power_trigger.clear()
            self.oscope_trigger.clear()

            params.index = i

            meta = DischargeMeta(index=i,
                                 gap_cm=params.gap_cm,
                                 gas_species=params.gas_species,
                                 cathode_material=params.cathode_material,
                                 anode_material=params.anode_material,
                                 cathode_shape=params.cathode_shape,
                                 anode_shape=params.anode_shape
                                 )
            self.controller.start_run(f"discharge_{i+1:03d}", meta)

            self.logger.info(f"Discharge {i+1}/{params.n_discharges} - target pressure {pressure:.3f} Torr")
            discharge_result = self._run_discharge(pressure, params, nidaq)

            self._wait_for_thread_close(nidaq, dmm, scope, pwr)

            self.logger.info("Venting chamber to atmosphere")
            self._wait_for_atmosphere(nidaq) #, timeout=300)
        self.controller.queue.put(
            ExperimentComplete(
                n_discharges=len(params.pressures),
                filepath=str(self.writer.filepath)
            )
        )

    def _run_discharge(self, pressure, params: ExperimentParams, nidaq) -> DischargeComplete | DischargeSkipped:
        # starting at atmosphere
        MIN_PRESSURE = 1 # Torr
        try:
            # because the valves and feedthrough are on different output tasks we need to either stop all of the
            # valves while setting feedthrough. or we set the feedthrough before all of the pressure stuff is done. 
            # This is controversial. by setting the feedthrough before pulling out all of the gas we could accidentally
            # move the feedthrough. But by closing the valves mid experiment we will cause a leak and ruin the gas composition.
            # going to set the feedthrough first for now until a new way to do this is figured out.
            self.controller.run("nidaq_stop", "nidaq", "stop_pressure_acquisition")
            # first need to enable do_feedthrough and disable do_valves
            self.controller.run("nidaq_deactivate_do_valves", "nidaq", "_disconnect_valves")
            self.controller.run("nidaq_activate_do_feedthrough", "nidaq", "_connect_feedthrough")
            # set dmm to continuity mode
            self.controller.run("dmm_set_cont_mode", "dmm", "func_select", func="CONT")
            # start dmm acquisition with event to trigger when resistance < threshold
            self.controller.run("dmm_start_cont_meas", "dmm", "start_continuous_measure", trigger_event = self.feedthrough_ground_event, trigger_value = 270)
            # start feedthrough for with dmm trigger as stop
            self.controller.run("nidaq_ground_feedthrough", "nidaq", "start_feedthrough", dir_ = True, stop_event = self.feedthrough_ground_event)
            # wait for dmm trigger, then wait for some time to allow feedthrough to stop
            while not self.feedthrough_ground_event.is_set():
                time.sleep(0.01)
            time.sleep(0.5)
            # start feedthrough set to params distance with set trigger
            self.controller.run("nidaq_set_feedthrough", "nidaq", "step_feedthrough_cm", dir_ = False, cm = params.gap_cm, trigger_event = self.feedthrough_gap_set_event)
            # wait for feedthrough trigger
            while not self.feedthrough_gap_set_event.is_set():
                time.sleep(0.01)
            self.controller.run("nidaq_deactivate_do_feedthrough", "nidaq", "_disconnect_feedthrough")
            self.controller.run("nidaq_activate_do_valves", "nidaq", "_connect_valves")
            time.sleep(0.5)
            self.logger.info("Setting chamber pressure")
            # open pump valve to get to min pressure
            self.controller.run("nidaq_open_main_pump", 'nidaq', "open_valve", valve=0)
            # start reading with a target of min pressure, as the pressure drops to equal or less than target, set the event
            self.controller.run("nidaq_pressure_read", 'nidaq', "start_pressure_acquisition", stop_event = self.pressure_min_event, target_=MIN_PRESSURE, target_trigger='falling')
            # wait for the event trigger from pressure thread
            while not self.pressure_min_event.is_set():
                time.sleep(0.01)
            # start reading again with no trigger
            self.logger.info(f"Chamber reached minimum pressure: {MIN_PRESSURE} Torr")
            time.sleep(0.5)
            self.controller.run("nidaq_pressure_read", 'nidaq', "start_pressure_acquisition")
            # set PI controller to target pressure with event
            self.controller.run("nidaq_set_pi", 'nidaq', "set_PI", kp = 0.1, ki=0.005, pressure_torr = pressure)
            self.controller.run("nidaq_start_pi", 'nidaq', "start_PI", settled_event = self.pi_settled_event)
            # wait for settled event to trigger
            while not self.pi_settled_event.is_set():
                time.sleep(0.01)
            self.logger.info(f"Chamber pressure stable at {nidaq.pressure.latest[1]} Torr")
            # set dmm in voltage mode
            self.controller.run("dmm_set_cont_mode", "dmm", "func_select", func="VOLT:DC")
            # start dmm reading
            self.controller.run("dmm_start_cont_meas", "dmm", "start_continuous_measure", trigger_event = None, trigger_value = 0.0)
            # arm oscilloscope trigger 
            self.controller.run("osc_arm_trigger", "osc", "arm_trigger", trigger_event = self.oscope_trigger)
            # start voltage increase methode with power supply trigger
            self.controller.run("pwr_voltage_sweep", "pwr", "start_sweep", 
                                step = params.dV, 
                                start = params.start_voltage, 
                                current_limit = 0.5, 
                                trigger_event = self.power_trigger, 
                                stop_event = self.oscope_trigger)
            # wait for power supply or oscope trigger.
            while not self.oscope_trigger.is_set() and not self.power_trigger.is_set():
                time.sleep(0.01)
            
            # record which event triggers first
            if self.oscope_trigger.is_set():
                trigger_str = "osc"
            elif self.power_trigger.is_set():
                trigger_str = "pwr"
            self.logger.info(f"Discharge detected. Source: {trigger_str}")
            # check to ensure all threads have closed/check all triggers.
            self.controller.run("nidaq_stop", "nidaq", "stop_pressure_acquisition")
            self.controller.run("dmm_stop", "dmm", "stop_continuous_measure")
            

            
        except Exception as e:
            self.logger.warning(f"experiment run failed due to exception: {str(e)}")
            return DischargeSkipped(params.index, str(e))
        return DischargeComplete(params.index, nidaq.pressure.latest[1], self.controller.get("pwr").latest[0], self.controller.get("pwr").latest[1], trigger_str)

    def _wait_for_thread_close(self, nidaq: NIDAQEquipment, dmm: KeithleyDMM6500, osc: SiglentSDS1204XE, pwr: Keithley2260B_800_1):
        if nidaq.pressure._running:
            self.controller.run("nidaq_stop", "nidaq", "stop_pressure_acquisition")
        if dmm._running:
            self.controller.run("dmm_stop", "dmm", "stop_continuous_measurement")
        if pwr._output:
            self.controller.run("pwr_stop", "pwr", "stop")
        if not osc.triggered:
            self.controller.run("osc_stop", "osc", "stop")
        time.sleep(0.5)

        

    def _wait_for_atmosphere(self, nidaq: NIDAQEquipment):
        nidaq.open_valve(2)
        self.controller.run("nidaq_pressure_read", 'nidaq', "start_pressure_acquisition", stop_event = self.pressure_atmosphere_set, target_=750, target_trigger='rising')
        while not self.pressure_atmosphere_set.is_set():
            time.sleep(0.01)
        self.logger.info("Chamber reached atmospheric pressure")
        return