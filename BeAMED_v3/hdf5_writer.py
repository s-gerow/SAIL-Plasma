import h5py
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from datatypes import RunData, ExperimentMeta, DischargeMeta, DischargeData

class HDF5Writer:
    def __init__(self, log_queue=None):
        self.logger = logging.getLogger("BeAMED.hdf5")
        self._filepath: Path | None = None
        self._meta: ExperimentMeta | None
        self._save_dir: Path = Path("c:/Users/gerows/Python/SAIL-Plasma/BeAMED_v3/data")

    def new_file(self, filepath: str | Path, meta: ExperimentMeta):
        self._filepath = Path(filepath)
        self._meta = meta
        with h5py.File(self._save_dir/self._filepath, 'w') as f:
            grp = f.require_group("meta")
            self._write_meta(grp, meta)
            f.require_group("discharges")
        self.logger.info(f"Created new file: {self._save_dir/self._filepath}")

    def import_file(self, filepath: str | Path) -> ExperimentMeta:
        self._filepath = Path(filepath)
        with h5py.File(self._save_dir/self._filepath, 'r') as f:
            meta = self._read_meta(f["meta"])
        self._meta = meta
        self.logger.info(f"Imported file: {self._save_dir/self._filepath}")
        return meta
    
    def close(self):
        self._filepath = None
        self._meta = None

    @property
    def is_open(self) -> bool:
        return self._filepath is not None
    
    @property
    def filepath(self) -> Path | None:
        return self._filepath
    
    def next_discharge_index(self) -> int:
        if not self._filepath:
            raise RuntimeError("No file open")
        with h5py.File(self._save_dir/self._filepath, 'r') as f:
            existing = list(f["discharges"].keys())
        if not existing:
            return 1
        indices = [int(k.split("_")[1]) for k in existing]
        return max(indices) + 1
    
    def save_discharge(self, run: RunData):
        if not self._filepath:
            raise RuntimeError("No file open")

        idx = run.meta.index
        key = f"discharge_{run.meta.index:03d}"

        with h5py.File(self._save_dir/self._filepath, 'a') as f:
            if key in f["discharges"]:
                self.logger.warning(f"Overwritting existing {key}")
            grp = f["discharges"].require_group(key)

            self._write_discharge_meta(grp.require_group("meta"), run.meta)
            self._write_discharge_critical_data(grp.require_group("critical data"), run.critical_data)

            if run.waveform.voltage:
                wf = grp.require_group("waveform")
                wf.create_dataset("voltage", data=np.array(run.waveform.voltage))
                wf.create_dataset("time_axis", data=np.array(run.waveform.time))
                if run.waveform.dy is not None:
                    wf.attrs["dy"] = run.waveform.dy
            
            self._write_timeseries(
                grp.require_group("pressure"),
                {
                    "mks_values": [v for _, v in run.pressure.samples_mks],
                    "mks_times": [t for t, _ in run.pressure.samples_mks],
                    "kjl_values": [v for _, v in run.pressure.samples_kjl],
                    "kjl_times": [t for t, _ in run.pressure.samples_kjl]
                },
                t_trigger=run.pressure.t_trigger
            )

            self._write_timeseries(
                grp.require_group("mfc"),
                {
                    "readback_values": [v for _, v in run.mfc.samples_readback],
                    "readback_times": [t for t, _ in run.mfc.samples_readback],
                    "setpoint_values": [v for _,v in run.mfc.samples_setpoint],
                    "setpoint_times": [t for t, _ in run.mfc.samples_setpoint]
                },
                t_trigger=run.mfc.t_trigger
            )

            self._write_timeseries(
                grp.require_group("power_supply"),
                {
                    "voltage_values": [v for _,v in run.power_supply.samples_voltage],
                    "voltage_times": [t for t,_ in run.power_supply.samples_voltage],
                    "current_values": [v for _,v in run.power_supply.samples_current],
                    "current_times": [t for t,_ in run.power_supply.samples_current]
                },
                t_trigger=run.power_supply.t_trigger,
            )

            self._write_timeseries(
                grp.require_group("dmm"),
                {
                    "voltage_values": [v for _, v in run.dmm.samples_voltage],
                    "voltage_times": [t for t,_ in run.dmm.samples_voltage]
                },
                t_trigger=run.dmm.t_trigger
            )

        self.logger.info(f"Saved {key} to {self._filepath.name}")

    def _write_meta(self, grp: h5py.Group, meta: ExperimentMeta):
        self.logger.info(f"received metedata: {meta}")
        grp.attrs["gap_cm"] = meta.gap_cm
        grp.attrs["gas_species"] = meta.gas_species
        grp.attrs["cathode_material"] = meta.cathode_material
        grp.attrs["anode_material"] = meta.anode_material
        grp.attrs["cathode_shape"] = meta.cathode_shape
        grp.attrs["anode_shape"] = meta.anode_shape
        grp.attrs["notes"] = meta.notes
        grp.attrs["date_created"] = meta.date_created

    def _read_meta(self, grp: h5py.Group) -> ExperimentMeta:
        return ExperimentMeta(
            gap_cm = float(grp.attrs["gap_cm"]),
            gas_species= str(grp.attrs["gas_species"]),
            cathode_material= str(grp.attrs["cathode_material"]),
            anode_material= str(grp.attrs["anode_material"]),
            cathode_shape= str(grp.attrs["cathode_shape"]),
            anode_shape= str(grp.attrs["anode_shape"]),
            notes = str(grp.attrs.get("notes", "")),
            date_created= str(grp.attrs.get("date_created", ""))
        )
    
    def _write_discharge_meta(self, grp: h5py.Group, meta: DischargeMeta):
        grp.attrs["index"] = meta.index
        grp.attrs["date"] = meta.date
        grp.attrs["trigger_source"] = meta.trigger_source
        grp.attrs["notes"] = meta.notes

        for field in ("gap_cm", "gas_species", "cathode_material", "anode_material", "cathode_shape", "anode_shape"):
            val = getattr(meta, field)
            if val is not None:
                grp.attrs[field] = val

    def _write_timeseries(self, grp: h5py.Group, datasets: dict, t_trigger: float | None = None):
        for name, data in datasets.items():
            if data:
                grp.create_dataset(name, data=np.array(data, dtype=np.float64))
            if t_trigger is not None:
                grp.attrs["t_trigger"] = t_trigger

    def _write_discharge_critical_data(self, grp: h5py.Group, data: DischargeData):
        grp.attrs["gap_cm"] = data.gap_cm
        grp.attrs["pressure_mks"] = data.pressure_mks
        grp.attrs["pressure_kjl"] = data.pressure_kjl
        grp.attrs["voltage_pwr"] = data.voltage_pwr
        grp.attrs["current_pwr"] = data.current_pwr
        grp.attrs["voltage_dmm"] = data.voltage_dmm
        grp.attrs["source"] = data.source

        grp.attrs["pressure_kjl_err"] = data.pressure_kjl_err
        grp.attrs["pressure_mks_err"] = data.pressure_mks_err
        grp.attrs["voltage_pwr_err"] = data.voltage_pwr_err
        grp.attrs["current_pwr_err"] = data.current_pwr_err
        grp.attrs["voltage_dmm_err"] = data.voltage_dmm_err
        grp.attrs["gap_err"] = data.gap_err
        grp.attrs["pd_kjl_err"] = data.pd_kjl_err
        grp.attrs["pd_mks_err"] = data.pd_mks_err