from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication

from . import layout
import db

class ProfilePanel(QWidget):
    # signal emitted when user logs in successfully
    loginSucceeded = pyqtSignal()

    def __init__(self):
        super().__init__()

        # get screen size and set panel size
        screen = QGuiApplication.primaryScreen().geometry()
        panel_width = int(screen.width() * (5 / 6))
        panel_height = screen.height()
        self.setFixedSize(panel_width, panel_height)

        # main container layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # build login page
        self.login_page = self._build_login_page(panel_width, panel_height)
        main_layout.addWidget(self.login_page)

    def _build_login_page(self, panel_width, panel_height):
        # login screen container
        page = QWidget()
        layout_v = QVBoxLayout(page)
        layout_v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # sizing for inputs
        input_width = int(panel_width * 0.25)
        input_height = int(panel_height * 0.05)

        # email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email")
        self.email_input.setFixedSize(input_width, input_height)
        self.email_input.setObjectName("prof_emailInput")

        # password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedSize(input_width, input_height)
        self.password_input.setObjectName("prof_passwordInput")

        # error message label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setObjectName("prof_errorLabel")

        # submit button
        submit_button = QPushButton("submit")
        submit_button.setFixedWidth(input_width)
        submit_button.setObjectName("prof_submitButton")
        submit_button.clicked.connect(self.handle_login)

        # scale fonts consistently
        layout.scale_buttons([submit_button], input_width * 0.5)
        font = submit_button.font()
        self.email_input.setFont(font)
        self.password_input.setFont(font)

        # add widgets to layout
        layout_v.addWidget(self.email_input)
        layout_v.addWidget(self.password_input)
        layout_v.addWidget(self.error_label)
        layout_v.addWidget(submit_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        return page

    def try_auto_login(self):
        if db.has_valid_session():
            self.loginSucceeded.emit()

    def handle_login(self):
        # attempt login with entered credentials
        success = db.login(
            self.email_input.text(),
            self.password_input.text()
        )

        # emit signal or show error
        if success:
            self.loginSucceeded.emit()
            self.email_input.clear()
            self.password_input.clear()
            self.error_label.setText("")
        else:
            self.error_label.setText("invalid credentials")

    def reset_login_form(self):
        # reset login form for display after logout
        self.email_input.clear()
        self.password_input.clear()
        self.error_label.setText("")