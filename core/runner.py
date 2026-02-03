from __future__ import annotations

from typing import Optional
from pathlib import Path
import os
import sys
import json

import pandas as pd

from core.config import load_limits
from core.parser import scan_csv_columns
from core.analysis import analyze_all


def analyze_file(data_path: str, limits_path: Optional[str] = None, out_path: str = "soa_violations_report.csv") -> str:
    """
    Load a CSV data file and a JSON limits file, run analysis and write violations CSV.

    Parameters:
    - data_path: path to CSV file containing ADS simulation data.
    - limits_path: path to JSON limits file. If None, will try to use 'soa_limits_ex.json'
      in the repository root.
    - out_path: path to output CSV file (defaults to 'soa_violations_report.csv').

    Returns the output path on success.
    """
    data_p = Path(data_path)
    if not data_p.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    # Load data
    if data_p.suffix.lower() == ".csv":
        df = pd.read_csv(data_path)
    else:
        raise ValueError("Unsupported data file type. Please provide a CSV file for data.")

    # Resolve limits_path
    if limits_path is None:
        # Try repository root file
        repo_root = Path(__file__).resolve().parents[1]
        default_limits = repo_root / "soa_limits_ex.json"
        if default_limits.exists():
            limits_path = str(default_limits)
        else:
            raise ValueError("limits_path not provided and default 'soa_limits_ex.json' not found.")

    if not Path(limits_path).exists():
        raise FileNotFoundError(f"Limits JSON file not found: {limits_path}")

    defaults, overrides = load_limits(limits_path)

    # Discover devices
    bjt_devices, res_devices, time_col = scan_csv_columns(df, defaults, overrides)

    # Run analysis
    violations_df = analyze_all(df, bjt_devices, res_devices, time_col)

    # Ensure output directory exists
    out_p = Path(out_path)
    if out_p.parent and not out_p.parent.exists():
        out_p.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV (even if empty, keep columns)
    if violations_df is None or violations_df.empty:
        cols = ["Device Name", "Time", "Parameter", "Value", "Limit", "Violation Type"]
        pd.DataFrame(columns=cols).to_csv(out_path, index=False)
    else:
        violations_df.to_csv(out_path, index=False)

    return str(out_p)


def _parse_args(argv: Optional[list] = None) -> tuple[str, Optional[str], str]:
    """
    Very small CLI parser that accepts positional `data [limits [out]]` and
    also understands `--limits/-l` and `--out/-o` flags which override positional values.

    Returns (data, limits, out)
    """
    if argv is None:
        argv = sys.argv[1:]

    data = None
    limits = None
    out = "soa_violations_report.csv"

    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--limits", "-l"):
            if i + 1 >= len(argv):
                raise ValueError("Missing value for --limits")
            limits = argv[i + 1]
            i += 2
            continue
        if a in ("--out", "-o"):
            if i + 1 >= len(argv):
                raise ValueError("Missing value for --out")
            out = argv[i + 1]
            i += 2
            continue

        # Positional args
        if data is None:
            data = a
        elif limits is None:
            limits = a
        elif out == "soa_violations_report.csv":
            out = a
        else:
            # extra positional args ignored
            pass
        i += 1

    if data is None:
        raise ValueError("Missing data CSV path (first positional argument)")

    return data, limits, out


def main(argv: Optional[list] = None) -> int:
    try:
        data, limits, out = _parse_args(argv)
    except Exception as e:
        print(f"Error parsing arguments: {e}", file=sys.stderr)
        print("Usage: python -m core.runner <data.csv> [limits.json] [out.csv]  (flags: --limits/-l, --out/-o)")
        return 2

    try:
        out_path = analyze_file(data, limits, out)
        print(f"Violations written to: {out_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())