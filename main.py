"""ADS SOA GUI entrypoint.

Loads ADS simulation datasets in CSV format and performs SOA (Safe Operating Area) analysis.
"""
from typing import Optional
import sys
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
    from PyQt5 import QtWidgets, QtCore
except ModuleNotFoundError as e:  # pragma: no cover
    raise SystemExit(
        "缺少依赖：PyQt5。\n"
        "请先安装依赖：\n"
        "  pip install -r requirements.txt\n"
    ) from e

from gui.main_window import MainWindow


def main(argv: Optional[list] = None) -> int:
    if argv is None:
        argv = sys.argv

    app = QtWidgets.QApplication([])
    win = MainWindow()

    win.show()

    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        logger.exception("Unhandled exception in main executable")
        raise