from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BJTLimits:
    MAX_VCE: float
    MAX_VBE: float
    MAX_VBC: Optional[float] = None
    MAX_IB: Optional[float] = None
    MAX_IC: Optional[float] = None
    MAX_IE: Optional[float] = None
    MAX_POWER: Optional[float] = None
    MAX_TEMP: Optional[float] = None


@dataclass(frozen=True)
class ResistorLimits:
    MAX_RES_CURRENT: float


@dataclass(frozen=True)
class BJTDevice:
    name: str
    # raw column names in DataFrame
    col_vc: str
    col_vb: str
    col_ve: str
    col_ib: Optional[str] = None
    col_ic: Optional[str] = None
    col_ie: Optional[str] = None
    col_temp: Optional[str] = None
    limits: BJTLimits = None  # type: ignore[assignment]


@dataclass(frozen=True)
class ResistorDevice:
    name: str
    col_ir: str
    limits: ResistorLimits

