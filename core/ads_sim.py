from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def run_simulation_task(workspace: str, lib: str, cell: str) -> str:
    """
    Run ADS transient simulation using Keysight ADS Python APIs.

    Returns the path to the generated .ds file.
    """
    # Lazy imports so that normal SOA GUI can run without ADS environment
    from keysight.ads import de
    from keysight.ads.de import db_uu as db
    from keysight.edatoolbox import ads

    workspace_path = Path(workspace)
    if not workspace_path.exists():
        raise FileNotFoundError(f"Workspace path does not exist: {workspace_path}")

    # Open workspace
    de.open(workspace_path)

    design_str = f"{lib}:{cell}:schematic"
    target_output_dir = workspace_path / "data"
    target_output_dir.mkdir(parents=True, exist_ok=True)

    design = db.open_design(design_str)
    netlist = design.generate_netlist()
    simulator = ads.CircuitSimulator()
    simulator.run_netlist(netlist, output_dir=str(target_output_dir))

    ds_path = target_output_dir / f"{cell}.ds"
    return str(ds_path)


def convert_ds_task(ds_file_path: str) -> str:
    """
    Convert an ADS dataset (.ds) to CSV using pandas DataFrame.

    Returns the path to the generated .csv file.
    """
    import keysight.ads.dataset as dataset

    ds_path = Path(ds_file_path)
    if not ds_path.exists():
        raise FileNotFoundError(f"Dataset file does not exist: {ds_path}")

    output_data = dataset.open(ds_path)

    time_block_name: Optional[str] = None
    for data_block in output_data.find_varblocks_with_var_name("time"):
        time_block_name = data_block.name
        break

    if not time_block_name:
        raise ValueError("No transient data block containing 'time' was found in dataset.")

    df = output_data[time_block_name].to_dataframe().reset_index()

    base_name = os.path.splitext(str(ds_path))[0]
    csv_path = base_name + ".csv"
    df.to_csv(csv_path, index=False)
    return csv_path

