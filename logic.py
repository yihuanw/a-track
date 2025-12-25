from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
import sys, os

# repath for pyinstaller
def path(*paths):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)
    return os.path.join(base, *paths)


# buttons for ui.py
def on_cal_clicked():
    print("calendar")

def on_tasks_clicked():
    print("tasks")

def on_prof_clicked():
    print("profile")


# controls for tasks.py
def add_task(add_task_input, task_list):
    text = add_task_input.text().strip()
    if not text:
        return
    item = QListWidgetItem(text)
    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
    item.setCheckState(Qt.CheckState.Unchecked)
    task_list.addItem(item)
    add_task_input.clear()

def recolor(color, svg_path):
    renderer = QSvgRenderer(svg_path)

    # determine size
    size = renderer.defaultSize()
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)  # keep transparency

    painter = QPainter(pixmap)
    # render the SVG onto the pixmap
    renderer.render(painter)
    
    # apply recolor
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()

    return pixmap