import sys
import mysql.connector
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox, \
    QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QDialog, QLabel
from PyQt5.QtCore import Qt, QTimer
from config import DB_CONFIG  # Імпортуємо конфігурацію з DB_CONFIG


class AddAdminDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Admin")
        self.setGeometry(300, 300, 400, 200)
        layout = QVBoxLayout()

        self.form_layout = QFormLayout()
        self.admin_name_input = QLineEdit()
        self.admin_password_input = QLineEdit()
        self.admin_password_input.setEchoMode(QLineEdit.Password)
        self.form_layout.addRow("Admin Name:", self.admin_name_input)
        self.form_layout.addRow("Admin Password:", self.admin_password_input)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_admin)

        layout.addLayout(self.form_layout)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def add_admin(self):
        admin_name = self.admin_name_input.text()
        admin_password = self.admin_password_input.text()
        if admin_name and admin_password:
            try:
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (admin_name, admin_password))
                conn.commit()
                cursor.close()
                conn.close()
                QMessageBox.information(self, 'Success', f'Admin {admin_name} added successfully.')
                self.accept()
            except mysql.connector.Error as err:
                QMessageBox.warning(self, 'Error', f'Error: {err}')
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Error: {e}')
        else:
            QMessageBox.warning(self, 'Error', 'Please fill in all fields.')


class AddServiceDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Service")
        self.setGeometry(300, 300, 400, 200)
        layout = QVBoxLayout()

        self.form_layout = QFormLayout()
        self.service_name_input = QLineEdit()
        self.service_price_input = QLineEdit()
        self.form_layout.addRow("Service Name:", self.service_name_input)
        self.form_layout.addRow("Service Price:", self.service_price_input)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_service)

        layout.addLayout(self.form_layout)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def add_service(self):
        service_name = self.service_name_input.text()
        service_price = self.service_price_input.text()
        if service_name and service_price:
            try:
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO service (name, price) VALUES (%s, %s)", (service_name, service_price))
                conn.commit()
                cursor.close()
                conn.close()
                QMessageBox.information(self, 'Success', f'Service {service_name} added successfully.')
                self.accept()
            except mysql.connector.Error as err:
                QMessageBox.warning(self, 'Error', f'Error: {err}')
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Error: {e}')
        else:
            QMessageBox.warning(self, 'Error', 'Please fill in all fields.')


class RootWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.connect_db()
        self.load_admins()
        self.load_services()

    def initUI(self):
        self.setWindowTitle('Root Window - Main Administrator Access Only')
        self.setGeometry(100, 100, 1000, 600)

        self.tab_widget = QTabWidget()

        # Tabs
        self.admin_tab = QWidget()
        self.service_tab = QWidget()

        self.tab_widget.addTab(self.admin_tab, "Admins")
        self.tab_widget.addTab(self.service_tab, "Services")

        # Admin Tab
        self.admin_layout = QVBoxLayout()
        self.admin_search_input = QLineEdit()
        self.admin_search_input.setPlaceholderText("Search admins...")
        self.admin_search_input.textChanged.connect(self.schedule_admin_search)
        self.admin_layout.addWidget(self.admin_search_input)

        self.admin_table = QTableWidget()
        self.admin_layout.addWidget(self.admin_table)

        self.admin_button_layout = QHBoxLayout()
        self.add_admin_button = QPushButton('Add Admin')
        self.update_admin_button = QPushButton('Update Admin')
        self.delete_admin_button = QPushButton('Delete Admin')
        self.admin_button_layout.addWidget(self.add_admin_button)
        self.admin_button_layout.addWidget(self.update_admin_button)
        self.admin_button_layout.addWidget(self.delete_admin_button)

        self.admin_layout.addLayout(self.admin_button_layout)
        self.admin_tab.setLayout(self.admin_layout)

        self.add_admin_button.clicked.connect(self.open_add_admin_dialog)
        self.update_admin_button.clicked.connect(self.update_admin)
        self.delete_admin_button.clicked.connect(self.delete_admin)
        self.admin_table.itemSelectionChanged.connect(self.load_selected_admin)

        # Service Tab
        self.service_layout = QVBoxLayout()
        self.service_search_input = QLineEdit()
        self.service_search_input.setPlaceholderText("Search services...")
        self.service_search_input.textChanged.connect(self.schedule_service_search)
        self.service_layout.addWidget(self.service_search_input)

        self.service_table = QTableWidget()
        self.service_layout.addWidget(self.service_table)

        self.service_button_layout = QHBoxLayout()
        self.add_service_button = QPushButton('Add Service')
        self.update_service_button = QPushButton('Update Service')
        self.delete_service_button = QPushButton('Delete Service')
        self.service_button_layout.addWidget(self.add_service_button)
        self.service_button_layout.addWidget(self.update_service_button)
        self.service_button_layout.addWidget(self.delete_service_button)

        self.service_layout.addLayout(self.service_button_layout)
        self.service_tab.setLayout(self.service_layout)

        self.add_service_button.clicked.connect(self.open_add_service_dialog)
        self.update_service_button.clicked.connect(self.update_service)
        self.delete_service_button.clicked.connect(self.delete_service)
        self.service_table.itemSelectionChanged.connect(self.load_selected_service)

        # Main Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.tab_widget)
        self.setLayout(self.main_layout)

    def connect_db(self):
        try:
            self.db = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.db.cursor()
        except mysql.connector.Error as err:
            QMessageBox.critical(self, 'Database Connection Error', f'Error: {err}')
        except Exception as e:
            QMessageBox.critical(self, 'Unknown Error', f'Error: {e}')

    def schedule_admin_search(self):
        self.admin_search_timer = QTimer()
        self.admin_search_timer.setSingleShot(True)
        self.admin_search_timer.timeout.connect(self.perform_admin_search)
        self.admin_search_timer.start(300)

    def perform_admin_search(self):
        search_text = self.admin_search_input.text()
        self.cursor.execute("SELECT * FROM admin WHERE username LIKE %s OR password LIKE %s",
                            (f'%{search_text}%', f'%{search_text}%'))
        rows = self.cursor.fetchall()
        self.admin_table.setRowCount(0)
        self.admin_table.setColumnCount(len(self.cursor.column_names))
        self.admin_table.setHorizontalHeaderLabels(self.cursor.column_names)
        for row in rows:
            row_position = self.admin_table.rowCount()
            self.admin_table.insertRow(row_position)
            for col, item in enumerate(row):
                self.admin_table.setItem(row_position, col, QTableWidgetItem(str(item)))
        self.admin_table.resizeColumnsToContents()

    def schedule_service_search(self):
        self.service_search_timer = QTimer()
        self.service_search_timer.setSingleShot(True)
        self.service_search_timer.timeout.connect(self.perform_service_search)
        self.service_search_timer.start(300)

    def perform_service_search(self):
        search_text = self.service_search_input.text()
        self.cursor.execute("SELECT * FROM service WHERE name LIKE %s OR price LIKE %s",
                            (f'%{search_text}%', f'%{search_text}%'))
        rows = self.cursor.fetchall()
        self.service_table.setRowCount(0)
        self.service_table.setColumnCount(len(self.cursor.column_names))
        self.service_table.setHorizontalHeaderLabels(self.cursor.column_names)
        for row in rows:
            row_position = self.service_table.rowCount()
            self.service_table.insertRow(row_position)
            for col, item in enumerate(row):
                self.service_table.setItem(row_position, col, QTableWidgetItem(str(item)))
        self.service_table.resizeColumnsToContents()

    def load_admins(self):
        self.cursor.execute("SELECT * FROM admin")
        rows = self.cursor.fetchall()
        self.admin_table.setRowCount(0)
        self.admin_table.setColumnCount(len(self.cursor.column_names))
        self.admin_table.setHorizontalHeaderLabels(self.cursor.column_names)
        for row in rows:
            row_position = self.admin_table.rowCount()
            self.admin_table.insertRow(row_position)
            for col, item in enumerate(row):
                self.admin_table.setItem(row_position, col, QTableWidgetItem(str(item)))
        self.admin_table.resizeColumnsToContents()

    def load_selected_admin(self):
        selected_row = self.admin_table.currentRow()
        if selected_row >= 0:
            self.admin_name_input.setText(self.admin_table.item(selected_row, 1).text())
            self.admin_password_input.setText(self.admin_table.item(selected_row, 2).text())

    def open_add_admin_dialog(self):
        dialog = AddAdminDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.load_admins()

    def update_admin(self):
        selected_row = self.admin_table.currentRow()
        if selected_row >= 0:
            admin_id = self.admin_table.item(selected_row, 0).text()
            admin_name = self.admin_name_input.text()
            admin_password = self.admin_password_input.text()
            if admin_name and admin_password:
                try:
                    self.cursor.execute("UPDATE admin SET username = %s, password = %s WHERE id = %s",
                                        (admin_name, admin_password, admin_id))
                    self.db.commit()
                    QMessageBox.information(self, 'Success', f'Admin {admin_name} updated successfully.')
                    self.load_admins()
                except mysql.connector.Error as err:
                    QMessageBox.warning(self, 'Error', f'Error: {err}')
            else:
                QMessageBox.warning(self, 'Error', 'Please fill in all fields.')
        else:
            QMessageBox.warning(self, 'Error', 'No admin selected.')

    def delete_admin(self):
        selected_row = self.admin_table.currentRow()
        if selected_row >= 0:
            admin_id = self.admin_table.item(selected_row, 0).text()
            try:
                self.cursor.execute("DELETE FROM admin WHERE id = %s", (admin_id,))
                self.db.commit()
                QMessageBox.information(self, 'Success', f'Admin deleted successfully.')
                self.load_admins()
            except mysql.connector.Error as err:
                QMessageBox.warning(self, 'Error', f'Error: {err}')
        else:
            QMessageBox.warning(self, 'Error', 'No admin selected.')

    def load_services(self):
        self.cursor.execute("SELECT * FROM service")
        rows = self.cursor.fetchall()
        self.service_table.setRowCount(0)
        self.service_table.setColumnCount(len(self.cursor.column_names))
        self.service_table.setHorizontalHeaderLabels(self.cursor.column_names)
        for row in rows:
            row_position = self.service_table.rowCount()
            self.service_table.insertRow(row_position)
            for col, item in enumerate(row):
                self.service_table.setItem(row_position, col, QTableWidgetItem(str(item)))
        self.service_table.resizeColumnsToContents()

    def load_selected_service(self):
        selected_row = self.service_table.currentRow()
        if selected_row >= 0:
            self.service_name_input.setText(self.service_table.item(selected_row, 1).text())
            self.service_price_input.setText(self.service_table.item(selected_row, 2).text())

    def open_add_service_dialog(self):
        dialog = AddServiceDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.load_services()

    def update_service(self):
        selected_row = self.service_table.currentRow()
        if selected_row >= 0:
            service_id = self.service_table.item(selected_row, 0).text()
            service_name = self.service_name_input.text()
            service_price = self.service_price_input.text()
            if service_name and service_price:
                try:
                    self.cursor.execute("UPDATE service SET name = %s, price = %s WHERE id = %s",
                                        (service_name, service_price, service_id))
                    self.db.commit()
                    QMessageBox.information(self, 'Success', f'Service {service_name} updated successfully.')
                    self.load_services()
                except mysql.connector.Error as err:
                    QMessageBox.warning(self, 'Error', f'Error: {err}')
            else:
                QMessageBox.warning(self, 'Error', 'Please fill in all fields.')
        else:
            QMessageBox.warning(self, 'Error', 'No service selected.')

    def delete_service(self):
        selected_row = self.service_table.currentRow()
        if selected_row >= 0:
            service_id = self.service_table.item(selected_row, 0).text()
            try:
                self.cursor.execute("DELETE FROM service WHERE id = %s", (service_id,))
                self.db.commit()
                QMessageBox.information(self, 'Success', f'Service deleted successfully.')
                self.load_services()
            except mysql.connector.Error as err:
                QMessageBox.warning(self, 'Error', f'Error: {err}')
        else:
            QMessageBox.warning(self, 'Error', 'No service selected.')

    def closeEvent(self, event):
        self.cursor.close()
        self.db.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RootWindow()
    window.show()
    sys.exit(app.exec_())
