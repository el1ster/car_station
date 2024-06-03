# login_window.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget
from user_window import UserWindow
from admin_window import AdminWindow
import mysql.connector
from config import DB_CONFIG


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система входу")
        self.setGeometry(100, 100, 280, 150)
        self.initUI()
        self.db_connection()

    def initUI(self):
        layout = QVBoxLayout()

        self.login_input = QLineEdit(self)
        self.login_input.setPlaceholderText("Login")
        layout.addWidget(self.login_input)

        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        layout.addWidget(self.password_input)

        self.user_button = QPushButton("Війти як користувач", self)
        self.user_button.clicked.connect(self.login_as_user)
        layout.addWidget(self.user_button)

        self.admin_button = QPushButton("Війти як адміністратор", self)
        self.admin_button.clicked.connect(self.login_as_admin)
        layout.addWidget(self.admin_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def db_connection(self):
        self.conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        self.cursor = self.conn.cursor()

    def login_as_user(self):
        login = self.login_input.text()
        password = self.password_input.text()
        login1 = "ivanlogin"
        password1 = "ivanpass"
        query = "SELECT * FROM Client WHERE Login = %s AND Password = %s"
        self.cursor.execute(query, (login, password))
        result = self.cursor.fetchone()
        if result:
            self.user_window = UserWindow(result)
            self.user_window.show()
        else:
            print("Невірний логін або пароль")

    def login_as_admin(self):
        login = self.login_input.text()
        password = self.password_input.text()
        query = "SELECT * FROM Admin WHERE Login = %s AND Password = %s"
        self.cursor.execute(query, (login, password))
        result = self.cursor.fetchone()
        if result:
            self.admin_window = AdminWindow(result)
            self.admin_window.show()
        else:
            print("Невірний логін або пароль")
