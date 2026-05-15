from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QRect, QDateTime, pyqtSignal, QRunnable, QThreadPool
from PyQt6.QtGui import QPainter, QColor, QFont

import logic_tasks as logic


# ---------- Async worker ----------
class _Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn, self._args, self._kwargs = fn, args, kwargs
        self.setAutoDelete(True)

    def run(self):
        try:
            self._fn(*self._args, **self._kwargs)
        except Exception as e:
            print(f"[Worker] error: {e}")


def run_async(fn, *args, **kwargs):
    QThreadPool.globalInstance().start(_Worker(fn, *args, **kwargs))


# ---------- Folder list delegate ----------
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

        style = option.widget.style() if option.widget else None
        if style:
            style.drawPrimitive(
                QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget
            )

        radius = option.rect.height() * 0.15
        padding = option.rect.height() * 0.15
        center_x = option.rect.left() + radius + padding
        center_y = option.rect.center().y()
        painter.setBrush(QColor(self.colors[row]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(center_x - radius), int(center_y - radius),
            int(2 * radius), int(2 * radius)
        )

        text_rect = option.rect.adjusted(int(5 * radius), 0, 0, 0)
        painter.setPen(option.palette.color(option.palette.ColorRole.Text))
        painter.drawText(
            text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, index.data()
        )
        painter.restore()


# ---------- Task list delegate ----------
class SimpleSVGCheckDelegate(QStyledItemDelegate):
    taskToggled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_checked = {}
        self.cached_unchecked = {}

    def get_checkbox_size(self, option):
        if option.widget:
            return int(option.widget.style().pixelMetric(
                QStyle.PixelMetric.PM_IndicatorHeight, None, option.widget) * 1.75)
        return 24

    def get_pixmap(self, color, checked=True):
        cache = self.cached_checked if checked else self.cached_unchecked
        if color not in cache:
            svg = "assets/icon/check.svg" if checked else "assets/icon/uncheck.svg"
            cache[color] = logic.recolor(color, logic.path(svg))
        return cache[color]

    def paint(self, painter: QPainter, option, index):
        state = index.data(Qt.ItemDataRole.CheckStateRole)
        if state is None:
            return

        checkbox_size = self.get_checkbox_size(option)
        color = index.data(Qt.ItemDataRole.UserRole + 1) or "#ebe6e8"
        checked = (state == Qt.CheckState.Checked.value)
        pixmap = self.get_pixmap(color, checked)

        style = option.widget.style() if option.widget else None
        if style:
            style.drawPrimitive(
                QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget
            )

        y = option.rect.top() + (option.rect.height() - checkbox_size) // 2
        painter.drawPixmap(option.rect.left(), y, checkbox_size, checkbox_size, pixmap)

        display_text = index.data(Qt.ItemDataRole.DisplayRole)
        deadline = index.data(Qt.ItemDataRole.UserRole + 2)
        rect = option.rect

        if display_text:
            painter.drawText(
                QRect(rect.left() + checkbox_size + 4, rect.top(), rect.width() // 2, rect.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                display_text
            )

        if deadline:
            painter.save()
            is_overdue = deadline < QDateTime.currentDateTime()
            c = QColor(
                "#cf8085" if is_overdue
                else option.palette.color(option.palette.ColorRole.Text)
            )
            c.setAlphaF(0.75)
            painter.setPen(c)
            f = option.font
            f.setWeight(QFont.Weight.Normal)
            painter.setFont(f)
            painter.drawText(
                QRect(rect.left() + rect.width() // 2, rect.top(),
                      rect.width() // 2 - 4, rect.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                deadline.toString("MM/dd/yy HH:mm")
            )
            painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == event.Type.MouseButtonRelease:
            checkbox_size = self.get_checkbox_size(option)
            y = option.rect.top() + (option.rect.height() - checkbox_size) // 2
            checkbox_rect = QRect(option.rect.left(), y, checkbox_size, checkbox_size)

            if checkbox_rect.contains(event.pos()):
                current_state = Qt.CheckState(index.data(Qt.ItemDataRole.CheckStateRole))
                new_state = (
                    Qt.CheckState.Unchecked
                    if current_state == Qt.CheckState.Checked
                    else Qt.CheckState.Checked
                )
                model.setData(index, new_state.value, Qt.ItemDataRole.CheckStateRole)
                if option.widget:
                    option.widget.viewport().update(option.rect)

                task_id = index.data(Qt.ItemDataRole.UserRole)
                if task_id:
                    run_async(logic.update_task_completion, task_id, new_state == Qt.CheckState.Checked)
                    self.taskToggled.emit()

                return True
        return super().editorEvent(event, model, option, index)