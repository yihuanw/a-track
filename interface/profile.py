from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from . import layout
import db

class ProfilePanel(QWidget):
    def __init__(self):
        super().__init__()

        screen = QGuiApplication.primaryScreen().geometry()
        panel_width = int(screen.width() * (5 / 6))
        panel_height = screen.height()

        self.setFixedSize(panel_width, panel_height)

        # main layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(30)

        # container for email/password
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)
        form_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        input_width = int(panel_width * 0.25)
        input_height = int(panel_height * 0.05)

        # email field
        email_input = QLineEdit()
        email_input.setPlaceholderText("email")
        email_input.setFixedSize(input_width, input_height)
        email_input.setObjectName("prof_emailInput")
        form_layout.addWidget(email_input)

        # password field
        password_input = QLineEdit()
        password_input.setPlaceholderText("password")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setFixedSize(input_width, input_height)
        password_input.setObjectName("prof_passwordInput")
        form_layout.addWidget(password_input)

        # submit button
        submit_button = QPushButton("submit")
        submit_button.setFixedWidth(input_width)
        submit_button.setObjectName("prof_submitButton")

        submit_button.clicked.connect(lambda: db.login(
            email_input.text(), password_input.text()
        ))

        form_layout.addWidget(submit_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # scale text/buttons
        layout.scale_buttons([submit_button], input_width * 0.5)
        font = submit_button.font()
        email_input.setFont(font)
        password_input.setFont(font)

        main_layout.addWidget(form_container)