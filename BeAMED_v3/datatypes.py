from dataclasses import dataclass, field
import numpy as np

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

    @property
    def pressures(self) -> np.ndarray:
        return np.linspace(
            self.start_pressure,
            self.stop_pressure,
            self.n_discharges,
            endpoint=True
        )

@dataclass
class DischargeComplete:
    index: int
    pressure: float
    voltage: float
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
    pass

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
    voltage: np.ndarray
    current: np.ndarray
    time: np.ndarray
    t_discharge: float
