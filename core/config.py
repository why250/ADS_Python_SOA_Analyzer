from __future__ import annotations

import json
from typing import Dict, Tuple


def load_limits(path: str) -> Tuple[Dict, Dict]:
    """Load JSON limits and split into defaults and overrides."""
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    defaults = cfg.get("defaults", {})
    overrides = cfg.get("overrides", {})
    return defaults, overrides

