from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtCore import Qt, QTimer

from interface import layout
import logic, db
from interface.tasks import TasksPanel
from interface.profile import ProfilePanel


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # window bar
        self.setWindowTitle("Assignment Tracker")
        self.setWindowIcon(QIcon(logic.path("assets/icon/logo.png")))

        # panels
        self.left = QWidget()
        self.right = QWidget()
        self.left.setObjectName("leftPanel")
        self.right.setObjectName("rightPanel")

        # left layout
        left_layout = QVBoxLayout(self.left)
        left_layout.setSpacing(20)

        self.header = QLabel("ASSIGNMENT\nTRACKER")
        self.header.setObjectName("headerLabel")
        self.header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(self.header, alignment=Qt.AlignmentFlag.AlignHCenter)

        left_layout.addStretch()

        self.logout_button = QPushButton("Log Out")
        self.logout_button.setObjectName("logoutButton")
        self.logout_button.clicked.connect(self.handle_logout)
        left_layout.addWidget(self.logout_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        left_layout.setContentsMargins(0, 20, 0, 20)

        # right layout
        right_layout = QVBoxLayout(self.right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()

        self.profile_panel = ProfilePanel()
        self.profile_panel.loginSucceeded.connect(self.show_tasks_panel)

        self.stacked_widget.addWidget(self.profile_panel)

        right_layout.addWidget(self.stacked_widget)

        # layout split
        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(0)
        split_layout.addWidget(self.left, 1)
        split_layout.addWidget(self.right, 5)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(split_layout)

        # scaling
        screen_width = QGuiApplication.primaryScreen().geometry().width()
        self.left_width = screen_width // 6

        layout.scale_text(self.header, self.left_width)
        layout.scale_buttons([self.logout_button], self.left_width)

        self.logout_button.hide()
        self.stacked_widget.setCurrentIndex(0)

        if db.has_valid_session():
            QTimer.singleShot(0, self.auto_login)

    def auto_login(self):
        if db.has_valid_session():
            self.profile_panel.loginSucceeded.emit()

    def show_tasks_panel(self):
        uid = db.get_uid()
        if not uid:
            return

        while self.stacked_widget.count() > 1:
            widget = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(widget)

        tasks_panel = TasksPanel(uid)
        self.stacked_widget.addWidget(tasks_panel)
        self.stacked_widget.setCurrentIndex(1)
        self.logout_button.show()

    def handle_logout(self):
        db.logout()
        self.profile_panel.reset_login_form()
        self.stacked_widget.setCurrentIndex(0)
        self.logout_button.hide()

        while self.stacked_widget.count() > 1:
            widget = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(widget)