from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QTextEdit, QMessageBox,
                             QComboBox, QCheckBox, QHBoxLayout)
import mysql.connector
from config import DB_CONFIG


class EditWindow(QDialog):
    def __init__(self, data, is_car=True):
        super().__init__()
        self.data = data
        self.is_car = is_car
        self.service_checkboxes = []
        try:
            self.initUI()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації: {e}")

    def initUI(self):
        try:
            self.setWindowTitle("Редагування даних")
            self.setGeometry(100, 100, 400, 600)
            layout = QVBoxLayout()

            form_layout = QFormLayout()
            self.inputs = []

            if self.is_car:
                fields = ["ID Авто", "Марка", "Модель", "Рік", "ID Власника", "Номерний знак", "VIN"]
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
                cursor.execute("SELECT Status FROM `Order` WHERE Car = %s ORDER BY OrderDate DESC LIMIT 1",
                               (self.data[0],))
                current_status = cursor.fetchone()
                cursor.close()
                conn.close()
                if current_status:
                    index = self.status_combo.findText(current_status[0])
                    if index != -1:
                        self.status_combo.setCurrentIndex(index)

                # Загрузка текущих услуг из таблицы OrderService
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT Service FROM OrderService WHERE `Order` = (SELECT OrderID FROM `Order` WHERE Car = %s ORDER BY OrderDate DESC LIMIT 1)",
                    (self.data[0],))
                current_services = cursor.fetchall()
                current_services = [service[0] for service in current_services]

                # Загрузка всех услуг из таблицы Service
                cursor.execute("SELECT ServiceID, ServiceName FROM Service")
                all_services = cursor.fetchall()
                cursor.close()
                conn.close()

                layout.addLayout(form_layout)

                services_layout = QVBoxLayout()
                services_layout.addWidget(QLabel("Виберіть послуги:"))

                for service_id, service_name in all_services:
                    checkbox = QCheckBox(service_name)
                    if service_id in current_services:
                        checkbox.setChecked(True)
                    self.service_checkboxes.append((service_id, checkbox))
                    services_layout.addWidget(checkbox)

                layout.addLayout(services_layout)

            else:
                fields = ["ID Кліента", "Ім'я", "Прізвище", "Телефон", "Email", "Логін"]
                for i, field in enumerate(fields):
                    label = QLabel(field)
                    line_edit = QLineEdit(str(self.data[i]))
                    line_edit.setObjectName(field)
                    form_layout.addRow(label, line_edit)
                    self.inputs.append(line_edit)

                # Добавление поля для пароля
                password_label = QLabel("Новий пароль")
                self.password_input = QLineEdit()
                self.password_input.setEchoMode(QLineEdit.Password)
                form_layout.addRow(password_label, self.password_input)

                # Добавление поля для текущего пароля
                current_password_label = QLabel("Поточний пароль")
                self.current_password_input = QLineEdit()
                self.current_password_input.setEchoMode(QLineEdit.Password)
                form_layout.addRow(current_password_label, self.current_password_input)

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

                # Обновление услуг в таблице OrderService
                query = "SELECT OrderID FROM `Order` WHERE Car = %s ORDER BY OrderDate DESC LIMIT 1"
                cursor.execute(query, (updated_data[0],))
                order_id = cursor.fetchone()[0]

                cursor.execute("DELETE FROM OrderService WHERE `Order` = %s", (order_id,))
                for service_id, checkbox in self.service_checkboxes:
                    if checkbox.isChecked():
                        cursor.execute("INSERT INTO OrderService (`Order`, Service, Quantity) VALUES (%s, %s, %s)",
                                       (order_id, service_id, 1))

            else:
                query = """
                UPDATE Client SET Name = %s, Surname = %s, Phone = %s, Email = %s, Login = %s
                WHERE ClientID = %s
                """
                cursor.execute(query, (
                    updated_data[1], updated_data[2], updated_data[3], updated_data[4], updated_data[5],
                    int(updated_data[0])))

                # Обновление пароля, если введен
                if self.password_input.text():
                    # Проверка текущего пароля
                    query = "SELECT Password FROM Client WHERE ClientID = %s"
                    cursor.execute(query, (int(updated_data[0]),))
                    current_password = cursor.fetchone()[0]

                    if self.current_password_input.text() == current_password:
                        query = "UPDATE Client SET Password = %s WHERE ClientID = %s"
                        cursor.execute(query, (self.password_input.text(), int(updated_data[0])))
                    else:
                        raise ValueError("Поточний пароль неправильний")

            conn.commit()
            cursor.close()
            conn.close()

            QMessageBox.information(self, "Успіх", "Дані успішно оновлено")
            self.accept()
        except ValueError as ve:
            self.show_error_message(f"Помилка: {ve}")
        except mysql.connector.Error as err:
            self.show_error_message(f"Помилка бази даних: {err}")
        except Exception as e:
            self.show_error_message(f"Невідома помилка: {e}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Помилка", message)
