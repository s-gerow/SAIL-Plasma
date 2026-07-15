from dataclasses import dataclass, field
import numpy as np
from datetime import datetime
from pathlib import Path


# ── Controller queue message types ────────────────────────────────────────────

@dataclass
class ConnectResult:
    key: str
    success: bool
    error: str | None = None

@dataclass
class DisconnectResult:
    key: str
    success: bool
    error: str | None = None

@dataclass
class ActionResult:
    key: str
    action: str
    success: bool
    data: dict = field(default_factory=dict)
    error: str| None = None

@dataclass
class StepResult:
    step_name: str
    success: bool
    data: dict = field(default_factory=dict)
    error: str| None = None

@dataclass
class SequenceComplete:
    success: bool
    aborted: bool = False

# ── Experiment process event types ────────────────────────────────────────────
@dataclass
class ExperimentMeta:
    gap_cm: float
    gas_species: str
    cathode_material: str
    anode_material: str
    cathode_shape: str
    anode_shape: str
    notes: str = ""
    date_created: str = field(
        default_factory=lambda:datetime.now().isoformat()
    )

    CONSTANT_FIELDS = {
        "gap_cm", "gas_species", "cathode_material", "anode_material", "cathode_shape", "anode_shape"
    }

    def mismatches(self, other: 'ExperimentMeta') -> dict:
        result = {}
        for field in self.CONSTANT_FIELDS:
            a = getattr(self, field)
            b = getattr(other, field)
            if a != b:
                result[field] = (a,b)
        return result
    
@dataclass
class DischargeMeta:
    index: int
    date: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    trigger_source: str = ""
    notes: str = ""

    gap_cm: float | None = None
    gas_species: float | None = None
    cathode_material: str | None = None
    anode_material: str | None = None
    cathode_shape: str | None = None
    anode_shape: str | None = None

@dataclass
class ExperimentParams:
    start_pressure: float
    stop_pressure: float
    n_discharges: int
    gap_cm: float
    start_voltage: float
    dV: float
    dwell_time: float
    target_pressure: float
    pi_timeout: float = 120
    index: int | None = None
    save_path: Path = None

    gas_species: str = ""
    cathode_material: str = ""
    anode_material: str = ""
    cathode_shape: str = ""
    anode_shape: str = ""
    notes: str = ""

    @property
    def pressures(self) -> np.ndarray:
        return np.linspace(
            start = self.start_pressure,
            stop = self.stop_pressure,
            num = int(self.n_discharges),
            endpoint=True
        )
    
    def to_meta(self) -> ExperimentMeta:
        return ExperimentMeta(
            gap_cm=self.gap_cm,
            gas_species=self.gas_species,
            cathode_material=self.cathode_material,
            anode_material=self.anode_material,
            cathode_shape=self.cathode_shape,
            anode_shape=self.anode_shape,
            notes=self.notes
        )
    
    def issameparams(self, other_params: ExperimentMeta):
        if self.gas_species != other_params.gas_species:
            return False
        elif self.gap_cm != other_params.gap_cm:
            return False
        elif self.cathode_material != other_params.cathode_material:
            return False
        elif self.anode_material != other_params.anode_material:
            return False
        elif self.cathode_shape != other_params.cathode_shape:
            return False
        elif self.anode_shape != other_params.anode_shape:
            return False
        else:
            return True

@dataclass
class DischargeComplete:
    index: int
    pressure_mks: float
    pressure_kjl: float
    voltage: float
    current: float
    source: str

@dataclass
class DischargeData:
    gap_cm: float = None
    pressure_mks: float = None
    pressure_kjl: float = None
    voltage_pwr: float = None
    current_pwr: float = None
    voltage_dmm: float = None
    source: str = None

    pressure_kjl_err: float = None
    pressure_mks_err: float = None
    voltage_pwr_err: float = None
    current_pwr_err: float = None
    voltage_dmm_err: float = None
    gap_err: float = None
    pd_kjl_err: float = None
    pd_mks_err: float = None

    def calculate_errors(self):
        #~21 C, 40-50% humidity
        self.pressure_kjl_err = self.pressure_kjl * 0.1
        self.pressure_mks_err = self.pressure_mks*0.005 if self.pressure_mks < 1 else self.pressure_mks*0.0025
        self.voltage_pwr_err = self.voltage_pwr*0.001 + 0.400 #uncertainty in measured voltage: 0.1% + 400mV
        self.current_pwr_err = self.current_pwr*0.001 + 0.002 #uncertainty in measured current: 0.1% + 2mA
        #self.voltage_dmm_err = self.voltage_dmm*0.000001 # old uncertainty
        self.voltage_dmm_err = (0.00004 * self.voltage_dmm) + (0.000006 * 1000) + (0.00002 * max(0, self.voltage_dmm-500))
        self.gap_err = 0.05
        self.pd_kjl_err = (self.pressure_kjl*self.gap_cm)*((self.pressure_kjl_err/self.pressure_kjl)+(0.05/self.gap_err)) #kurt J lesker d(pd)
        self.pd_mks_err = (self.pressure_mks*self.gap_cm)*((self.pressure_mks_err/self.pressure_mks)+(0.05/self.gap_err)) #MKS d(pd)



@dataclass
class DischargeSkipped:
    index: int
    reason: str

@dataclass
class ExperimentFailed:
    reason: str

@dataclass
class ExperimentComplete:
    n_discharges: int
    filepath: str

# ── Measurement data types ────────────────────────────────────────────────────

@dataclass
class Waveform:
    """Processed waveform data captured from the oscilloscope at discharge."""
    voltage: np.ndarray | None = None
    time: np.ndarray | None = None
    dy: float | None = None
    t_discharge: float | None = None

@dataclass
class PowerSeries:
    """Voltage and current timeseries recorded by the power supply."""
    samples_voltage: list[tuple[float, float]] = field(default_factory=list)
    samples_current: list[tuple[float, float]] = field(default_factory=list)
    t_trigger: float | None = None
    trigger_source:   str   | None = None

@dataclass
class DMMSeries:
    samples_voltage:  list[tuple[float, float]] = field(default_factory=list)
    samples_resistance: list[tuple[float, float]] = field(default_factory=list)
    t_trigger:        float | None = None
    trigger_source:   str   | None = None

@dataclass
class PressureTimeseries:
    samples_mks: list[tuple[float, float]] = field(default_factory=list)
    samples_kjl: list[tuple[float, float]] = field(default_factory=list)
    t_trigger: float | None = None
    trigger_source: str | None = None

@dataclass
class MFCTimeseries:
    samples_readback: list[tuple[float, float]] = field(default_factory=list)
    samples_setpoint: list[tuple[float, float]] = field(default_factory=list)
    t_trigger: float | None = None
    trigger_source: str | None = None

@dataclass
class RunData:
    meta: DischargeMeta
    critical_data: DischargeData = field(default_factory=DischargeData)
    pressure: PressureTimeseries = field(default_factory=PressureTimeseries) 
    mfc: MFCTimeseries = field(default_factory=MFCTimeseries)
    dmm: DMMSeries = field(default_factory=DMMSeries)
    power_supply: PowerSeries = field(default_factory=PowerSeries)
    waveform: Waveform = field(default_factory=Waveform)
    t_start: float | None = None
    t_end: float | None = None