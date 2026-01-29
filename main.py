def main() -> int:
    try:
        from PyQt6 import QtWidgets
    except ModuleNotFoundError as e:  # pragma: no cover
        raise SystemExit(
            "缺少依赖：PyQt6。\n"
            "请先安装依赖：\n"
            "  pip install -r requirements.txt\n"
        ) from e

    from gui.main_window import MainWindow

    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

