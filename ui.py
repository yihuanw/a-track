from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QStackedWidget, QSizePolicy
)
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtCore import Qt

from interface import layout
import logic, os, sys
from interface.tasks import TasksPanel

def path(*paths):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)
    return os.path.join(base, *paths)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # window bar
        self.setWindowTitle("Assignment Tracker")
        self.setWindowIcon(QIcon(path("assets/icon/logo.png")))

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
        btn_cal = layout.IconTextButton(path("assets/icon/calendar.png"), "calendar")
        btn_tasks = layout.IconTextButton(path("assets/icon/tasks.png"), "tasks")
        btn_prof = layout.IconTextButton(path("assets/icon/profile.png"), "profile")
        self.buttons = [btn_cal, btn_tasks, btn_prof]

        for btn in self.buttons:
            left_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        btn_cal.clicked.connect(logic.on_cal_clicked)
        btn_tasks.clicked.connect(logic.on_tasks_clicked)
        btn_prof.clicked.connect(logic.on_prof_clicked)

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
        tasks_panel = TasksPanel()
        stacked_widget.addWidget(tasks_panel)
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