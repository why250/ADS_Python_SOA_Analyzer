"""ADS GUI entrypoint.

If invoked with two arguments (design_name, workspace_path) the GUI will
initialize fields and start a background thread to run simulation and
convert the resulting dataset to CSV, then load it into the GUI for
analysis. This keeps ADS responsive because AEL will launch this script
as a separate process.
"""
from typing import Optional
import sys
import threading
import logging
from pathlib import Path

# Setup simple file logger to capture startup errors when launched from ADS
log_file = Path(__file__).parent / "ads_soa_gui.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info("Starting main.py; argv=%s", sys.argv)

try:
    from PyQt6 import QtWidgets, QtCore
except ModuleNotFoundError as e:  # pragma: no cover
    raise SystemExit(
        "缺少依赖：PyQt6。\n"
        "请先安装依赖：\n"
        "  pip install -r requirements.txt\n"
    ) from e

from gui.main_window import MainWindow


def _background_run(workspace: str, lib: str, cell: str, win: MainWindow) -> None:
    """Run ADS simulation and conversion in a background thread, then
    schedule CSV loading on the Qt main thread."""
    try:
        from core.ads_sim import run_simulation_task, convert_ds_task
    except Exception as e:
        logger.exception("Failed to import ADS simulation helpers: %s", e)
        # Could not import ADS helpers; schedule a status update
        def _err():
            win.lbl_status.setText(f"ADS import error: {e}")
        QtCore.QTimer.singleShot(0, _err)
        return

    try:
        ds_path = run_simulation_task(workspace, lib, cell)
    except Exception as e:
        logger.exception("Simulation failed: %s", e)
        def _sim_err():
            win.lbl_status.setText(f"Simulation error: {e}")
        QtCore.QTimer.singleShot(0, _sim_err)
        return

    try:
        csv_path = convert_ds_task(ds_path)
    except Exception as e:
        logger.exception("Conversion failed: %s", e)
        def _conv_err():
            win.lbl_status.setText(f"Conversion error: {e}")
        QtCore.QTimer.singleShot(0, _conv_err)
        return

    # Schedule CSV loading on main thread
    def _load_csv():
        win._load_csv_from_path(csv_path)

    QtCore.QTimer.singleShot(0, _load_csv)


def main(argv: Optional[list] = None) -> int:
    if argv is None:
        argv = sys.argv

    app = QtWidgets.QApplication([])
    win = MainWindow()

    # If ADS passed design/workspace, use them and start background work
    design_name = None
    workspace_path = None
    if len(argv) >= 3:
        design_name = argv[1]
        workspace_path = argv[2]

    # Apply initial values to UI fields
    if workspace_path:
        win.state.workspace = workspace_path
        try:
            win.edit_workspace.setText(workspace_path)
        except Exception:
            logger.exception("Failed to set workspace in GUI")
    if design_name:
        # design_name from ADS must be exactly 'lib:cell:schematic'
        parts = design_name.split(":")
        if len(parts) != 3 or parts[2].lower() != "schematic":
            # Inform user via GUI and log; do not auto-start simulation
            msg = (
                "Invalid design_name format received from ADS.\n"
                "Expected: lib_name:cell_name:schematic\n"
                f"Got: {design_name}"
            )
            logger.error(msg)
            # Ensure GUI shows the raw value so user can correct it
            win.state.cell_name = design_name
            if hasattr(win, "edit_design"):
                try:
                    win.edit_design.setText(design_name)
                except Exception:
                    logger.exception("Failed to set design in GUI")
            # Show blocking error dialog so user is aware
            QtWidgets.QMessageBox.critical(None, "Invalid design_name", msg)
            # Do not proceed to auto-run simulation
            design_name = None
        else:
            lib_from_design = parts[0]
            cell_from_design = parts[1]
            # Update state.lib_name and GUI cell
            win.state.design_name = design_name
            win.state.lib_name = lib_from_design
            win.state.cell_name = cell_from_design
            if hasattr(win, "edit_design"):
                try:
                    win.edit_design.setText(design_name)
                except Exception:
                    logger.exception("Failed to set design in GUI")

    win.show()

    # If both workspace and design are present, run simulation+convert in background
    if workspace_path and design_name:
        # Use parsed/internal lib name and the GUI cell name
        lib = win.state.lib_name
        cell = win.state.cell_name
        t = threading.Thread(target=_background_run, args=(workspace_path, lib, cell, win), daemon=True)
        t.start()

    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        logger.exception("Unhandled exception in main executable")
        raise