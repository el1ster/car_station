from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QMessageBox)
import mysql.connector
from config import DB_CONFIG


class CreateNewItemWindow(QDialog):
    def __init__(self, is_car=True):
        super().__init__()
        self.is_car = is_car
        try:
            self.initUI()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації: {e}")

    def initUI(self):
        try:
            self.setWindowTitle("Створення нового запису")
            self.setGeometry(100, 100, 400, 300)
            layout = QVBoxLayout()

            form_layout = QFormLayout()
            self.inputs = {}

            if self.is_car:
                fields = ["Марка", "Модель", "Рік", "ID Власника", "Номерний знак", "VIN"]
            else:
                fields = ["Ім'я", "Прізвище", "Телефон", "Email", "Логін",
                          "Пароль"]

            for field in fields:
                label = QLabel(field)
                line_edit = QLineEdit()
                line_edit.setObjectName(field)
                form_layout.addRow(label, line_edit)
                self.inputs[field] = line_edit

            layout.addLayout(form_layout)

            save_button = QPushButton("Зберегти")
            save_button.clicked.connect(self.saveData)
            layout.addWidget(save_button)

            self.setLayout(layout)
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації форми: {e}")

    def saveData(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            if self.is_car:
                query = """
                INSERT INTO Car (Make, Model, Year, OwnerID, LicensePlate, VIN) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                data = (
                    self.inputs["Марка"].text(),
                    self.inputs["Модель"].text(),
                    self.inputs["Рік"].text(),
                    self.inputs["ID Власника"].text(),
                    self.inputs["Номерний знак"].text(),
                    self.inputs["VIN"].text()
                )
            else:
                query = """
                INSERT INTO Client (Name, Surname, Phone, Email, Login, Password) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                data = (
                    self.inputs["Ім'я"].text(),
                    self.inputs["Прізвище"].text(),
                    self.inputs["Телефон"].text(),
                    self.inputs["Email"].text(),
                    self.inputs["Логін"].text(),
                    self.inputs["Пароль"].text()
                )

            cursor.execute(query, data)
            conn.commit()
            cursor.close()
            conn.close()

            QMessageBox.information(self, "Успіх", "Запис успішно створено")
            self.accept()
        except mysql.connector.Error as err:
            self.show_error_message(f"Помилка бази даних: {err}")
        except Exception as e:
            self.show_error_message(f"Невідома помилка: {e}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Помилка", message)
