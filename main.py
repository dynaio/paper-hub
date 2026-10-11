#!/usr/bin/env python3
"""amayas — research paper companion. Entry point."""
import signal
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from amayas.mainwindow import MainWindow
from amayas import logo as logo_mod


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("amayas")
    app.setApplicationDisplayName("Amayas")
    app.setOrganizationName("amayas")

    # icon and .desktop sync
    try:
        logo_mod.install_bundled_logo()
        logo_mod.sync_desktop_icon()
        app.setWindowIcon(logo_mod.get_icon())
    except Exception:
        pass
    try:
        app.setDesktopFileName("amayas")
    except Exception:
        pass

    def _sigint(*_):
        app.quit()
    signal.signal(signal.SIGINT, _sigint)

    timer = QTimer(); timer.timeout.connect(lambda: None); timer.start(100)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
