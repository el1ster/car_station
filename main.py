# main.py
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from login_window import LoginWindow
from config import STYLE_SHEET_PATH


def main():
    app = QApplication(sys.argv)

    try:
        # Завантаження стилів
        with open(STYLE_SHEET_PATH, "r") as f:
            style = f.read()
            app.setStyleSheet(style)

        win = LoginWindow()
        win.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Критична помилка", f"Сталася помилка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
