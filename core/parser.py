from __future__ import annotations

import re
from typing import Dict, List, Tuple

import pandas as pd

from .models import BJTDevice, BJTLimits, ResistorDevice, ResistorLimits


def short_name_from_column(col: str) -> str:
    """
    Extract a short device name from ADS-like hierarchical column.
    Example: 'Testbench.Q1.Q1.c' -> 'Q1', 'R2.R_contact.i' -> 'R2'
    """
    parts = col.split(".")
    for token in reversed(parts):
        if re.match(r"^[QR]\w*", token):
            return token
    if len(parts) >= 2:
        return parts[-2]
    return col


def bjt_device_name_from_base_key(base_key: str) -> str:
    """
    Device name for BJT: distinguishes Q1 vs X1.Q1 (Q1 inside module X1).
    Strip trailing '.Q<id>' so 'Q1.Q1' -> 'Q1', 'X1.Q1.Q1' -> 'X1.Q1'.
    """
    return re.sub(r"\.Q\w*$", "", base_key) or base_key


def resistor_device_name_from_column(col: str) -> str:
    """
    Device name for resistor: full prefix so R1.R_contact and R2.R_contact are distinct.
    Example: 'R1.R_contact.i' -> 'R1.R_contact', 'R2.R_contact.i' -> 'R2.R_contact'
    """
    if col.endswith(".R_contact.i"):
        return col[: -len(".i")]  # strip trailing ".i" only
    return short_name_from_column(col)


def scan_csv_columns(df: pd.DataFrame, defaults: Dict, overrides: Dict) -> Tuple[List[BJTDevice], List[ResistorDevice], str]:
    """
    Auto-discover BJT and resistor devices based on column suffix rules.
    Returns (bjt_devices, resistor_devices, time_col_name).
    """
    columns = list(df.columns)

    time_col = None
    for c in columns:
        if c.lower() == "time":
            time_col = c
            break
    if not time_col:
        raise ValueError("CSV 中缺少 'time' 列")

    # Map: base_key -> suffix -> column_name
    bjt_groups: Dict[str, Dict[str, str]] = {}
    for col in columns:
        if col == time_col:
            continue
        m = re.search(r"\.(c|b|e|Lb\.i|Lc\.i|Le\.i|t)$", col)
        if m:
            suf = m.group(1)
            base_key = col[: -len(m.group(0))]  # strip ".c" or ".Lb.i" etc.
            grp = bjt_groups.setdefault(base_key, {})
            grp[suf] = col

    bjt_devices: List[BJTDevice] = []
    for base_key, grp in bjt_groups.items():
        if not all(k in grp for k in ("c", "b", "e")):
            continue

        name = bjt_device_name_from_base_key(base_key)
        # Merge currents from same device (e.g. Q1.Lb.i for base_key Q1.Q1, or X1.Q1 for X1.Q1.Q1)
        name_grp = bjt_groups.get(name, {})
        col_ib = grp.get("Lb.i") or name_grp.get("Lb.i")
        col_ic = grp.get("Lc.i") or name_grp.get("Lc.i")
        col_ie = grp.get("Le.i") or name_grp.get("Le.i")
        col_temp = grp.get("t") or name_grp.get("t")

        merged = {**defaults.get("BJT", {}), **overrides.get(name, {})}
        limits = BJTLimits(
            MAX_VCE=merged.get("MAX_VCE", float("inf")),
            MAX_VBE=merged.get("MAX_VBE", float("inf")),
            MAX_VBC=merged.get("MAX_VBC"),
            MAX_IB=merged.get("MAX_IB"),
            MAX_IC=merged.get("MAX_IC"),
            MAX_IE=merged.get("MAX_IE"),
            MAX_POWER=merged.get("MAX_POWER"),
            MAX_TEMP=merged.get("MAX_TEMP"),
        )

        bjt_devices.append(
            BJTDevice(
                name=name,
                col_vc=grp["c"],
                col_vb=grp["b"],
                col_ve=grp["e"],
                col_ib=col_ib,
                col_ic=col_ic,
                col_ie=col_ie,
                col_temp=col_temp,
                limits=limits,
            )
        )

    resistor_devices: List[ResistorDevice] = []
    for col in columns:
        if col.endswith(".R_contact.i"):
            name = resistor_device_name_from_column(col)
            merged = {**defaults.get("RESISTOR", {}), **overrides.get(name, {})}
            limits = ResistorLimits(MAX_RES_CURRENT=merged.get("MAX_RES_CURRENT", float("inf")))
            resistor_devices.append(ResistorDevice(name=name, col_ir=col, limits=limits))

    return bjt_devices, resistor_devices, time_col

