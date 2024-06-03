from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget, QTabWidget,
                             QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import mysql.connector
from config import STYLE_SHEET_PATH, DB_CONFIG
from edit_window import EditWindow


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
                """
            elif self.search_type == "users":
                query = """
                SELECT ClientID, Name, Surname, Phone, Email 
                FROM Client 
                WHERE ClientID LIKE %s OR Name LIKE %s OR Surname LIKE %s 
                OR Phone LIKE %s OR Email LIKE %s OR Login LIKE %s
                """
            search_pattern = f"%{self.search_text}%"
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

            admin_info = QLabel(
                f"ФІО: {self.admin_data[5]}\nПосада: {self.admin_data[3]}\nРівень доступу: {self.admin_data[4]}", self)
            admin_info.setAlignment(Qt.AlignCenter)
            layout.addWidget(admin_info)

            if self.admin_data[6]:  # Assuming AdminPhoto is at index 6
                admin_photo = QLabel(self)
                pixmap = QPixmap(self.admin_data[6])
                admin_photo.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
                layout.addWidget(admin_photo)

            buttons_layout = QHBoxLayout()

            cars_button = QPushButton("Показати всі автомобілі")
            cars_button.clicked.connect(lambda: self.tabs.setCurrentWidget(self.cars_tab))
            buttons_layout.addWidget(cars_button)

            users_button = QPushButton("Показати всіх користувачів")
            users_button.clicked.connect(lambda: self.tabs.setCurrentWidget(self.users_tab))
            buttons_layout.addWidget(users_button)

            layout.addLayout(buttons_layout)
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації головної вкладки: {e}")

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
                "SELECT CarID, Make, Model, Year, OwnerID, LicensePlate, VIN, CarDetail FROM Car WHERE CarID = %s",
                (car_id,))
            car = cursor.fetchone()
            cursor.close()
            conn.close()

            if car:
                details = f"ID: {car[0]}\nМарка: {car[1]}\nМодель: {car[2]}\nРік: {car[3]}\nID Власника: {car[4]}\nНомерний знак: {car[5]}\nVIN: {car[6]}\nДеталі: {car[7]}"
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Детальна інформація про авто")
                msg_box.setText(details)
                edit_button = msg_box.addButton("Змінити дані", QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Ok)
                msg_box.exec_()

                if msg_box.clickedButton() == edit_button:
                    self.editCar(car)
            else:
                QMessageBox.warning(self, "Помилка", "Авто з таким ID не знайдено")
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")

    def editCar(self, car_data):
        try:
            edit_window = EditWindow(car_data, is_car=True)
            edit_window.exec_()
            self.loadCarsData()
            self.updateTable("cars")
        except Exception as e:
            self.show_error_message(f"Сталася помилка при редагуванні автомобіля: {e}")

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
                msg_box.addButton(QMessageBox.Ok)
                msg_box.exec_()

                if msg_box.clickedButton() == edit_button:
                    self.editClient(client)
            else:
                QMessageBox.warning(self, "Помилка", "Клієнт з таким ID не знайдено")
        except mysql.connector.Error as err:
            self.show_error_message(f"Сталася помилка з базою даних: {err}")
        except Exception as e:
            self.show_error_message(f"Сталася невідома помилка: {e}")

    def editClient(self, client_data):
        try:
            edit_window = EditWindow(client_data, is_car=False)
            edit_window.exec_()
            self.loadUsersData()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при редагуванні клієнта: {e}")

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
