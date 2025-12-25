from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QGuiApplication, QPainter, QColor

from . import layout
import logic

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
        folder_list.setObjectName("tasks_folderlist")

        folders = ["all", "folder 1", "folder 2", "folder 3", "folder 4", "folder 5", "folder 6", "folder 7", "uncategorized"]
        colors = [Qt.GlobalColor.transparent, "#929FCA", "#B39BA5", "#BDD2C0", "#929FCA", "#B39BA5", "#BDD2C0", "#929FCA", Qt.GlobalColor.transparent]

        for folder in folders:
            item = QListWidgetItem(folder)
            folder_list.addItem(item)

        font = header.font()
        font.setPointSize(int(font.pointSize() * 0.75))
        folder_list.setFont(font)

        folder_list.setItemDelegate(CircleDelegate(colors, folder_list))
        left_layout.addWidget(folder_list)

        # right rectangle
        self.right_rect = QWidget()
        self.right_rect.setFixedSize(right_width, rect_height)
        self.right_rect.setObjectName("tasks_rightRect")

        right_layout = QVBoxLayout(self.right_rect)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left, top, right, bottom = right_layout.getContentsMargins()
        right_layout.setContentsMargins(left, int(header_height // 2), right, int(header_height // 2))

        # add task input
        add_task_input = QLineEdit()
        add_task_input.setPlaceholderText("add task")
        add_task_input.setFixedHeight(int(header_height * 1.5))
        add_task_input.setFixedWidth(int(right_width * 0.9))
        add_task_input.setFont(font)
        add_task_input.setObjectName("tasks_addTaskInput")

        right_layout.addWidget(add_task_input, alignment=Qt.AlignmentFlag.AlignCenter)

        # task checklist
        task_list = QListWidget()
        task_list.setFixedHeight(int((rect_height - int(header_height * 1.5) - 50)))
        task_list.setFixedWidth(int(right_width * 0.9))
        task_list.setFont(font)
        task_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        task_list.setObjectName("tasks_tasklist")

        add_task_input.returnPressed.connect(
            lambda: logic.add_task(add_task_input, task_list)
        )
        task_list.setItemDelegate(SimpleSVGCheckDelegate(parent=task_list))

        right_layout.addWidget(task_list, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.left_rect)
        main_layout.addWidget(self.right_rect)


# delegate for bullet circles
class CircleDelegate(QStyledItemDelegate):
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


# delegate for checkmark
class SimpleSVGCheckDelegate(QStyledItemDelegate):
    COLOR_MAP = {"a": "#b39ba5", "b": "#929FCA", "c": "#BDD2C0"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_checked = {}
        self.cached_unchecked = {}

    def get_checkbox_size(self, option):
        if option.widget:
            widget = option.widget
            return int(widget.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorHeight, None, widget) * 1.75)
        return 24

    def get_pixmap(self, text, checked=True):
        color = self.COLOR_MAP.get(text, "#ebe6e8")
        cache = self.cached_checked if checked else self.cached_unchecked
        key = (text, color)
        if key not in cache:
            path = logic.path("assets/icon/check.svg" if checked else "assets/icon/uncheck.svg")
            cache[key] = logic.recolor(color, path)
        return cache[key]

    def paint(self, painter: QPainter, option, index):
        state = index.data(Qt.ItemDataRole.CheckStateRole)
        if state is None:
            return

        checkbox_size = self.get_checkbox_size(option)
        text = index.data(Qt.ItemDataRole.DisplayRole)

        checked = (state == Qt.CheckState.Checked)
        pixmap = self.get_pixmap(text, checked)

        # draw the checkbox
        y = option.rect.top() + (option.rect.height() - checkbox_size) // 2
        x = option.rect.left()
        painter.drawPixmap(x, y, checkbox_size, checkbox_size, pixmap)

        # draw the text
        text_rect = option.rect.adjusted(checkbox_size + 4, 0, 0, 0)
        if text:
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)

    def editorEvent(self, event, model, option, index):
        if event.type() == event.Type.MouseButtonRelease:
            checkbox_size = self.get_checkbox_size(option)
            y = option.rect.top() + (option.rect.height() - checkbox_size) // 2
            x = option.rect.left()
            checkbox_rect = QRect(x, y, checkbox_size, checkbox_size)

            if checkbox_rect.contains(event.pos()):
                current_state = index.data(Qt.ItemDataRole.CheckStateRole)
                new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
                if option.widget:
                    option.widget.viewport().update()
                return True

        return super().editorEvent(event, model, option, index)