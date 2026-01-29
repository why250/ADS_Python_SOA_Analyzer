from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .models import BJTDevice, ResistorDevice


def analyze_bjt(df: pd.DataFrame, dev: BJTDevice, time_col: str) -> pd.DataFrame:
    """
    Compute VCE, VBE, VBC, currents, power, temp and flag violations.
    Returns a DataFrame with violation records for this device.
    """
    t = df[time_col].to_numpy()
    vc = df[dev.col_vc].to_numpy()
    vb = df[dev.col_vb].to_numpy()
    ve = df[dev.col_ve].to_numpy()

    vce = vc - ve
    vbe = vb - ve
    vbc = vb - vc

    ib = df[dev.col_ib].to_numpy() if dev.col_ib and dev.col_ib in df.columns else None
    ic = df[dev.col_ic].to_numpy() if dev.col_ic and dev.col_ic in df.columns else None
    ie = df[dev.col_ie].to_numpy() if dev.col_ie and dev.col_ie in df.columns else None
    temp = df[dev.col_temp].to_numpy() if dev.col_temp and dev.col_temp in df.columns else None

    records: List[Dict] = []

    def add_violations(mask: np.ndarray, param: str, values: np.ndarray, limit_val: float):
        idxs = np.nonzero(mask)[0]
        for i in idxs:
            records.append(
                {
                    "Device Name": dev.name,
                    "Time": t[i],
                    "Parameter": param,
                    "Value": float(values[i]),
                    "Limit": float(limit_val),
                    "Violation Type": "BJT",
                }
            )

    if np.isfinite(dev.limits.MAX_VCE):
        add_violations(np.abs(vce) > dev.limits.MAX_VCE, "VCE", vce, dev.limits.MAX_VCE)

    if np.isfinite(dev.limits.MAX_VBE):
        add_violations(np.abs(vbe) > dev.limits.MAX_VBE, "VBE", vbe, dev.limits.MAX_VBE)

    if dev.limits.MAX_VBC is not None:
        add_violations(np.abs(vbc) > dev.limits.MAX_VBC, "VBC", vbc, dev.limits.MAX_VBC)

    if dev.limits.MAX_IB is not None and ib is not None:
        add_violations(np.abs(ib) > dev.limits.MAX_IB, "IB", ib, dev.limits.MAX_IB)

    if dev.limits.MAX_IC is not None and ic is not None:
        add_violations(np.abs(ic) > dev.limits.MAX_IC, "IC", ic, dev.limits.MAX_IC)

    if dev.limits.MAX_IE is not None and ie is not None:
        add_violations(np.abs(ie) > dev.limits.MAX_IE, "IE", ie, dev.limits.MAX_IE)

    if dev.limits.MAX_POWER is not None and ic is not None and ib is not None:
        p = np.abs(vce * ic) + np.abs(vbe * ib)
        add_violations(p > dev.limits.MAX_POWER, "POWER", p, dev.limits.MAX_POWER)

    if dev.limits.MAX_TEMP is not None and temp is not None:
        add_violations(temp > dev.limits.MAX_TEMP, "TEMP", temp, dev.limits.MAX_TEMP)

    return pd.DataFrame.from_records(records)


def analyze_resistor(df: pd.DataFrame, dev: ResistorDevice, time_col: str) -> pd.DataFrame:
    t = df[time_col].to_numpy()
    ir = df[dev.col_ir].to_numpy()

    records: List[Dict] = []
    mask = np.abs(ir) > dev.limits.MAX_RES_CURRENT
    idxs = np.nonzero(mask)[0]
    for i in idxs:
        records.append(
            {
                "Device Name": dev.name,
                "Time": t[i],
                "Parameter": "IR",
                "Value": float(ir[i]),
                "Limit": float(dev.limits.MAX_RES_CURRENT),
                "Violation Type": "RESISTOR",
            }
        )
    return pd.DataFrame.from_records(records)


def analyze_all(
    df: pd.DataFrame, bjt_devices: List[BJTDevice], res_devices: List[ResistorDevice], time_col: str
) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for dev in bjt_devices:
        frames.append(analyze_bjt(df, dev, time_col))
    for dev in res_devices:
        frames.append(analyze_resistor(df, dev, time_col))
    if not frames:
        return pd.DataFrame(columns=["Device Name", "Time", "Parameter", "Value", "Limit", "Violation Type"])
    out = pd.concat(frames, ignore_index=True)
    if out.empty:
        out = pd.DataFrame(columns=["Device Name", "Time", "Parameter", "Value", "Limit", "Violation Type"])
    return out


def violated_device_names(violations_df: Optional[pd.DataFrame]) -> set[str]:
    if violations_df is None or violations_df.empty:
        return set()
    return set(violations_df["Device Name"].astype(str))

