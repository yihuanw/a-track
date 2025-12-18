from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QPushButton
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
import logic, sys, os

# path helper
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
        self.setWindowIcon(QIcon(path("assets", "icon", "logo.png")))

        # panels
        self.left = QWidget()
        self.right = QWidget()
        self.left.setObjectName("leftPanel")
        self.right.setObjectName("rightPanel")

        self.left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # left layout
        left_layout = QVBoxLayout(self.left)
        left_layout.setSpacing(20)

        # header label
        header = QLabel("ASSIGNMENT \nTRACKER")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignHCenter)

        # container for buttons
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # buttons
        btn_cal = IconTextButton(path("assets", "icon", "calendar.png"), "calendar")
        btn_tasks = IconTextButton(path("assets", "icon", "tasks.png"), "tasks")
        btn_prof = IconTextButton(path("assets", "icon", "profile.png"), "profile")

        btn_cal.clicked.connect(logic.on_cal_clicked)
        btn_tasks.clicked.connect(logic.on_tasks_clicked)
        btn_prof.clicked.connect(logic.on_prof_clicked)

        # button container
        for btn in (btn_cal, btn_tasks, btn_prof):
            button_layout.addWidget(btn)

        left_layout.addWidget(button_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        left_layout.addStretch()
        
        # horizontal split layout with stretch factors
        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(0)
        split_layout.addWidget(self.left, 1)   # left = 1 part
        split_layout.addWidget(self.right, 5)  # right = 5 parts

        # main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(split_layout)

class IconTextButton(QPushButton):
    def __init__(self, icon_path, text):
        super().__init__()

        # remove default text
        self.setText("")

        # layout inside button
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)  # inner padding
        layout.setSpacing(10)

        # icon label
        icon_label = QLabel()
        icon = QIcon(icon_path)
        size = int(self.font().pointSize() * 2.5)
        icon_label.setPixmap(icon.pixmap(size, size))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(icon_label)

        # text label
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(text_label, 1)  # centers text

        # make button expand horizontally, fixed height
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(40)