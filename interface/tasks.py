from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QListWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from . import layout

class TasksPanel(QWidget):
    def __init__(self):
        super().__init__()
        panel_width = QGuiApplication.primaryScreen().geometry().width() * (5/6)
        panel_height = QGuiApplication.primaryScreen().geometry().height()

        # calculate rectangle sizes
        rect_height = int(panel_height * 0.85)  # 85% of panel height
        rect_width = int(panel_width * 0.9)
        total_ratio = 1 + 4
        left_width = int(rect_width * 1 / total_ratio)
        right_width = int(rect_width * 4 / total_ratio)

        # main layout
        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(20)

        # left rectangle
        self.left_rect = QWidget()
        self.left_rect.setFixedSize(left_width, rect_height)
        self.left_rect.setObjectName("tasks_leftRect")

        left_layout = QVBoxLayout(self.left_rect)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # header
        header = QLabel("FOLDERS")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setObjectName("tasks_header")
        left_layout.addWidget(header)
        layout.scale_text(header, int(left_width * 0.6), 0.7)
        header_height = header.sizeHint().height()

        # scrollable list
        folder_list = QListWidget()
        folder_list.setFixedHeight(int((rect_height - header_height - 50)))
        folder_list.addItems(["all", "folder 1", "folder 2", "folder 3", "uncategorized"])

        font = header.font()
        font.setPointSize(int(font.pointSize() * 0.75))
        folder_list.setFont(font)
        left_layout.addWidget(folder_list)

        # right rectangle
        self.right_rect = QWidget()
        self.right_rect.setFixedSize(right_width, rect_height)
        self.right_rect.setObjectName("tasks_rightRect")

        main_layout.addWidget(self.left_rect)
        main_layout.addWidget(self.right_rect)
