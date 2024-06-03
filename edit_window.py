from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QTextEdit, QMessageBox,
                             QComboBox)
import mysql.connector
from config import DB_CONFIG


class EditWindow(QDialog):
    def __init__(self, data, is_car=True):
        super().__init__()
        self.data = data
        self.is_car = is_car
        try:
            self.initUI()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації: {e}")

    def initUI(self):
        try:
            self.setWindowTitle("Редагування даних")
            self.setGeometry(100, 100, 400, 400)  # Увеличение размера окна
            layout = QVBoxLayout()

            form_layout = QFormLayout()
            self.inputs = []

            if self.is_car:
                fields = ["CarID", "Make", "Model", "Year", "OwnerID", "LicensePlate", "VIN"]
                for i, field in enumerate(fields):
                    label = QLabel(field)
                    line_edit = QLineEdit(str(self.data[i]))
                    line_edit.setObjectName(field)
                    form_layout.addRow(label, line_edit)
                    self.inputs.append(line_edit)

                # Добавление выпадающего списка для статуса
                self.status_combo = QComboBox()
                self.status_combo.addItems(["В очікуванні", "У процесі", "Завершено"])
                form_layout.addRow(QLabel("Статус"), self.status_combo)

                # Загрузка текущего статуса из таблицы Order
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("SELECT Status FROM `Order` WHERE Car = %s ORDER BY OrderDate DESC LIMIT 1", (self.data[0],))
                current_status = cursor.fetchone()
                cursor.close()
                conn.close()
                if current_status:
                    index = self.status_combo.findText(current_status[0])
                    if index != -1:
                        self.status_combo.setCurrentIndex(index)

            else:
                fields = ["ClientID", "Name", "Surname", "Phone", "Email", "Login", "ClientPhoto"]
                for i, field in enumerate(fields):
                    label = QLabel(field)
                    line_edit = QLineEdit(str(self.data[i]))
                    line_edit.setObjectName(field)
                    form_layout.addRow(label, line_edit)
                    self.inputs.append(line_edit)

            layout.addLayout(form_layout)

            save_button = QPushButton("Зберегти")
            save_button.clicked.connect(self.saveData)
            layout.addWidget(save_button)

            self.setLayout(layout)
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації форми: {e}")

    def saveData(self):
        try:
            updated_data = []
            for input in self.inputs:
                updated_data.append(input.text())

            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            if self.is_car:
                query = """
                UPDATE Car SET Make = %s, Model = %s, Year = %s, OwnerID = %s, LicensePlate = %s, VIN = %s
                WHERE CarID = %s
                """
                cursor.execute(query, (
                    updated_data[1], updated_data[2], int(updated_data[3]), int(updated_data[4]), updated_data[5],
                    updated_data[6], int(updated_data[0])))

                # Обновление статуса в таблице Order
                status = self.status_combo.currentText()
                query = """
                UPDATE `Order` SET Status = %s WHERE Car = %s ORDER BY OrderDate DESC LIMIT 1
                """
                cursor.execute(query, (status, int(updated_data[0])))

            else:
                query = """
                UPDATE Client SET Name = %s, Surname = %s, Phone = %s, Email = %s, Login = %s, ClientPhoto = %s
                WHERE ClientID = %s
                """
                cursor.execute(query, (
                    updated_data[1], updated_data[2], updated_data[3], updated_data[4], updated_data[5],
                    updated_data[6], int(updated_data[0])))

            conn.commit()
            cursor.close()
            conn.close()

            QMessageBox.information(self, "Успіх", "Дані успішно оновлено")
            self.accept()
        except ValueError as ve:
            self.show_error_message(f"Помилка конвертації даних: {ve}")
        except mysql.connector.Error as err:
            self.show_error_message(f"Помилка бази даних: {err}")
        except Exception as e:
            self.show_error_message(f"Невідома помилка: {e}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Помилка", message)
