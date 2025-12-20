from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

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

        # main layout, centered
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # left rectangle
        self.left_rect = QWidget()
        self.left_rect.setFixedSize(left_width, rect_height)

        # right rectangle
        self.right_rect = QWidget()
        self.right_rect.setFixedSize(right_width, rect_height)

        layout.addWidget(self.left_rect)
        layout.addWidget(self.right_rect)

        self.left_rect.setObjectName("tasks_leftRect")
        self.right_rect.setObjectName("tasks_rightRect")
