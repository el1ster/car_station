from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget, QTabWidget,
                             QScrollArea, QHBoxLayout, QFrame, QPushButton, QFileDialog, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import os
import shutil
import mysql.connector
from config import STYLE_SHEET_PATH, DB_CONFIG


class CarDetailsWindow(QMainWindow):
    def __init__(self, car_data):
        super().__init__()
        self.car_data = car_data
        self.setWindowTitle(f"Детальна інформація про авто: {car_data[1]} {car_data[2]}")
        self.setGeometry(200, 200, 600, 900)
        try:
            self.initUI()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації: {e}")

    def initUI(self):
        try:
            layout = QVBoxLayout()

            car_info_label = QLabel(
                f"Марка: {self.car_data[1]}\nМодель: {self.car_data[2]}\nРік: {self.car_data[3]}\n"
                f"Номерний знак: {self.car_data[4]}\nVIN: {self.car_data[6]}"
            )
            layout.addWidget(car_info_label)

            car_photo_label = QLabel()
            car_photo_path = os.path.join('car_photos', f'Car_{self.car_data[0]}.jpg')
            if os.path.exists(car_photo_path):
                car_pixmap = QPixmap(car_photo_path)
                car_photo_label.setPixmap(car_pixmap.scaled(400, 400, Qt.KeepAspectRatio))
            else:
                car_photo_label.setText("Немає фото")
            layout.addWidget(car_photo_label)

            # Поле для отображения описания
            detail_label = QTextEdit(self)
            detail_label.setReadOnly(True)
            layout.addWidget(QLabel("Опис ремонту:"))
            layout.addWidget(detail_label)

            # Добавление статуса из таблицы Order
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT Status FROM `Order` WHERE Car = %s ORDER BY OrderDate DESC LIMIT 1",
                           (self.car_data[0],))
            order_status = cursor.fetchone()
            status_label = QLabel(f"Статус: {order_status[0]}" if order_status else "Статус: Немає даних")
            layout.addWidget(status_label)

            # Получение услуг и их стоимости
            cursor.execute("""
                SELECT s.ServiceName, s.Description, s.Cost 
                FROM orderservice os
                JOIN service s ON os.Service = s.ServiceID
                JOIN `Order` o ON os.Order = o.OrderID
                WHERE o.Car = %s
            """, (self.car_data[0],))
            services = cursor.fetchall()

            if services:
                details_text = ""
                total_cost = 0
                for service in services:
                    details_text += f"{service[0]}: {service[1]} (Вартість: {service[2]})\n"
                    total_cost += service[2]
                detail_label.setPlainText(details_text)
                layout.addWidget(QLabel(f"Загальна вартість ремонту: {total_cost}"))
            else:
                detail_label.setPlainText("Немає опису")

            cursor.close()
            conn.close()

            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)
        except Exception as e:
            self.show_error_message(f"Сталася помилка при завантаженні даних: {e}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Помилка", message)


class UserWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle(f"Користувач: {user_data[1]} {user_data[2]}")
        self.setGeometry(100, 100, 900, 900)
        try:
            self.initUI()
            self.applyStyleSheet()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації: {e}")

    def initUI(self):
        try:
            self.tabs = QTabWidget(self)
            self.setCentralWidget(self.tabs)

            self.profile_tab = QWidget()
            self.cars_tab = QWidget()

            self.tabs.addTab(self.profile_tab, "Особистий кабінет")
            self.tabs.addTab(self.cars_tab, "Мої авто")

            self.initProfileTab()
            self.initCarsTab()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації вкладок: {e}")

    def initProfileTab(self):
        try:
            layout = QVBoxLayout(self.profile_tab)
            h_layout = QHBoxLayout()

            photo_label = QLabel()
            photo_path = os.path.join('user_photos', f'User_{self.user_data[0]}.jpg')
            if os.path.exists(photo_path):
                pixmap = QPixmap(photo_path)
                photo_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                photo_label.setText("Немає фото")
            photo_label.setObjectName("PhotoLabel")
            photo_layout = QVBoxLayout()
            photo_layout.addWidget(photo_label)
            photo_layout.setAlignment(Qt.AlignCenter)

            info_label = QLabel(f"Ім'я: {self.user_data[1]}\nПрізвище: {self.user_data[2]}\n"
                                f"Телефон: {self.user_data[3]}\nEmail: {self.user_data[4]}")
            info_label.setObjectName("InfoLabel")
            info_layout = QVBoxLayout()
            info_layout.addWidget(info_label)
            info_layout.setAlignment(Qt.AlignCenter)

            h_layout.addLayout(photo_layout)
            h_layout.addLayout(info_layout)
            layout.addLayout(h_layout)

            upload_user_photo_button = QPushButton("Завантажити фото")
            layout.addWidget(upload_user_photo_button)
            upload_user_photo_button.clicked.connect(
                lambda ch, user_id=self.user_data[0]: self.uploadUserPhoto(user_id))
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації особистого кабінету: {e}")

    def uploadUserPhoto(self, user_id):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Вибрати фото користувача", "", "Image files (*.jpg *.png)")
            if path:
                filename = os.path.join('user_photos', f'User_{user_id}.jpg')
                self.ensure_directory_exists('user_photos')
                if os.path.exists(filename):
                    reply = QMessageBox.question(self, 'Підтвердження', 'Фото користувача вже існує. Замінити його?',
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.No:
                        return
                shutil.copy(path, filename)
                # Оновлюємо QLabel з фото користувача, якщо він існує, встановлюючи нове зображення за допомогою setPixmap
                photo_label = self.findChild(QLabel, "PhotoLabel")
                if photo_label:
                    pixmap = QPixmap(path)
                    photo_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                # Оновлюємо шлях до фото в базі даних
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("UPDATE Client SET ClientPhoto = %s WHERE ClientID = %s", (filename, user_id))
                conn.commit()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при завантаженні фото користувача: {e}")

    def applyStyleSheet(self):
        try:
            with open(STYLE_SHEET_PATH, "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            self.show_error_message(f"Сталася помилка при завантаженні стилів: {e}")

    def initCarsTab(self):
        try:
            layout = QVBoxLayout()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_content = QWidget(scroll)
            scroll_layout = QVBoxLayout(scroll_content)

            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT CarID, Make, Model, Year, LicensePlate, CarPhoto, VIN FROM Car WHERE OwnerID = %s",
                (self.user_data[0],))
            cars = cursor.fetchall()

            for car in cars:
                car_frame = QFrame()
                car_layout = QVBoxLayout()  # Вертикальний макет для кожного автомобіля

                # Перший рядок з фото та описом автомобіля
                car_info_layout = QHBoxLayout()  # Горизонтальний макет для фото та опису
                car_photo_label = QLabel()
                car_photo_path = os.path.join('car_photos', f'Car_{car[0]}.jpg')
                if os.path.exists(car_photo_path):
                    car_pixmap = QPixmap(car_photo_path)
                    car_photo_label.setPixmap(car_pixmap.scaled(300, 300, Qt.KeepAspectRatio))
                else:
                    car_photo_label.setText("Немає фото")
                car_photo_label.setObjectName(f"CarPhotoLabel_{car[0]}")
                car_info_layout.addWidget(car_photo_label)

                car_info_label = QLabel(
                    f"Марка: {car[1]}\nМодель: {car[2]}\nРік: {car[3]}\nНомерний знак: {car[4]}\nVIN: {car[6]}")
                car_info_layout.addWidget(car_info_label)

                car_layout.addLayout(car_info_layout)  # Додаємо перший рядок до загального макету авто

                # Другий рядок з кнопками "Замінити фото" та "Деталі"
                buttons_layout = QHBoxLayout()  # Горизонтальний макет для кнопок
                upload_car_photo_button = QPushButton("Замінити фото авто")
                upload_car_photo_button.clicked.connect(lambda ch, car_id=car[0]: self.uploadCarPhoto(car_id))
                buttons_layout.addWidget(upload_car_photo_button)

                details_button = QPushButton("Деталі")
                details_button.clicked.connect(lambda ch, car=car: self.showCarDetails(car))
                buttons_layout.addWidget(details_button)

                car_layout.addLayout(buttons_layout)  # Додаємо другий рядок до загального макету авто

                car_frame.setLayout(car_layout)
                scroll_layout.addWidget(car_frame)

            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)
            self.cars_tab.setLayout(layout)
        except Exception as e:
            self.show_error_message(f"Сталася помилка при ініціалізації вкладки авто: {e}")

    def showCarDetails(self, car):
        try:
            self.car_details_window = CarDetailsWindow(car)
            self.car_details_window.show()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при відображенні деталей авто: {e}")

    def ensure_directory_exists(self, folder):
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except Exception as e:
            self.show_error_message(f"Сталася помилка при перевірці/створенні каталогу: {e}")

    def uploadCarPhoto(self, car_id):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Вибрати фото авто", "", "Image files (*.jpg *.png)")
            if path:
                filename = os.path.join('car_photos', f'Car_{car_id}.jpg')
                self.ensure_directory_exists('car_photos')
                if os.path.exists(filename):
                    reply = QMessageBox.question(self, 'Підтвердження', 'Фото авто вже існує. Замінити його?',
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.No:
                        return
                shutil.copy(path, filename)
                # Обновляем QLabel с фото авто
                car_photo_label = self.findChild(QLabel, f"CarPhotoLabel_{car_id}")
                if car_photo_label:
                    car_pixmap = QPixmap(path)
                    car_photo_label.setPixmap(car_pixmap.scaled(300, 300, Qt.KeepAspectRatio))
                # Обновляем путь к фото в базе данных
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("UPDATE Car SET CarPhoto = %s WHERE CarID = %s", (filename, car_id))
                conn.commit()
        except Exception as e:
            self.show_error_message(f"Сталася помилка при завантаженні фото авто: {e}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Помилка", message)
