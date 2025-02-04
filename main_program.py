import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QScrollArea, 
                           QToolBar, QFrame, QStackedWidget, QLineEdit,
                           QMessageBox, QSizePolicy)
from PyQt5.QtCore import Qt

class PasswordManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Password Manager")
        self.setGeometry(100, 100, 800, 600)
        self.passwords_file = 'passwords.json'
        self.settings_file = 'settings.json'
        self.load_passwords()
        self.load_settings()
        self.setup_ui()

    def setup_ui(self):
        """Set up the main UI components"""
        # Create toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add toolbar buttons
        toolbar_buttons = [
            ("New Password", self.show_add_password_page),
            ("Help", self.show_help_page),
            ("Settings", self.show_settings_page)
        ]
        for text, callback in toolbar_buttons:
            btn = self.create_button(text, callback)
            toolbar.addWidget(btn)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add app name
        self.app_name = self.create_header("Password Manager")
        layout.addWidget(self.app_name)

        # Create stacked widget
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Create and add pages
        self.pages = {
            'main': self.create_main_page(),
            'add': self.create_add_password_page(),
            'help': self.create_help_page(),
            'settings': self.create_settings_page(),
            'update': self.create_update_password_page()
        }
        
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

    def create_button(self, text, callback=None, fixed_width=None):
        """Create a standardized button"""
        btn = QPushButton(text)
        if callback:
            btn.clicked.connect(callback)
        if fixed_width:
            btn.setFixedWidth(fixed_width)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return btn

    def create_header(self, text, size=18, margin=10):
        """Create a standardized header"""
        label = QLabel(text)
        label.setStyleSheet(f"font-size: {size}px; font-weight: bold; margin-bottom: {margin}px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def create_page(self, title, content_widget, buttons=None):
        """Create a standardized page with header, content, and buttons"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        if title:
            layout.addWidget(self.create_header(title, 24, 20))

        layout.addWidget(content_widget)
        layout.addStretch()

        if buttons:
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.addStretch()
            for btn in buttons:
                button_layout.addWidget(btn)
            button_layout.addStretch()
            layout.addWidget(button_widget)

        # Add close button
        layout.addWidget(self.create_close_button())
        return page

    def create_close_button(self):
        """Create a standardized close button"""
        return self.create_button("Close Password Manager", self.close)

    def create_input_field(self, label_text, placeholder="", readonly=False, password=False):
        """Create a standardized input field with label"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setReadOnly(readonly)
        if password:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addWidget(label)
        layout.addWidget(input_field)
        return widget, input_field

    def load_passwords(self):
        """Load passwords from JSON file"""
        self.passwords = {}
        if os.path.exists(self.passwords_file):
            try:
                with open(self.passwords_file, 'r') as f:
                    self.passwords = json.load(f)
            except json.JSONDecodeError:
                pass

    def load_settings(self):
        """Load settings from JSON file"""
        self.default_settings = {
            'min_length': 8,
            'max_length': 20,
            'require_special': True,
            'require_capital': True,
            'require_number': True
        }
        self.settings = self.default_settings.copy()
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
            except json.JSONDecodeError:
                pass

    def save_to_json(self, data, filename, success_msg=None):
        """Save data to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            if success_msg:
                QMessageBox.information(self, "Success", success_msg)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
            return False

    def create_password_row(self, program_name):
        """Create a row for the password list"""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        program_label = QLabel(program_name)
        program_label.setMinimumWidth(150)

        buttons = [
            ("Retrieve", lambda: self.retrieve_password(program_name)),
            ("Update", lambda: self.show_update_password_page(program_name)),
            ("Delete", lambda: self.delete_password(program_name))
        ]

        layout.addWidget(program_label)
        for text, callback in buttons:
            btn = self.create_button(text, callback, 80)
            layout.addWidget(btn)
        layout.addStretch()

        return row

    def create_main_page(self):
        content = QScrollArea()
        content.setWidgetResizable(True)
        content.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        self.password_list_layout = QVBoxLayout(scroll_content)
        self.password_list_layout.setSpacing(0)
        self.password_list_layout.setContentsMargins(0, 0, 0, 0)
        
        self.refresh_password_list()
        content.setWidget(scroll_content)
        
        return self.create_page(None, content)

    def refresh_password_list(self):
        """Refresh the password list display"""
        while self.password_list_layout.count():
            child = self.password_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, program_name in enumerate(sorted(self.passwords.keys())):
            row = self.create_password_row(program_name)
            self.password_list_layout.addWidget(row)
            
            if i < len(self.passwords) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                self.password_list_layout.addWidget(line)

        self.password_list_layout.addStretch()

    def create_add_password_page(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        
        program_widget, self.program_input = self.create_input_field("Program Name:", "Enter program name")
        password_widget, self.password_input = self.create_input_field("Password:", "Enter password", password=True)
        
        layout.addWidget(program_widget)
        layout.addWidget(password_widget)
        
        buttons = [
            self.create_button("Save", self.save_password, 100),
            self.create_button("Cancel", self.show_main_page, 100)
        ]
        
        return self.create_page("Add a New Password", content, buttons)

    def create_update_password_page(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        
        program_widget, self.update_program_input = self.create_input_field("Program Name:", readonly=True)
        password_widget, self.update_password_input = self.create_input_field("New Password:", "Enter new password", password=True)
        
        layout.addWidget(program_widget)
        layout.addWidget(password_widget)
        
        buttons = [
            self.create_button("Update", self.update_password, 100),
            self.create_button("Cancel", self.show_main_page, 100)
        ]
        
        return self.create_page("Update Password", content, buttons)

    def create_help_page(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        
        help_text = """
        Adding a Password:
        1. Click 'New Password' in the toolbar
        2. Enter program name and password
        3. Click 'Save' to store
        
        Retrieving a Password:
        Click 'Retrieve' next to any program
        
        Updating a Password:
        Click 'Update' next to any program
        
        Deleting a Password:
        Click 'Delete' next to any program
        """
        
        help_label = QLabel(help_text.strip())
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        buttons = [self.create_button("Back to Main Page", self.show_main_page, 150)]
        return self.create_page("Help & Instructions", content, buttons)

    def create_settings_page(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        
        min_widget, self.min_length_input = self.create_input_field("Minimum Password Length:")
        max_widget, self.max_length_input = self.create_input_field("Maximum Password Length:")
        
        layout.addWidget(min_widget)
        layout.addWidget(max_widget)
        
        buttons = [
            self.create_button("Save Settings", self.save_settings),
            self.create_button("Reset to Defaults", self.reset_settings),
            self.create_button("Cancel", self.show_main_page)
        ]
        
        return self.create_page("Password Settings", content, buttons)

    def save_settings(self):
        """Save settings to JSON file"""
        try:
            min_length = int(self.min_length_input.text())
            max_length = int(self.max_length_input.text())
            
            if min_length < 1 or max_length < min_length:
                QMessageBox.warning(self, "Invalid Input", 
                    "Minimum length must be at least 1 and maximum length must be greater than or equal to minimum length.")
                return
            
            self.settings['min_length'] = min_length
            self.settings['max_length'] = max_length
            
            if self.save_to_json(self.settings, self.settings_file, "Settings saved successfully!"):
                self.show_main_page()
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Length values must be valid numbers.")

    def reset_settings(self):
        """Reset settings to default values"""
        self.settings = self.default_settings.copy()
        self.min_length_input.setText(str(self.settings['min_length']))
        self.max_length_input.setText(str(self.settings['max_length']))
        self.save_to_json(self.settings, self.settings_file, "Settings reset to defaults!")

    # Navigation methods
    def show_main_page(self): self.stacked_widget.setCurrentIndex(0)
    def show_add_password_page(self): self.stacked_widget.setCurrentIndex(1)
    def show_help_page(self): self.stacked_widget.setCurrentIndex(2)
    def show_settings_page(self): self.stacked_widget.setCurrentIndex(3)
    def show_update_password_page(self, program_name):
        self.update_program_input.setText(program_name)
        self.update_password_input.clear()
        self.stacked_widget.setCurrentIndex(4)

    # Password operations
    def save_password(self):
        program = self.program_input.text().strip()
        password = self.password_input.text().strip()
        
        if not program or not password:
            QMessageBox.warning(self, "Input Error", "Both fields are required!")
            return
            
        self.passwords[program] = password
        if self.save_to_json(self.passwords, self.passwords_file, "Password saved successfully!"):
            self.program_input.clear()
            self.password_input.clear()
            self.refresh_password_list()
            self.show_main_page()

    def update_password(self):
        program = self.update_program_input.text().strip()
        password = self.update_password_input.text().strip()
        
        if not password:
            QMessageBox.warning(self, "Input Error", "Password cannot be empty!")
            return
            
        self.passwords[program] = password
        if self.save_to_json(self.passwords, self.passwords_file, "Password updated successfully!"):
            self.update_password_input.clear()
            self.refresh_password_list()
            self.show_main_page()

    def retrieve_password(self, program_name):
        password = self.passwords.get(program_name, '')
        QMessageBox.information(self, "Password", f"Password for {program_name}: {password}")

    def delete_password(self, program_name):
        reply = QMessageBox.question(self, 'Delete Password',
                                   f'Delete password for {program_name}?',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.passwords[program_name]
            if self.save_to_json(self.passwords, self.passwords_file, "Password deleted successfully!"):
                self.refresh_password_list()

def main():
    app = QApplication(sys.argv)
    window = PasswordManager()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
