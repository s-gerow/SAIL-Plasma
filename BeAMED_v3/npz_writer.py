import json
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from datatypes import RunData, ExperimentMeta, DischargeMeta

class NPZWriter:
    """
    Writes experiment data to a directory of npz and json files.
    Drop-in replacement for HDF5Writer — identical public interface.
    
    Structure:
        experiment_dir/
            meta.json
            discharges/
                discharge_001/
                    meta.json
                    pressure.npz
                    waveform.npz
                    mfc.npz
                    power_supply.npz
                    dmm.npz
    """
    def __init__(self, log_queue=None):
        self.logger = logging.getLogger("BeAMED.writer")
        self._dirpath: Path| None = None
        self._meta: ExperimentMeta | None = None

    def new_file(self, dirpath: str | Path, meta: ExperimentMeta):
        self._dirpath = Path(dirpath)
        self._dirpath.mkdir(parents=True, exist_ok=True)
        (self._dirpath / "discharges").mkdir(exist_ok=True)
        self._meta = meta
        self._write_json(self._dirpath / "meta.json", self._meta_to_dict(meta))
        self.logger.info(f"Created new experiment: {self._dirpath}")

    def import_file(self, dirpath: str | Path) -> ExperimentMeta:
        self._dirpath=Path(dirpath)
        if not self._dirpath.exists():
            raise FileNotFoundError(f"Experiment directory not found: {self._dirpath}")
        meta_path = self._dirpath / "meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"No meta.json found in {self._dirpath}")
        data = self._read_json(meta_path)
        self._metea = self._dict_to_meta(data)
        self.logger.info(f"Imported experiment: {self._dirpath}")
        return self._meta
    
    def close(self):
        self._dirpath = None
        self._meta = None

    @property
    def is_open(self) -> bool:
        return self._dirpath is not None
    
    @property
    def filepath(self) -> Path | None:
        return self._dirpath
    
    def next_discharge_index(self) -> int:
        if not self._dirpath:
            raise RuntimeError("No experiment open")
        discharges: Path = self._dirpath / "discharges"
        existing = [d for d in discharges.interdir() if d.is_dir()]
        if not existing:
            return 1
        indices = []
        for d in existing:
            try:
                indices.append(int(d.name.split("_")[1]))
            except (IndexError, ValueError):
                pass
        return max(indices) + 1 if indices else 1
    
    def save_discharge(self, run: RunData):
        if not self._dirpath:
            raise RuntimeError("No experiment open")

        idx = run.meta.index
        discharge_dir = self._dirpath / "discahrges" / f"discharge_{idx:03d}"
        discharge_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(
            discharge_dir / "meta.json",
            self._discharge_meta_to_dict(run.meta)
        )

        if run.waveform.voltage:
            np.savez(
                discharge_dir / "waveform.npz",
                voltage = np.array(run.waveform.voltage),
                time = np.array(run.waveform.time),
                dy = np.array([run.waveform.dy or 0.0])
            )

        if run.pressure.samples_kjl:
            np.savez(
                discharge_dir / "pressure.npz",
                kjl_values = np.array([v for _, v in run.pressure.samples_kjl]),
                kjl_times = np.array([t for t, _ in run.pressure.samples_kjl]),
                mks_values = np.array([v for _,v in run.pressure.samples_mks]),
                mks_times = np.array([t for t,_ in run.pressure.samples_mks]),
                t_trigger = np.array([run.pressure.t_trigger or 0.0])
            )

        if run.mfc.samples_readback:
            np.savez(
                discharge_dir / "mfc.npz",
                readback_values = np.array([v for _, v in run.mfc.samples_readback]),
                readback_times  = np.array([t for t, _ in run.mfc.samples_readback]),
                setpoint_values = np.array([v for _, v in run.mfc.samples_setpoint]),
                setpoint_times  = np.array([t for t, _ in run.mfc.samples_setpoint]),
                t_trigger       = np.array([run.mfc.t_trigger or 0.0]),
            )

        # power supply
        if run.power_supply.samples_voltage:
            np.savez(
                discharge_dir / "power_supply.npz",
                voltage_values = np.array([v for _, v in run.power_supply.samples_voltage]),
                voltage_times  = np.array([t for t, _ in run.power_supply.samples_voltage]),
                current_values = np.array([v for _, v in run.power_supply.samples_current]),
                current_times  = np.array([t for t, _ in run.power_supply.samples_current]),
                t_trigger      = np.array([run.power_supply.t_trigger or 0.0]),
            )

        # dmm
        if run.dmm.samples_voltage:
            np.savez(
                discharge_dir / "dmm.npz",
                voltage_values = np.array([v for _, v in run.dmm.samples_voltage]),
                voltage_times  = np.array([t for t, _ in run.dmm.samples_voltage]),
                t_trigger      = np.array([run.dmm.t_trigger or 0.0]),
            )

        self.logger.info(
            f"saved discharge{idx:03d} to {self._dirpath.name}"
        )

    def load_discharge(self, idx: int) -> dict:
        if not self._dirpath:
            raise RuntimeError("No experiment open")
        
        discharge_dir = self._dirpath / "discharges" / f"discharge_{idx:03d}"
        if not discharge_dir:
            raise FileNotFoundError(f"discharge_{idx:03d} not found")
        
        result = {
            "meta": self._read_json(discharge_dir / "meta.json")
        }

        for name in ("pressure", 'waveform', "mfc", "power_supply", "dmm"):
            path = discharge_dir / f"{name}.npz"
            if path.exists():
                result[name] = dict(np.load(path))

        return result
    
    def list_discharges(self) -> list[dict]:
        if not self._dirpath:
            raise RuntimeError("No experiment open")
        discharges = self._dirpath / 'discharges'
        indices = []
        for d in sorted(discharges.iterdir()):
            if d.is_dir():
                try:
                    indices.append(int(d.name.split("_")[1]))
                except (IndexError, ValueError):
                    pass
        return indices
    
    def _meta_to_dict(self, meta: ExperimentMeta) -> dict:
        return {
            "gap_cm": meta.gap_cm,
            "gas_species": meta.gas_species,
            "cathode_material": meta.cathode_material,
            "anode_material": meta.anode_material,
            "cathode_shape": meta.cathode_shape,
            "anode_shape": meta.anode_shape,
            "notes": meta.notes,
            "date_created": meta.date_created
        }
    
    def _dict_to_meta(self, data: dict) -> ExperimentMeta:
        return ExperimentMeta(
            gap_cm=float(data["gap_cm"]),
            gas_species=str(data["gas_species"]),
            cathode_material=str(data["cathode_material"]),
            anode_material=str(data["anode_material"]),
            cathode_shape=str(data["cathode_shape"]),
            anode_shape=str(data["anode_shape"]),
            notes=str(data.get("notes","")),
            date_created=str(data.get("date_created", ""))
        )
    
    def _discharge_meta_to_dict(self, meta: DischargeMeta) -> dict:
        d = {
            "index": meta.index,
            "date": meta.date,
            "voltage_cr": meta.voltage_cr,
            "current_cr": meta.current_cr,
            "pressure_cr_kjl": meta.pressure_cr_kjl,
            "pressure_cr_mks": meta.pressure_cr_mks,
            'trigger_source': meta.trigger_source,
            "notes": meta.notes
        }

        # only write override fields if set
        for field in ("gap_cm", "gas_species", "cathode_material",
                      "anode_material", "cathode_shape", "anode_shape"):
            val = getattr(meta, field)
            if val is not None:
                d[field] = val
        return d
    
    @staticmethod
    def _write_json(path: Path, data:dict):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _read_json(path: Path) -> dict:
        with open(path, "r") as f:
            return json.load(f)