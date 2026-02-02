from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from PyQt6 import QtCore, QtWidgets
import logging
import traceback

logger = logging.getLogger("ads_soa_gui")

from core.analysis import analyze_all, violated_device_names
from core.config import load_limits
from core.models import BJTDevice, ResistorDevice
from core.parser import scan_csv_columns
from gui.mpl_canvas import MplCanvas


@dataclass
class AppState:
    df: Optional[pd.DataFrame] = None
    defaults: Dict = None  # type: ignore[assignment]
    overrides: Dict = None  # type: ignore[assignment]
    bjt_devices: List[BJTDevice] = None  # type: ignore[assignment]
    res_devices: List[ResistorDevice] = None  # type: ignore[assignment]
    time_col: str = "time"
    violations_df: Optional[pd.DataFrame] = None
    limits_path: Optional[str] = None
    csv_path: Optional[str] = None
    workspace: str = str(Path.cwd())
    lib_name: str = "SOA_Tran_Check.lib"
    cell_name: str = "TB_EF_Tran"
    view_name: str = "schematic"
    design_name: str = "SOA_Tran_Check.lib:TB_EF_Tran:schematic"
    last_ds_path: Optional[str] = None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ADS Simulation Data SOA Analyzer")
        self.resize(1200, 800)

        self.state = AppState(defaults={}, overrides={}, bjt_devices=[], res_devices=[])
        self._build_ui()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        main_layout = QtWidgets.QVBoxLayout(central)

        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        # --- ADS Simulation & Data group ---
        sim_group = QtWidgets.QGroupBox("ADS Simulation & Data")
        sim_layout = QtWidgets.QVBoxLayout(sim_group)

        # Workspace (label above input, same style as Design)
        sim_layout.addWidget(QtWidgets.QLabel("Workspace:"))
        self.edit_workspace = QtWidgets.QLineEdit(self.state.workspace)
        sim_layout.addWidget(self.edit_workspace)

        # Design (replaces Lib/Cell inputs). Editable so user can change before running.
        self.edit_design = QtWidgets.QLineEdit(self.state.design_name)
        sim_layout.addWidget(QtWidgets.QLabel("Design:"))
        sim_layout.addWidget(self.edit_design)

        # Simulation buttons
        btn_run_sim = QtWidgets.QPushButton("Run Simulation")
        btn_convert_ds = QtWidgets.QPushButton("Convert .ds to Dataframe")
        btn_run_sim.clicked.connect(self.on_run_simulation)
        btn_convert_ds.clicked.connect(self.on_convert_ds)
        sim_layout.addWidget(btn_run_sim)
        sim_layout.addWidget(btn_convert_ds)

        left_layout.addWidget(sim_group)

        # Existing CSV / JSON controls
        btn_load_csv = QtWidgets.QPushButton("Load CSV Data")
        btn_load_json = QtWidgets.QPushButton("Load Limit Config (JSON)")
        btn_analyze = QtWidgets.QPushButton("Analyze")
        btn_analyze.setEnabled(False)  # Initially disabled until CSV and JSON are loaded
        btn_load_csv.clicked.connect(self.on_load_csv)
        btn_load_json.clicked.connect(self.on_load_json)
        btn_analyze.clicked.connect(self.on_analyze)

        left_layout.addWidget(btn_load_csv)
        left_layout.addWidget(btn_load_json)
        left_layout.addWidget(btn_analyze)
        self.btn_analyze = btn_analyze  # Store reference for enabling/disabling

        self.lbl_status = QtWidgets.QLabel("Ready")
        left_layout.addWidget(self.lbl_status)

        self.tree_devices = QtWidgets.QTreeWidget()
        self.tree_devices.setHeaderLabels(["Device", "Status"])
        self.tree_devices.itemSelectionChanged.connect(self.on_device_selected)
        left_layout.addWidget(self.tree_devices)

        splitter.addWidget(left_widget)

        # Right panel with tabs
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        self.tabs = QtWidgets.QTabWidget()
        right_layout.addWidget(self.tabs)

        # --- Top-level tabs ---
        self.tab_bjt_results = QtWidgets.QWidget()
        self.tab_res = QtWidgets.QWidget()
        self.tab_results = QtWidgets.QWidget()

        self.tabs.addTab(self.tab_bjt_results, "BJT Results")
        self.tabs.addTab(self.tab_res, "Resistor Results")
        self.tabs.addTab(self.tab_results, "Result Table")

        # --- BJT Results: nested tabs ---
        bjt_results_layout = QtWidgets.QVBoxLayout(self.tab_bjt_results)
        self.bjt_tabs = QtWidgets.QTabWidget()
        bjt_results_layout.addWidget(self.bjt_tabs)

        self.tab_bjt_soa = QtWidgets.QWidget()
        self.tab_bjt_v = QtWidgets.QWidget()
        self.tab_bjt_i = QtWidgets.QWidget()
        self.tab_bjt_p = QtWidgets.QWidget()
        self.tab_bjt_t = QtWidgets.QWidget()

        self.bjt_tabs.addTab(self.tab_bjt_soa, "BJT SOA")
        self.bjt_tabs.addTab(self.tab_bjt_v, "V (Time)")
        self.bjt_tabs.addTab(self.tab_bjt_i, "I (Time)")
        self.bjt_tabs.addTab(self.tab_bjt_p, "P (Time)")
        self.bjt_tabs.addTab(self.tab_bjt_t, "T (Time)")

        bjt_soa_layout = QtWidgets.QVBoxLayout(self.tab_bjt_soa)
        self.canvas_soa = MplCanvas()
        bjt_soa_layout.addWidget(self.canvas_soa)

        bjt_v_layout = QtWidgets.QVBoxLayout(self.tab_bjt_v)
        self.canvas_v = MplCanvas()
        bjt_v_layout.addWidget(self.canvas_v)

        bjt_i_layout = QtWidgets.QVBoxLayout(self.tab_bjt_i)
        self.canvas_i = MplCanvas()
        bjt_i_layout.addWidget(self.canvas_i)

        bjt_p_layout = QtWidgets.QVBoxLayout(self.tab_bjt_p)
        self.canvas_p = MplCanvas()
        bjt_p_layout.addWidget(self.canvas_p)

        bjt_t_layout = QtWidgets.QVBoxLayout(self.tab_bjt_t)
        self.canvas_t = MplCanvas()
        bjt_t_layout.addWidget(self.canvas_t)

        # --- Resistor Results ---
        res_layout = QtWidgets.QVBoxLayout(self.tab_res)
        self.canvas_res = MplCanvas()
        res_layout.addWidget(self.canvas_res)

        # Results tab: table + export
        results_layout = QtWidgets.QVBoxLayout(self.tab_results)
        results_title = QtWidgets.QLabel("Result Table")
        results_title.setStyleSheet("font-weight: 600;")
        results_layout.addWidget(results_title)

        self.table = QtWidgets.QTableWidget()
        results_layout.addWidget(self.table)

        btn_export = QtWidgets.QPushButton("Export Violations as CSV")
        btn_export.clicked.connect(self.on_export_csv)
        results_layout.addWidget(btn_export)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

    # ---------------- File operations ----------------
    def on_load_csv(self) -> None:
        # Default path: workspace/data/{cell_name}.csv (same base as .ds)
        start_dir = str(Path(self.state.workspace) / "data") if self.state.workspace else ""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open CSV Data", start_dir, "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        self._load_csv_from_path(path)

    def _load_csv_from_path(self, path: str, show_message: bool = True) -> bool:
        """Shared CSV-loading logic used by both manual load and DS conversion. Returns True on success."""
        try:
            df = pd.read_csv(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to read CSV:\n{e}")
            return False

        self.state.csv_path = path
        self.state.df = df

        # If no limits loaded yet, try default example file in current directory
        if not self.state.defaults:
            try:
                defaults, overrides = load_limits("soa_limits_ex.json")
                self.state.defaults, self.state.overrides = defaults, overrides
                self.state.limits_path = "soa_limits_ex.json"
            except Exception:
                self.state.defaults, self.state.overrides = {}, {}

        if show_message:
            QtWidgets.QMessageBox.information(
                self, "Success", f"CSV loaded successfully!\nRows: {len(df)}\nColumns: {len(df.columns)}"
            )

        self._update_analyze_button_state()
        return True

    def on_load_json(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open JSON Config", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        self._load_json_from_path(path, show_message=True)

    def _load_json_from_path(self, path: str, show_message: bool = True) -> bool:
        """Load limit config from JSON path. Returns True on success."""
        try:
            defaults, overrides = load_limits(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to read JSON:\n{e}")
            return False

        self.state.defaults, self.state.overrides = defaults, overrides
        self.state.limits_path = path

        if show_message:
            bjt_limits = defaults.get("BJT", {})
            res_limits = defaults.get("RESISTOR", {})
            msg = f"JSON config loaded successfully!\n"
            msg += f"BJT defaults: {len(bjt_limits)} parameters\n"
            msg += f"Resistor defaults: {len(res_limits)} parameters\n"
            msg += f"Overrides: {len(overrides)} devices"
            QtWidgets.QMessageBox.information(self, "Success", msg)

        self._update_analyze_button_state()
        return True

    # ---------------- ADS Simulation & Data ----------------
    def on_browse_workspace(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select ADS Workspace", self.state.workspace
        )
        if not directory:
            return
        self.state.workspace = directory
        self.edit_workspace.setText(directory)

    def on_run_simulation(self) -> None:
        """Run ADS transient simulation to generate .ds file (no conversion)."""
        from core.ads_sim import run_simulation_task

        workspace_path = self.edit_workspace.text().strip()

        # Design (cell) is provided from ADS and editable in the Design field
        design_name = self.edit_design.text().strip()

        [lib_name,cell_name,view_name] = design_name.split(":")


        if not workspace_path or not design_name:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Please specify Workspace and Design."
            )
            return

        self.state.workspace = workspace_path
        self.state.design_name = design_name
        self.state.lib_name = lib_name
        self.state.cell_name = cell_name
        self.state.view_name = view_name

        try:
            ds_path = run_simulation_task(workspace_path, design_name,cell_name)
        except Exception as e:
            # Log full traceback for diagnosis
            tb = traceback.format_exc()
            log_file = Path.cwd() / "ads_soa_gui_error.log"
            try:
                logger.exception("Simulation failed: %s", e)
            except Exception:
                # If logger not configured, write to fallback file
                try:
                    with open(log_file, "a", encoding="utf-8") as fh:
                        fh.write(f"\n{'='*60}\n")
                        fh.write(f"Error at {datetime.now().isoformat()}\n")
                        fh.write(f"{'='*60}\n")
                        fh.write(tb)
                except Exception:
                    pass  # If even logging fails, just show the error dialog

            # Show user-friendly error and advise to check logs
            QtWidgets.QMessageBox.critical(
                self,
                "Simulation Error",
                f"{e}\n\n详细 traceback 已写入日志。\n请查看: {log_file}",
            )
            return

        self.state.last_ds_path = ds_path
        self.lbl_status.setText(f"Simulation finished. Dataset: {ds_path}")

        # Auto chain: convert_ds -> load_csv -> load_json -> analyze
        if not self._convert_ds_from_path(ds_path, show_message=False):
            return
        if not self.state.defaults:
            default_json = Path.cwd() / "soa_limits_ex.json"
            if default_json.exists():
                self._load_json_from_path(str(default_json), show_message=False)
        if self.state.df is not None and self.state.defaults:
            self.refresh_devices_and_analysis()

        QtWidgets.QMessageBox.information(
            self, "Simulation Finished", f"Dataset saved at:\n{ds_path}\n\nConvert, load CSV/JSON and analyze completed."
        )

    def _convert_ds_from_path(self, ds_path: str, show_message: bool = True) -> bool:
        """Convert .ds at ds_path to CSV and load into GUI. Returns True on success."""
        from core.ads_sim import convert_ds_task

        try:
            csv_path = convert_ds_task(ds_path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Conversion Error", str(e))
            return False

        self.state.last_ds_path = ds_path
        self.lbl_status.setText(f"Converted dataset to CSV: {csv_path}")
        return self._load_csv_from_path(csv_path, show_message=show_message)

    def on_convert_ds(self) -> None:
        """Select a .ds file, convert to CSV and load it into the SOA GUI."""
        # Default directory: last ds location or workspace/data/{cell_name}.ds
        start_dir = ""
        if self.state.last_ds_path:
            start_dir = str(Path(self.state.last_ds_path).parent)
        elif self.state.workspace:
            start_dir = str(Path(self.state.workspace) / "data")

        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select ADS Dataset (.ds)",
            start_dir,
            "ADS Dataset (*.ds);;All Files (*)",
        )
        if not path:
            return

        self._convert_ds_from_path(path, show_message=True)

    def _update_analyze_button_state(self) -> None:
        """Enable Analyze button only if both CSV and JSON are loaded."""
        has_csv = self.state.df is not None
        has_json = bool(self.state.defaults)
        self.btn_analyze.setEnabled(has_csv and has_json)

    def on_analyze(self) -> None:
        """Manually trigger analysis after CSV and JSON are loaded."""
        if self.state.df is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please load CSV data first.")
            return
        if not self.state.defaults:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please load JSON config first.")
            return

        self.refresh_devices_and_analysis()

    def refresh_devices_and_analysis(self) -> None:
        if self.state.df is None:
            return

        try:
            bjt_devices, res_devices, time_col = scan_csv_columns(self.state.df, self.state.defaults, self.state.overrides)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to parse CSV headers:\n{e}")
            return

        self.state.bjt_devices = bjt_devices
        self.state.res_devices = res_devices
        self.state.time_col = time_col

        self.state.violations_df = analyze_all(self.state.df, self.state.bjt_devices, self.state.res_devices, self.state.time_col)

        self.populate_device_tree()
        self.populate_violation_table()

        self.lbl_status.setText(
            f"CSV: {len(self.state.df)} rows | BJTs: {len(bjt_devices)} | Resistors: {len(res_devices)} | Violations: {len(self.state.violations_df)}"
        )

        # Auto-select first device if available to show plots
        if bjt_devices:
            self._select_first_device()
        elif res_devices:
            self._select_first_device()

    def _select_first_device(self) -> None:
        """Auto-select the first device in the tree to show plots."""
        # Try BJTs first
        bjt_root = None
        res_root = None
        for i in range(self.tree_devices.topLevelItemCount()):
            item = self.tree_devices.topLevelItem(i)
            if item.text(0) == "BJTs":
                bjt_root = item
            elif item.text(0) == "Resistors":
                res_root = item
        
        # Select first BJT if available, otherwise first resistor
        if bjt_root and bjt_root.childCount() > 0:
            first_item = bjt_root.child(0)
            self.tree_devices.setCurrentItem(first_item)
            # PyQt6: selection API is on the item, not QTreeWidget
            first_item.setSelected(True)
            # Manually trigger plot update
            self.on_device_selected()
        elif res_root and res_root.childCount() > 0:
            first_item = res_root.child(0)
            self.tree_devices.setCurrentItem(first_item)
            first_item.setSelected(True)
            # Manually trigger plot update
            self.on_device_selected()

    # ---------------- Tree + table ----------------
    def populate_device_tree(self) -> None:
        self.tree_devices.clear()

        bjt_root = QtWidgets.QTreeWidgetItem(["BJTs"])
        res_root = QtWidgets.QTreeWidgetItem(["Resistors"])

        violated = violated_device_names(self.state.violations_df)

        for dev in self.state.bjt_devices:
            status = "FAIL" if dev.name in violated else "OK"
            item = QtWidgets.QTreeWidgetItem([dev.name, status])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, ("BJT", dev.name))
            bjt_root.addChild(item)

        for dev in self.state.res_devices:
            status = "FAIL" if dev.name in violated else "OK"
            item = QtWidgets.QTreeWidgetItem([dev.name, status])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, ("RES", dev.name))
            res_root.addChild(item)

        self.tree_devices.addTopLevelItem(bjt_root)
        self.tree_devices.addTopLevelItem(res_root)
        self.tree_devices.expandAll()

    def populate_violation_table(self) -> None:
        df = self.state.violations_df
        if df is None:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(list(df.columns))
        self.table.setRowCount(len(df))

        for row in range(len(df)):
            for col, col_name in enumerate(df.columns):
                val = str(df.iloc[row][col_name])
                item = QtWidgets.QTableWidgetItem(val)
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()

    # ---------------- Device selection and plots ----------------
    def on_device_selected(self) -> None:
        items = self.tree_devices.selectedItems()
        if not items:
            return
        item = items[0]
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not data:
            return
        dev_type, name = data
        if dev_type == "BJT":
            self.show_bjt_plots(name)
        elif dev_type == "RES":
            self.show_res_plots(name)

    def _find_bjt(self, name: str) -> Optional[BJTDevice]:
        for dev in self.state.bjt_devices:
            if dev.name == name:
                return dev
        return None

    def _find_res(self, name: str) -> Optional[ResistorDevice]:
        for dev in self.state.res_devices:
            if dev.name == name:
                return dev
        return None

    def show_bjt_plots(self, name: str) -> None:
        if self.state.df is None:
            return
        dev = self._find_bjt(name)
        if dev is None:
            return

        df = self.state.df
        t = df[self.state.time_col].to_numpy()
        vc = df[dev.col_vc].to_numpy()
        vb = df[dev.col_vb].to_numpy()
        ve = df[dev.col_ve].to_numpy()
        vce = vc - ve
        vbe = vb - ve

        ic = df[dev.col_ic].to_numpy() if dev.col_ic and dev.col_ic in df.columns else None
        ib = df[dev.col_ib].to_numpy() if dev.col_ib and dev.col_ib in df.columns else None

        # SOA trajectory: VCE vs IC
        self.canvas_soa.fig.clear()
        ax = self.canvas_soa.fig.add_subplot(111)
        ax.set_title(f"{name} BJT SOA")
        ax.set_xlabel("VCE (V)")
        ax.set_ylabel("IC (A)")

        if ic is not None and len(ic) > 0:
            # Make data clearly visible (size + zorder)
            ax.scatter(vce, ic, s=28, c="tab:blue", alpha=0.75, label="Data", zorder=3)
            # Mark violations if any
            if self.state.violations_df is not None:
                dev_violations = self.state.violations_df[
                    (self.state.violations_df["Device Name"] == name) & 
                    (self.state.violations_df["Parameter"].isin(["VCE", "IC"]))
                ]
                if not dev_violations.empty:
                    violation_indices = []
                    for _, row in dev_violations.iterrows():
                        time_val = row["Time"]
                        idx = np.argmin(np.abs(t - time_val))
                        violation_indices.append(idx)
                    if violation_indices:
                        vce_viol = vce[violation_indices]
                        ic_viol = ic[violation_indices]
                        ax.scatter(vce_viol, ic_viol, s=60, c="red", marker="x", label="Violations", zorder=5)
        else:
            # If no IC data, show VCE vs time-like index
            ax.scatter(vce, np.arange(len(vce)), s=5, c="blue", alpha=0.6, label="VCE only (no IC column)")
            ax.set_ylabel("Index")

        # Draw SOA limits rectangle
        if dev.limits.MAX_VCE and np.isfinite(dev.limits.MAX_VCE) and dev.limits.MAX_IC and np.isfinite(dev.limits.MAX_IC):
            max_vce = dev.limits.MAX_VCE
            max_ic = dev.limits.MAX_IC
            rect_x = [-max_vce, max_vce, max_vce, -max_vce, -max_vce]
            rect_y = [-max_ic, -max_ic, max_ic, max_ic, -max_ic]
            ax.plot(rect_x, rect_y, "r--", linewidth=2, label="SOA limits")

        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.margins(x=0.08, y=0.10)
        self.canvas_soa.fig.tight_layout()
        self.canvas_soa.draw()

        # --- V(t) ---
        self.canvas_v.fig.clear()
        axv = self.canvas_v.fig.add_subplot(111)
        axv.set_title(f"{name} Voltage (Time)")
        if len(t) > 0:
            axv.plot(t, vce, label="VCE", linewidth=1.8)
            axv.plot(t, vbe, label="VBE", linewidth=1.8)
        if dev.limits.MAX_VCE and np.isfinite(dev.limits.MAX_VCE):
            axv.axhline(dev.limits.MAX_VCE, color="r", linestyle="--", linewidth=1.5, label=f"VCE limit: ±{dev.limits.MAX_VCE}V")
            axv.axhline(-dev.limits.MAX_VCE, color="r", linestyle="--", linewidth=1.5)
        if dev.limits.MAX_VBE and np.isfinite(dev.limits.MAX_VBE):
            axv.axhline(dev.limits.MAX_VBE, color="g", linestyle="--", linewidth=1.5, label=f"VBE limit: ±{dev.limits.MAX_VBE}V")
            axv.axhline(-dev.limits.MAX_VBE, color="g", linestyle="--", linewidth=1.5)
        axv.set_xlabel("Time")
        axv.set_ylabel("V (V)")
        axv.grid(True, alpha=0.3)
        axv.legend()
        self.canvas_v.fig.tight_layout()
        self.canvas_v.draw()

        # --- I(t) ---
        self.canvas_i.fig.clear()
        axi = self.canvas_i.fig.add_subplot(111)
        axi.set_title(f"{name} Current (Time)")
        if ic is not None and len(ic) > 0:
            axi.plot(t, ic, label="IC", linewidth=1.8)
            if dev.limits.MAX_IC and np.isfinite(dev.limits.MAX_IC):
                axi.axhline(dev.limits.MAX_IC, color="r", linestyle="--", linewidth=1.5, label=f"IC limit: ±{dev.limits.MAX_IC}A")
                axi.axhline(-dev.limits.MAX_IC, color="r", linestyle="--", linewidth=1.5)
        if ib is not None and len(ib) > 0:
            axi.plot(t, ib, label="IB", linewidth=1.8)
            if dev.limits.MAX_IB and np.isfinite(dev.limits.MAX_IB):
                axi.axhline(dev.limits.MAX_IB, color="g", linestyle="--", linewidth=1.5, label=f"IB limit: ±{dev.limits.MAX_IB}A")
                axi.axhline(-dev.limits.MAX_IB, color="g", linestyle="--", linewidth=1.5)
        axi.set_xlabel("Time")
        axi.set_ylabel("I (A)")
        axi.grid(True, alpha=0.3)
        axi.legend()
        self.canvas_i.fig.tight_layout()
        self.canvas_i.draw()

        # --- P(t) ---
        self.canvas_p.fig.clear()
        axp = self.canvas_p.fig.add_subplot(111)
        axp.set_title(f"{name} Power (Time)")
        if ic is not None and ib is not None and len(ic) > 0 and len(ib) > 0:
            p = np.abs(vce * ic) + np.abs(vbe * ib)
            axp.plot(t, p, label="Power (W)", linewidth=1.8)
            if dev.limits.MAX_POWER and np.isfinite(dev.limits.MAX_POWER):
                axp.axhline(
                    dev.limits.MAX_POWER,
                    color="r",
                    linestyle="--",
                    linewidth=1.5,
                    label=f"Power limit: {dev.limits.MAX_POWER}W",
                )
        axp.set_xlabel("Time")
        axp.set_ylabel("Power (W)")
        axp.grid(True, alpha=0.3)
        axp.legend()
        self.canvas_p.fig.tight_layout()
        self.canvas_p.draw()

        # --- T(t) ---
        self.canvas_t.fig.clear()
        axt = self.canvas_t.fig.add_subplot(111)
        axt.set_title(f"{name} Temperature (Time)")
        temp = df[dev.col_temp].to_numpy() if dev.col_temp and dev.col_temp in df.columns else None
        if temp is not None and len(temp) > 0:
            axt.plot(t, temp, label="Temp (°C)", linewidth=1.8)
            if dev.limits.MAX_TEMP and np.isfinite(dev.limits.MAX_TEMP):
                axt.axhline(
                    dev.limits.MAX_TEMP,
                    color="g",
                    linestyle="--",
                    linewidth=1.5,
                    label=f"Temp limit: {dev.limits.MAX_TEMP}°C",
                )
        axt.set_xlabel("Time")
        axt.set_ylabel("Temp (°C)")
        axt.grid(True, alpha=0.3)
        axt.legend()
        self.canvas_t.fig.tight_layout()
        self.canvas_t.draw()

        # Default to BJT Results -> BJT SOA tab when selecting a BJT
        self.tabs.setCurrentWidget(self.tab_bjt_results)
        self.bjt_tabs.setCurrentWidget(self.tab_bjt_soa)

    def show_res_plots(self, name: str) -> None:
        if self.state.df is None:
            return
        dev = self._find_res(name)
        if dev is None:
            return

        df = self.state.df
        t = df[self.state.time_col].to_numpy()
        ir = df[dev.col_ir].to_numpy()

        self.canvas_res.fig.clear()
        ax = self.canvas_res.fig.add_subplot(111)
        ax.set_title(f"{name} Current")
        if len(t) > 0 and len(ir) > 0:
            ax.plot(t, ir, label="IR", linewidth=1.5)
        if dev.limits.MAX_RES_CURRENT and np.isfinite(dev.limits.MAX_RES_CURRENT):
            ax.axhline(dev.limits.MAX_RES_CURRENT, color="r", linestyle="--", linewidth=1.5, label=f"Imax: ±{dev.limits.MAX_RES_CURRENT}A")
            ax.axhline(-dev.limits.MAX_RES_CURRENT, color="r", linestyle="--", linewidth=1.5)
        ax.set_xlabel("Time")
        ax.set_ylabel("Current (A)")
        ax.grid(True, alpha=0.3)
        ax.legend()
        self.canvas_res.fig.tight_layout()
        self.canvas_res.draw()

        self.tabs.setCurrentWidget(self.tab_res)

    # ---------------- Export ----------------
    def on_export_csv(self) -> None:
        df = self.state.violations_df
        if df is None or df.empty:
            QtWidgets.QMessageBox.information(self, "Info", "No violations to export.")
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Violations CSV", "soa_violations_report.csv", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            df.to_csv(path, index=False)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save CSV:\n{e}")

