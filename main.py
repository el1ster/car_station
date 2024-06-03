# main.py
import sys
from PyQt5.QtWidgets import QApplication
from login_window import LoginWindow
from config import STYLE_SHEET_PATH


def main():
    app = QApplication(sys.argv)

    # Завантаження стилів
    with open(STYLE_SHEET_PATH, "r") as f:
        style = f.read()
        app.setStyleSheet(style)

    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
