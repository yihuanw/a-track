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

        # header
        self.header = QLabel("ASSIGNMENT\nTRACKER")
        self.header.setObjectName("headerLabel")
        self.header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(self.header, alignment=Qt.AlignmentFlag.AlignHCenter)

        # buttons
        btn_cal = layout.IconTextButton(logic.path("assets/icon/calendar.png"), "Calendar")
        btn_tasks = layout.IconTextButton(logic.path("assets/icon/tasks.png"), "Tasks")
        btn_prof = layout.IconTextButton(logic.path("assets/icon/profile.png"), "Profile")
        self.buttons = [btn_cal, btn_tasks, btn_prof]

        for btn in self.buttons:
            left_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        def show_tasks_panel():
            uid = db.get_uid()
            if not uid:
                return
            
            tasks_panel = TasksPanel(uid)
            stacked_widget.addWidget(tasks_panel)
            stacked_widget.setCurrentIndex(stacked_widget.count() - 1)

        btn_tasks.clicked.connect(show_tasks_panel)
        btn_prof.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))

        left_layout.addStretch()

        # right layout
        right_layout = QVBoxLayout(self.right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # stacked widget
        stacked_widget = QStackedWidget()
        stacked_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        stacked_widget.addWidget(ProfilePanel()) 

        right_layout.addWidget(stacked_widget)

        # horizontal split
        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(0,0,0,0)
        split_layout.setSpacing(0)
        split_layout.addWidget(self.left, 1)
        split_layout.addWidget(self.right, 5)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addLayout(split_layout)

        # scale based on screen width
        screen_width = QGuiApplication.primaryScreen().geometry().width()
        left_width = screen_width // 6  # left panel = 1/6 screen width

        layout.scale_text(self.header, left_width)
        layout.scale_buttons(self.buttons, left_width)