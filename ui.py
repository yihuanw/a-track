from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtCore import Qt
import os

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assignment Tracker")

        # load intel bold font
        font_path = os.path.join("assets", "Inter", "Inter-VariableFont_opsz,wght.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("failed to load font")

        # panels
        self.left = QWidget()
        self.right = QWidget()
        self.left.setObjectName("leftPanel")
        self.right.setObjectName("rightPanel")

        # left layout
        left_layout = QVBoxLayout(self.left)
        left_layout.setSpacing(20)

        # header label
        header = QLabel("ASSIGNMENT \nTRACKER")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignLeft)
        left_layout.addWidget(header, alignment=Qt.AlignHCenter)

        # split layout
        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(0,0,0,0)
        split_layout.setSpacing(0)
        split_layout.addWidget(self.left, 1)
        split_layout.addWidget(self.right, 5)

        # main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addLayout(split_layout)
