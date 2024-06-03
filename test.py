import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
import mysql.connector


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login System")
        self.setGeometry(100, 100, 280, 200)
        self.initUI()
        self.db_connection()

    def initUI(self):
        layout = QVBoxLayout()

        self.user_button = QPushButton("Війти як користувач", self)
        self.user_button.clicked.connect(self.login_as_user)
        layout.addWidget(self.user_button)

        self.admin_button = QPushButton("Війти як адміністратор", self)
        self.admin_button.clicked.connect(self.login_as_admin)
        layout.addWidget(self.admin_button)

        self.login_input = QLineEdit(self)
        self.login_input.setPlaceholderText("Login")
        layout.addWidget(self.login_input)

        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        layout.addWidget(self.password_input)

        self.status_label = QLabel("", self)
        layout.addWidget(self.status_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def db_connection(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            port=8772,
            user='root',
            password='Qwant_8772_5033',
            database='car_station'
        )
        self.cursor = self.conn.cursor()

    def login_as_user(self):
        login = self.login_input.text()
        password = self.password_input.text()
        query = "SELECT * FROM Client WHERE Login = %s AND Password = %s"
        self.cursor.execute(query, (login, password))
        result = self.cursor.fetchone()
        if result:
            self.status_label.setText(f"Вітаємо, {result[1]} {result[2]}!")
        else:
            self.status_label.setText("Невірний логін або пароль")

    def login_as_admin(self):
        login = self.login_input.text()
        password = self.password_input.text()
        query = "SELECT * FROM Admin WHERE Login = %s AND Password = %s"
        self.cursor.execute(query, (login, password))
        result = self.cursor.fetchone()
        if result:
            self.status_label.setText(f"Вітаємо, {result[2]}!")
        else:
            self.status_label.setText("Невірний логін або пароль")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())
