from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtCore import Qt
 
from interface import layout
import logic, db
from interface.tasks import TasksPanel
from interface.profile import ProfilePanel
 
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
 
        self.setWindowTitle("Assignment Tracker")
        self.setWindowIcon(QIcon(logic.path("assets/icon/logo.png")))
 
        # panels
        self.left  = QWidget()
        self.right = QWidget()
        self.left.setObjectName("leftPanel")
        self.right.setObjectName("rightPanel")
 
        # left layout
        left_layout = QVBoxLayout(self.left)
        left_layout.setSpacing(20)
        left_layout.setContentsMargins(0, 20, 0, 20)
 
        self.header = QLabel("ASSIGNMENT\nTRACKER")
        self.header.setObjectName("headerLabel")
        self.header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(self.header, alignment=Qt.AlignmentFlag.AlignHCenter)
        left_layout.addStretch()
 
        self.logout_button = QPushButton("Log Out")
        self.logout_button.setObjectName("logoutButton")
        self.logout_button.clicked.connect(self.handle_logout)
        left_layout.addWidget(self.logout_button, alignment=Qt.AlignmentFlag.AlignHCenter)
 
        # right / stacked
        right_layout = QVBoxLayout(self.right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
 
        self.stacked_widget = QStackedWidget()
 
        # index 0 — login screen
        self.profile_panel = ProfilePanel()
        self.profile_panel.loginSucceeded.connect(self.show_tasks_panel)
        self.stacked_widget.addWidget(self.profile_panel)
 
        # index 1+ — TasksPanel (dynamic)
 
        right_layout.addWidget(self.stacked_widget)
 
        # layout split
        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(0)
        split_layout.addWidget(self.left,  1)
        split_layout.addWidget(self.right, 5)
 
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(split_layout)
 
        # scaling
        screen_width    = QGuiApplication.primaryScreen().geometry().width()
        self.left_width = screen_width // 6
        layout.scale_text(self.header, self.left_width)
        layout.scale_buttons([self.logout_button], self.left_width)
 
        self.logout_button.hide()
 
        if db.has_valid_session():
            # Build tasks panel synchronously — window hasn't shown yet so
            # there's nothing to flash; it opens directly on the tasks screen.
            uid = db.get_uid()
            self._build_tasks_panel(uid)
        else:
            self.stacked_widget.setCurrentIndex(0)

    def _build_tasks_panel(self, uid):
        # Remove any existing TasksPanel (index 1+)
        while self.stacked_widget.count() > 1:
            self.stacked_widget.removeWidget(self.stacked_widget.widget(1))
 
        panel = TasksPanel(uid)
        self.stacked_widget.addWidget(panel)
        self.stacked_widget.setCurrentIndex(1)
        self.logout_button.show()

    def show_tasks_panel(self):
        uid = db.get_uid()
        if not uid:
            return
        self._build_tasks_panel(uid)

    def handle_logout(self):
        db.logout()
        self.profile_panel.reset_login_form()
        self.logout_button.hide()
 
        while self.stacked_widget.count() > 1:
            self.stacked_widget.removeWidget(self.stacked_widget.widget(1))
 
        self.stacked_widget.setCurrentIndex(0)