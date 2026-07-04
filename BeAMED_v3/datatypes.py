from dataclasses import dataclass, field
import numpy as np
from datetime import datetime


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
    voltage_cr: float = 0.0
    current_cr: float = 0.0
    pressure_cr_mks: float = 0.0
    pressure_cr_kjl: float = 0.0
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

    gas_species: str = ""
    cathode_material: str = ""
    anode_material: str = ""
    cathode_shape: str = ""
    anode_shape: str = ""
    notes: str = ""

    @property
    def pressures(self) -> np.ndarray:
        return np.linspace(
            self.start_pressure,
            self.stop_pressure,
            self.n_discharges,
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

@dataclass
class DischargeComplete:
    index: int
    pressure: float
    voltage: float
    current: float
    source: str

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
    voltage: np.ndarray
    time: np.ndarray
    dy: float
    t_discharge: float

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
    pressure: PressureTimeseries = field(default_factory=PressureTimeseries) 
    mfc: MFCTimeseries = field(default_factory=MFCTimeseries)
    dmm: DMMSeries = field(default_factory=DMMSeries)
    power_supply: PowerSeries = field(default_factory=PowerSeries)
    waveform: Waveform = field(default_factory=Waveform)
    t_start: float | None = None
    t_end: float | None = None