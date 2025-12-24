from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QListWidget, QLineEdit, QListWidgetItem, 
    QStyledItemDelegate, QStyle, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QPainter, QColor
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
        layout.scale_text(header, int(left_width * 0.6), 0.7)
        header_height = header.sizeHint().height()

        left_layout.addWidget(header)

        # scrollable list
        folder_list = QListWidget()
        folder_list.setFixedHeight(int((rect_height - header_height - 50)))
        folder_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        folders = ["all", "folder 1", "folder 2", "folder 3", "uncategorized"]
        colors = [Qt.GlobalColor.transparent, "#929FCA", "#B39BA5", "#BDD2C0", Qt.GlobalColor.transparent]

        for folder in folders:
            item = QListWidgetItem(folder)
            folder_list.addItem(item)

        font = header.font()
        font.setPointSize(int(font.pointSize() * 0.75))
        folder_list.setFont(font)

        folder_list.setItemDelegate(circleDelegate(colors, folder_list))
        left_layout.addWidget(folder_list)

        # right rectangle
        self.right_rect = QWidget()
        self.right_rect.setFixedSize(right_width, rect_height)
        self.right_rect.setObjectName("tasks_rightRect")

        right_layout = QVBoxLayout(self.right_rect)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left, top, right, bottom = right_layout.getContentsMargins()
        right_layout.setContentsMargins(left, int(header_height // 2), right, bottom)

        # add task input
        add_task_input = QLineEdit()
        add_task_input.setPlaceholderText("add task")
        add_task_input.setFixedHeight(int(header_height * 1.5))
        add_task_input.setFixedWidth(int(right_width * 0.9))
        add_task_input.setObjectName("tasks_addTaskInput")
        add_task_input.setFont(font)

        right_layout.addWidget(add_task_input, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.left_rect)
        main_layout.addWidget(self.right_rect)

# delegate for bullet circles
class circleDelegate(QStyledItemDelegate):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = colors

    def paint(self, painter, option, index):
        row = index.row()
        if row >= len(self.colors):
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # draw the background according to the QSS
        style = option.widget.style() if option.widget else None
        if style:
            style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)

        # circle
        radius = option.rect.height() * 0.15
        padding = option.rect.height() * 0.15  # 15% of item height
        center_x = option.rect.left() + radius + padding
        center_y = option.rect.center().y()
        painter.setBrush(QColor(self.colors[row]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(2*radius), int(2*radius))

        # text
        text_rect = option.rect.adjusted(int(5*radius), 0, 0, 0)
        painter.setPen(option.palette.color(option.palette.ColorRole.Text))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, index.data())

        painter.restore()