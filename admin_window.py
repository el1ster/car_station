# admin_window.py
from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from config import STYLE_SHEET_PATH


class AdminWindow(QMainWindow):
    def __init__(self, admin_data):
        super().__init__()
        self.setWindowTitle("Адміністратор")
        self.setGeometry(100, 100, 320, 180)
        self.initUI(admin_data)
        self.applyStyleSheet()

    def initUI(self, admin_data):
        layout = QVBoxLayout()
        info_label = QLabel(f"Вітаємо, {admin_data[3]}!", self)
        info_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(info_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def applyStyleSheet(self):
        with open(STYLE_SHEET_PATH, "r") as f:
            style = f.read()
            self.setStyleSheet(style)
