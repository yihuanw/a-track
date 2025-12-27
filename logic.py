from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem, QColorDialog, QMenu, QInputDialog
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from dotenv import load_dotenv
import sys, os

from db import get_connection

# database setup
load_dotenv()
UID = os.getenv("uid")

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
def get_folders():
    folders_from_db = []
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, id, color
                FROM folders
                WHERE user_id = %s
                ORDER BY name
            """, (UID,))
            folders_from_db = cur.fetchall()  # list of tuples (name, id, color)

    # optionally, prepend "all" and append "uncategorized" if needed
    folders_from_db.insert(0, ("all", None, None))
    folders_from_db.append(("uncategorized", None, "#ebe6e8"))

    return folders_from_db

def add_task(add_task_input, folder_dropdown, task_list):
    text = add_task_input.text().strip()
    if not text:
        return
    
    # get current folder selection
    folder_id, folder_color = folder_dropdown.currentData() or (None, "#ebe6e8")

    # insert into tasks table
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (user_id, title, folder_id) VALUES (%s, %s, %s) RETURNING id, completed;",
                (UID, text, folder_id)
            )
            task_id, completed = cur.fetchone()
            conn.commit()

    # add to UI
    item = QListWidgetItem(text)
    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
    item.setCheckState(Qt.CheckState.Checked if completed else Qt.CheckState.Unchecked)
    item.setData(Qt.ItemDataRole.UserRole, task_id) # store db id
    item.setData(Qt.ItemDataRole.UserRole + 1, folder_color) # store folder color
    task_list.addItem(item)

    add_task_input.clear()

def fetch_tasks():
    # fetch all tasks for current user with optional folder color
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT t.id, t.title, t.completed, t.folder_id, f.color "
                "FROM tasks t LEFT JOIN folders f ON t.folder_id = f.id "
                "WHERE t.user_id = %s;",
                (UID,)
            )
            tasks = cur.fetchall()
    return tasks  # list of tuples: (id, title, completed, folder_id, color)

def populate_task_list(task_list):
    # fill a QListWidget with tasks from db
    for task_id, title, completed, folder_id, color in fetch_tasks():
        item = QListWidgetItem(title)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if completed else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, task_id)
        item.setData(Qt.ItemDataRole.UserRole + 1, color)
        task_list.addItem(item)

def update_task_completion(task_id, completed):
    # update a task's completed status in db
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET completed = %s WHERE id = %s;",
                (completed, task_id)
            )
            conn.commit()

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

def show_folder_menu(folder_list, pos, colors, CircleDelegate):
    item = folder_list.itemAt(pos)
    if not item:
        return

    # prevent change of "all" and "uncategorized"
    if item.text() in ["all", "uncategorized"]:
        return

    menu = QMenu()
    delete_action = menu.addAction("Delete folder")
    change_color_action = menu.addAction("Change color")
    rename_action = menu.addAction("Rename folder")  # new action
    action = menu.exec(folder_list.mapToGlobal(pos))

    row = folder_list.row(item)

    if action == delete_action:
        # remove from database
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM folders WHERE user_id = %s AND name = %s",
                    (UID, item.text())
                )
                conn.commit()

        # remove from UI and colors list
        folder_list.takeItem(row)
        colors.pop(row)
        folder_list.setItemDelegate(CircleDelegate(colors, folder_list))

    elif action == change_color_action:
        # pick a new color
        color = QColorDialog.getColor()
        if color.isValid():
            new_color = color.name()

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE folders SET color = %s WHERE user_id = %s AND name = %s",
                        (new_color, UID, item.text())
                    )
                    conn.commit()
        
        colors[row] = new_color
        folder_list.setItemDelegate(CircleDelegate(colors, folder_list))

    elif action == rename_action:
        # prompt for new name
        new_name, ok = QInputDialog.getText(folder_list, "rename Folder", "new folder name:", text=item.text())
        if ok and new_name.strip():
            new_name = new_name.strip()

            # update database
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE folders SET name = %s WHERE user_id = %s AND name = %s",
                        (new_name, UID, item.text())
                    )
                    conn.commit()

            # update UI
            item.setText(new_name)

def pick_color(set_color_callback):
    color = QColorDialog.getColor()
    if color.isValid():
        set_color_callback(color.name())

def add_folder(user_id, folder_name, color, folder_list, color_list, CircleDelegate):
    folder_name = folder_name.strip()
    if not folder_name:
        return

    # add folder to DB
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO folders (user_id, name, color) VALUES (%s, %s, %s) RETURNING id;",
                (user_id, folder_name, color)
            )
            conn.commit()
    
    # appearance update
    item = QListWidgetItem(folder_name)
    folder_list.insertItem(folder_list.count() - 1, item)

    color_list.insert(folder_list.count() - 2, color)
    folder_list.setItemDelegate(CircleDelegate(color_list, folder_list))