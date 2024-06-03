import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget, QMessageBox
from user_window import UserWindow
from admin_window import AdminWindow
import mysql.connector
from config import DB_CONFIG


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система входу")
        self.setGeometry(100, 100, 280, 150)
        try:
            self.initUI()
            self.db_connection()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації: {e}")

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
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")

    def login_as_user(self):
        try:
            login = self.login_input.text()
            password = self.password_input.text()
            loginU = "ivanlogin"
            passwordU = "ivanpass"
            query = "SELECT * FROM Client WHERE Login = %s AND Password = %s"
            self.cursor.execute(query, (login, password))
            result = self.cursor.fetchone()
            if result:
                self.user_window = UserWindow(result)
                self.user_window.show()
            else:
                self.show_error_message("Невірний логін або пароль")
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")

    def login_as_admin(self):
        try:
            login = self.login_input.text()
            password = self.password_input.text()
            loginA = "adminSales"
            passwordA = "sales123"
            query = "SELECT * FROM Admin WHERE Login = %s AND Password = %s"
            self.cursor.execute(query, (loginA, passwordA))
            result = self.cursor.fetchone()
            if result:
                self.admin_window = AdminWindow(result)
                self.admin_window.show()
            else:
                self.show_error_message("Невірний логін або пароль")
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Помилка", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())
