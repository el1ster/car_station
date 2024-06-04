import os
from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget, QTabWidget,
                             QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QLineEdit, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import mysql.connector
from config import STYLE_SHEET_PATH, DB_CONFIG
from edit_window import EditWindow
from create_new_item import CreateNewItemWindow


class SearchThread(QThread):
    search_results = pyqtSignal(list)

    def __init__(self, search_text, search_type):
        super().__init__()
        self.search_text = search_text
        self.search_type = search_type

    def run(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            if self.search_type == "cars":
                query = """
                SELECT Car.CarID, Car.Make, Car.Model, Car.Year, Car.LicensePlate, 
                (SELECT Status FROM `Order` WHERE `Order`.Car = Car.CarID ORDER BY `Order`.OrderDate DESC LIMIT 1) AS Status
                FROM Car 
                WHERE Car.CarID LIKE %s OR Car.Make LIKE %s OR Car.Model LIKE %s 
                OR Car.Year LIKE %s OR Car.LicensePlate LIKE %s OR Car.VIN LIKE %s
                OR (SELECT Status FROM `Order` WHERE `Order`.Car = Car.CarID ORDER BY `Order`.OrderDate DESC LIMIT 1) LIKE %s
                """
            elif self.search_type == "users":
                query = """
                SELECT ClientID, Name, Surname, Phone, Email 
                FROM Client 
                WHERE ClientID LIKE %s OR Name LIKE %s OR Surname LIKE %s 
                OR Phone LIKE %s OR Email LIKE %s OR Login LIKE %s
                """
            search_pattern = f"%{self.search_text}%"
            if self.search_type == "cars":
                cursor.execute(query, (search_pattern, search_pattern, search_pattern,
                                       search_pattern, search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute(query, (search_pattern, search_pattern, search_pattern,
                                       search_pattern, search_pattern, search_pattern))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            self.search_results.emit(results)
        except mysql.connector.Error as err:
            self.search_results.emit([])
        except Exception as e:
            self.search_results.emit([])


class CarDetailsWindow(QMainWindow):
    def __init__(self, car_data, parent, access_level):
        super().__init__()
        self.car_data = car_data
        self.parent = parent
        self.access_level = access_level
        self.setWindowTitle(f"Детальна інформація про авто: {car_data[1]} {car_data[2]}")
        self.setGeometry(200, 200, 400, 500)
        try:
            self.initUI()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації: {e}")

    def initUI(self):
        try:
            layout = QVBoxLayout()

            car_info_label = QLabel(
                f"ID: {self.car_data[0]}\nМарка: {self.car_data[1]}\nМодель: {self.car_data[2]}\nРік: {self.car_data[3]}\n"
                f"ID Власника: {self.car_data[4]}\nНомерний знак: {self.car_data[5]}\nVIN: {self.car_data[6]}"
            )
            layout.addWidget(car_info_label)

            car_photo_label = QLabel()
            car_photo_path = f"car_photos/{self.car_data[0]}.jpg"
            if os.path.exists(car_photo_path):
                car_pixmap = QPixmap(car_photo_path)
                car_photo_label.setPixmap(car_pixmap.scaled(300, 300, Qt.KeepAspectRatio))
            else:
                car_photo_label.setText("Немає фото")
            layout.addWidget(car_photo_label)

            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT Status FROM `Order` WHERE Car = %s ORDER BY OrderDate DESC LIMIT 1",
                           (self.car_data[0],))
            order_status = cursor.fetchone()
            status_label = QLabel(f"Статус: {order_status[0]}" if order_status else "Статус: Немає даних")
            layout.addWidget(status_label)

            cursor.execute("""
                SELECT Service.ServiceName, Service.Description, Service.Cost, OrderService.Quantity 
                FROM OrderService 
                JOIN Service ON OrderService.Service = Service.ServiceID 
                WHERE OrderService.`Order` = (
                    SELECT OrderID FROM `Order` WHERE Car = %s ORDER BY OrderDate DESC LIMIT 1
                )
            """, (self.car_data[0],))
            services = cursor.fetchall()
            cursor.close()
            conn.close()

            service_details = "\n\n".join(
                [f"Послуга: {s[0]}\nОпис: {s[1]}\nЦіна: {s[2]}\nКількість: {s[3]}" for s in services])
            if not service_details:
                service_details = "Немає послуг"
            total_cost = sum(s[2] * s[3] for s in services)

            details = f"{service_details}\n\nЗагальна сума послуг: {total_cost} грн"
            services_label = QLabel(details)
            layout.addWidget(services_label)

            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)

            buttons_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(self.close)
            buttons_layout.addWidget(ok_button)

            if self.access_level in [2, 3]:
                edit_button = QPushButton("Змінити дані")
                edit_button.clicked.connect(self.edit_car)
                buttons_layout.addWidget(edit_button)

                delete_button = QPushButton("Видалити")
                delete_button.clicked.connect(self.delete_car)
                buttons_layout.addWidget(delete_button)

            layout.addLayout(buttons_layout)
        except Exception as e:
            self.show_error_message(f"Сталася помилка при завантаженні даних: {e}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Помилка", message)

    def edit_car(self):
        try:
            edit_window = EditWindow(self.car_data, is_car=True)
            edit_window.exec_()
            self.close()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при редагуванні автомобіля: {e}")

    def delete_car(self):
        try:
            confirm = QMessageBox.question(self, 'Підтвердження', 'Ви впевнені, що хочете видалити це авто?',
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.parent.deleteCar(self.car_data[0])
                self.close()
        except mysql.connector.Error as err:
            self.show_error_message(f"Помилка бази даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")


class AdminWindow(QMainWindow):
    def __init__(self, admin_data):
        super().__init__()
        self.admin_data = admin_data
        self.setWindowTitle(f"Адмін: {admin_data[1]} ({admin_data[3]})")
        self.setGeometry(100, 100, 800, 600)
        try:
            self.initUI()
            self.applyStyleSheet()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації: {e}")

    def initUI(self):
        try:
            self.tabs = QTabWidget(self)
            self.setCentralWidget(self.tabs)

            self.main_tab = QWidget()
            self.cars_tab = QWidget()
            self.users_tab = QWidget()

            self.tabs.addTab(self.main_tab, "Головна")
            self.tabs.addTab(self.cars_tab, "Автомобілі")
            self.tabs.addTab(self.users_tab, "Користувачі")

            self.initMainTab()
            self.initCarsTab()
            self.initUsersTab()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації вкладок: {e}")

    def initMainTab(self):
        try:
            layout = QVBoxLayout(self.main_tab)

            self.admin_info = QLabel(
                f"ID: {self.admin_data[0]}\nФІО: {self.admin_data[5]}\nПосада: {self.admin_data[3]}\nРівень доступу: {self.admin_data[4]}",
                self)
            self.admin_info.setAlignment(Qt.AlignCenter)
            self.admin_info.setStyleSheet("font-size: 16px;")
            layout.addWidget(self.admin_info)

            self.admin_photo = QLabel(self)
            if self.admin_data[6]:  # Assuming AdminPhoto is at index 6
                pixmap = QPixmap(self.admin_data[6])
                self.admin_photo.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))
            else:
                self.admin_photo.setText("Немає фото")
            self.admin_photo.setAlignment(Qt.AlignCenter)  # Центровка фото
            layout.addWidget(self.admin_photo)

            # Кнопка изменения фото
            change_photo_button = QPushButton("Змінити фото")
            change_photo_button.clicked.connect(self.changePhoto)
            layout.addWidget(change_photo_button)

            buttons_layout = QVBoxLayout()

            cars_button = QPushButton("Показати всі автомобілі")
            cars_button.clicked.connect(lambda: self.tabs.setCurrentWidget(self.cars_tab))
            buttons_layout.addWidget(cars_button)

            users_button = QPushButton("Показати всіх користувачів")
            users_button.clicked.connect(lambda: self.tabs.setCurrentWidget(self.users_tab))
            buttons_layout.addWidget(users_button)

            new_car_button = QPushButton("Додати нову машину")
            new_car_button.clicked.connect(self.createNewCar)
            buttons_layout.addWidget(new_car_button)

            new_user_button = QPushButton("Додати нового користувача")
            new_user_button.clicked.connect(self.createNewUser)
            buttons_layout.addWidget(new_user_button)

            layout.addLayout(buttons_layout)
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації головної вкладки: {e}")

    def changePhoto(self):
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(self, "Виберіть фото", "", "Images (*.png *.xpm *.jpg)",
                                                       options=options)
            if file_name:
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                query = "UPDATE Admin SET AdminPhoto = %s WHERE AdminID = %s"
                cursor.execute(query, (file_name, self.admin_data[0]))
                conn.commit()
                cursor.close()
                conn.close()

                QMessageBox.information(self, "Успіх", "Фото успішно змінено")

                # Обновление фото в UI
                pixmap = QPixmap(file_name)
                self.admin_photo.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
        except Exception as e:
            self.show_error_message(f"Сталася помилка при зміні фото: {e}")

    def createNewCar(self):
        if self.admin_data[4] in [2, 3]:
            try:
                create_window = CreateNewItemWindow(is_car=True)
                create_window.exec_()
                self.loadCarsData()
            except Exception as e:
                self.show_error_message(f"Сталася помилка при створенні нової машини: {e}")
        else:
            self.show_error_message("У вас немає прав на створення нових машин.")

    def createNewUser(self):
        if self.admin_data[4] in [1, 3]:
            try:
                create_window = CreateNewItemWindow(is_car=False)
                create_window.exec_()
                self.loadUsersData()
            except Exception as e:
                self.show_error_message(f"Сталася помилка при створенні нового користувача: {e}")
        else:
            self.show_error_message("У вас немає прав на створення нових користувачів.")

    def initCarsTab(self):
        try:
            layout = QVBoxLayout(self.cars_tab)
            search_layout = QHBoxLayout()

            self.car_search_input = QLineEdit()
            self.car_search_input.setPlaceholderText("Пошук авто за параметрами...")
            self.car_search_input.textChanged.connect(self.scheduleSearch)
            search_layout.addWidget(self.car_search_input)

            self.car_id_input = QLineEdit()
            self.car_id_input.setPlaceholderText("Введіть ID авто")
            search_button = QPushButton("Пошук авто")
            search_button.clicked.connect(self.searchCar)

            search_layout.addWidget(self.car_id_input)
            search_layout.addWidget(search_button)

            layout.addLayout(search_layout)

            self.cars_table = QTableWidget()
            layout.addWidget(self.cars_table)

            self.loadCarsData()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації вкладки автомобілів: {e}")

    def scheduleSearch(self):
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.performSearch)
        self.search_timer.start(300)

    def performSearch(self):
        search_text = self.car_search_input.text()
        self.search_thread = SearchThread(search_text, "cars")
        self.search_thread.search_results.connect(self.updateCarsTable)
        self.search_thread.start()

    def updateCarsTable(self, cars):
        self.cars_table.setRowCount(len(cars))
        self.cars_table.setColumnCount(6)
        self.cars_table.setHorizontalHeaderLabels(["CarID", "Make", "Model", "Year", "LicensePlate", "Status"])

        for row_num, row_data in enumerate(cars):
            for col_num, data in enumerate(row_data):
                self.cars_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))

    def loadCarsData(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT Car.CarID, Car.Make, Car.Model, Car.Year, Car.LicensePlate, 
            (SELECT Status FROM `Order` WHERE `Order`.Car = Car.CarID ORDER BY `Order`.OrderDate DESC LIMIT 1) AS Status
            FROM Car
            """)
            cars = cursor.fetchall()
            cursor.close()
            conn.close()

            self.updateCarsTable(cars)
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")

    def initUsersTab(self):
        try:
            layout = QVBoxLayout(self.users_tab)
            search_layout = QHBoxLayout()

            self.user_search_input = QLineEdit()
            self.user_search_input.setPlaceholderText("Пошук користувачів за параметрами...")
            self.user_search_input.textChanged.connect(self.scheduleUserSearch)
            search_layout.addWidget(self.user_search_input)

            self.client_id_input = QLineEdit()
            self.client_id_input.setPlaceholderText("Введіть ID клієнта")
            search_button = QPushButton("Пошук клієнта")
            search_button.clicked.connect(self.searchClient)

            search_layout.addWidget(self.client_id_input)
            search_layout.addWidget(search_button)

            layout.addLayout(search_layout)

            self.users_table = QTableWidget()
            layout.addWidget(self.users_table)

            self.loadUsersData()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації вкладки користувачів: {e}")

    def scheduleUserSearch(self):
        self.user_search_timer = QTimer()
        self.user_search_timer.setSingleShot(True)
        self.user_search_timer.timeout.connect(self.performUserSearch)
        self.user_search_timer.start(300)

    def performUserSearch(self):
        search_text = self.user_search_input.text()
        self.user_search_thread = SearchThread(search_text, "users")
        self.user_search_thread.search_results.connect(self.updateUsersTable)
        self.user_search_thread.start()

    def updateUsersTable(self, users):
        self.users_table.setRowCount(len(users))
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["ClientID", "Name", "Surname", "Phone", "Email"])

        for row_num, row_data in enumerate(users):
            for col_num, data in enumerate(row_data):
                self.users_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))

    def loadUsersData(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT ClientID, Name, Surname, Phone, Email FROM Client")
            users = cursor.fetchall()
            cursor.close()
            conn.close()

            self.updateUsersTable(users)
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")

    def searchCar(self):
        try:
            car_id = self.car_id_input.text()
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT CarID, Make, Model, Year, OwnerID, LicensePlate, VIN FROM Car WHERE CarID = %s",
                (car_id,))
            car = cursor.fetchone()

            if car:
                # Получение списка услуг для автомобиля
                cursor.execute("""
                    SELECT Service.ServiceName, Service.Description, Service.Cost, OrderService.Quantity 
                    FROM OrderService 
                    JOIN Service ON OrderService.Service = Service.ServiceID 
                    WHERE OrderService.`Order` = (
                        SELECT OrderID FROM `Order` WHERE Car = %s ORDER BY OrderDate DESC LIMIT 1
                    )
                """, (car[0],))
                services = cursor.fetchall()

                # Подсчет общей стоимости услуг
                total_cost = sum(s[2] * s[3] for s in services)

                cursor.close()
                conn.close()

                service_details = "\n\n".join(
                    [f"Послуга: {s[0]}\nОпис: {s[1]}\nЦіна: {s[2]}\nКількість: {s[3]}" for s in services])
                if not service_details:
                    service_details = "Немає послуг"

                details = f"ID: {car[0]}\nМарка: {car[1]}\nМодель: {car[2]}\nРік: {car[3]}\nID Власника: {car[4]}\nНомерний знак: {car[5]}\nVIN: {car[6]}\n\nПослуги:\n{service_details}\n\nЗагальна сума послуг: {total_cost} грн"
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Детальна інформація про авто")
                msg_box.setText(details)
                delete_button = msg_box.addButton("Видалити", QMessageBox.ActionRole)
                edit_button = msg_box.addButton("Змінити дані", QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Ok)
                msg_box.exec_()

                if msg_box.clickedButton() == edit_button:
                    self.editCar(car)
                elif msg_box.clickedButton() == delete_button:
                    self.deleteCar(car[0])
            else:
                cursor.close()
                conn.close()
                QMessageBox.warning(self, "Помилка", "Авто з таким ID не знайдено")
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")

    def deleteCar(self, car_id):
        if self.admin_data[4] in [2, 3]:
            try:
                confirm = QMessageBox.question(self, 'Підтвердження',
                                               'Ви впевнені, що хочете видалити це авто та всі пов\'язані з ним дані?',
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if confirm == QMessageBox.Yes:
                    conn = mysql.connector.connect(**DB_CONFIG)
                    cursor = conn.cursor()

                    # Видалити пов'язані записи з таблиці orderservice
                    cursor.execute(
                        "DELETE FROM orderservice WHERE `Order` IN (SELECT OrderID FROM `order` WHERE Car = %s)",
                        (car_id,))

                    # Видалити пов'язані записи з таблиці order
                    cursor.execute("DELETE FROM `order` WHERE Car = %s", (car_id,))

                    # Видалити автомобіль з таблиці car
                    cursor.execute("DELETE FROM car WHERE CarID = %s", (car_id,))

                    conn.commit()
                    cursor.close()
                    conn.close()

                    QMessageBox.information(self, "Успіх", "Автомобіль успішно видалено")
                    self.loadCarsData()
            except mysql.connector.Error as err:
                self.show_error_message(f"Помилка бази даних: {err}")
            except Exception as e:
                self.show_error_message(f"Невідома помилка: {e}")
        else:
            self.show_error_message("У вас немає прав на видалення автомобілів.")

    def editCar(self, car_data):
        if self.admin_data[4] in [2, 3]:
            try:
                edit_window = EditWindow(car_data, is_car=True)
                edit_window.exec_()
                self.loadCarsData()
                self.updateTable("cars")
            except Exception as e:
                self.show_error_message(f"Сталася помилка при редагуванні автомобіля: {e}")
        else:
            self.show_error_message("У вас немає прав на редагування автомобілів.")

    def searchClient(self):
        try:
            client_id = self.client_id_input.text()
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ClientID, Name, Surname, Phone, Email, Login, ClientPhoto, (SELECT COUNT(*) FROM Car WHERE OwnerID = Client.ClientID) as CarCount FROM Client WHERE ClientID = %s",
                (client_id,))
            client = cursor.fetchone()
            cursor.close()
            conn.close()

            if client:
                details = f"ID Користувача: {client[0]}\nІм'я: {client[1]}\nПрізвище: {client[2]}\nТелефон: {client[3]}\nEmail: {client[4]}\nЛогін: {client[5]}\nКількість авто: {client[7]}"
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Детальна інформація про клієнта")
                msg_box.setText(details)
                edit_button = msg_box.addButton("Змінити дані", QMessageBox.ActionRole)
                delete_button = msg_box.addButton("Видалити", QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Ok)
                msg_box.exec_()

                if msg_box.clickedButton() == edit_button:
                    self.editClient(client)
                elif msg_box.clickedButton() == delete_button:
                    self.deleteClient(client[0])
            else:
                QMessageBox.warning(self, "Помилка", "Клієнт з таким ID не знайдено")
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")

    def deleteClient(self, client_id):
        if self.admin_data[4] in [1, 3]:
            try:
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("SELECT CarID, Make, Model FROM Car WHERE OwnerID = %s", (client_id,))
                cars = cursor.fetchall()
                car_list = "\n".join([f"ID: {car[0]}, Марка: {car[1]}, Модель: {car[2]}" for car in cars])

                confirm_text = f"Ви впевнені, що хочете видалити цього клієнта та всі його автомобілі?\n\n{car_list}"
                confirm = QMessageBox.question(self, 'Підтвердження', confirm_text,
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if confirm == QMessageBox.Yes:
                    # Видалити пов'язані автомобілі та їхні записи
                    for car in cars:
                        self.deleteCar(car[0])

                    # Видалити клієнта
                    cursor.execute("DELETE FROM Client WHERE ClientID = %s", (client_id,))

                    conn.commit()
                    cursor.close()
                    conn.close()

                    QMessageBox.information(self, "Успіх", "Клієнта та всі його автомобілі успішно видалено")
                    self.loadUsersData()
            except mysql.connector.Error as err:
                self.show_error_message(f"Помилка бази даних: {err}")
            except Exception as e:
                self.show_error_message(f"Невідома помилка: {e}")
        else:
            self.show_error_message("У вас немає прав на видалення клієнтів.")

    def editClient(self, client_data):
        if self.admin_data[4] in [1, 3]:
            try:
                edit_window = EditWindow(client_data, is_car=False)
                edit_window.exec_()
                self.loadUsersData()
                self.updateTable("user")
            except Exception as e:
                self.show_error_message(f"Сталася помилка при редагуванні клієнта: {e}")
        else:
            self.show_error_message("У вас немає прав на редагування клієнтів.")

    def applyStyleSheet(self):
        try:
            with open(STYLE_SHEET_PATH, "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            self.show_error_message(f"Сталася помилка при завантаженні стилів: {e}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Помилка", message)

    def updateTable(self, table_type):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            if table_type == "cars":
                self.cars_table.clearContents()
                cursor.execute("""
                SELECT Car.CarID, Car.Make, Car.Model, Car.Year, Car.LicensePlate, 
                (SELECT Status FROM `Order` WHERE `Order`.Car = Car.CarID ORDER BY `Order`.OrderDate DESC LIMIT 1) AS Status
                FROM Car
                """)
                cars = cursor.fetchall()
                self.cars_table.setRowCount(len(cars))
                for row_num, row_data in enumerate(cars):
                    for col_num, data in enumerate(row_data):
                        self.cars_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))
            elif table_type == "users":
                self.users_table.clearContents()
                cursor.execute("SELECT ClientID, Name, Surname, Phone, Email FROM Client")
                users = cursor.fetchall()
                self.users_table.setRowCount(len(users))
                for row_num, row_data in enumerate(users):
                    for col_num, data in enumerate(row_data):
                        self.users_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))

            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")
