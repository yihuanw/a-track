from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem, QColorDialog, QMenu, QInputDialog, QMessageBox
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from db import get_user_client
import sys, os

# database
_cached_client = get_user_client()  # cache the client once

def get_client():
    global _cached_client
    if _cached_client is None:
        _cached_client = get_user_client()
    return _cached_client

# repath for pyinstaller
def path(*paths):
    base = getattr(sys, "frozen", False) and sys._MEIPASS or os.path.dirname(__file__)
    return os.path.join(base, *paths)

# --------------------------- task.py functions ---------------------------
# fetches all folders for a user
def get_folders(uid):
    client = get_client()
    response = client.table("folders").select("name,id,color").eq("user_id", uid).order("name").execute()
    folders = [(f["name"], f["id"], f["color"]) for f in (response.data or [])]
    folders.insert(0, ("all", None, None))
    folders.append(("uncategorized", None, "#ebe6e8"))
    return folders

# adds a new folder to the database and updates the folder list and dropdown UI
def add_folder(folder_input, color, folder_list, color_list, CircleDelegate, folder_dropdown, uid):
    folder_name = folder_input.text().strip()
    if not folder_name:
        return
    folder_input.clear()

    client = get_client()
    res = client.table("folders").insert({
        "user_id": uid,
        "name": folder_name,
        "color": color
    }).execute()

    folder_id = res.data[0]["id"]

    # add to folder_list
    item = QListWidgetItem(folder_name)
    item.setData(Qt.ItemDataRole.UserRole, folder_id)  # store the id
    folder_list.insertItem(folder_list.count() - 1, item)
    color_list.insert(folder_list.count() - 2, color)
    folder_list.setItemDelegate(CircleDelegate(color_list, folder_list))

    # add to dropdown
    if folder_dropdown:
        folder_dropdown.addItem(folder_name, userData=(folder_id, color))

# adds a new task to the database and updates the task list UI
def add_task(add_task_input, folder_dropdown, task_list, uid):
    text = add_task_input.text().strip()
    if not text:
        return

    folder_id, folder_color = folder_dropdown.currentData() or (None, "#ebe6e8")
    client = get_client()
    response = client.table("tasks").insert({
        "user_id": uid,
        "title": text,
        "folder_id": folder_id
    }).execute()

    if not response.data:
        return

    task_data = response.data[0]
    item = QListWidgetItem(task_data["title"])
    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
    item.setCheckState(Qt.CheckState.Checked if task_data.get("completed") else Qt.CheckState.Unchecked)
    item.setData(Qt.ItemDataRole.UserRole, task_data["id"])
    item.setData(Qt.ItemDataRole.UserRole + 1, folder_color)
    task_list.addItem(item)
    add_task_input.clear()

# retrieves all tasks for a user, including folder color info
def fetch_tasks(uid):
    client = get_client()
    response = client.table("tasks")\
        .select("id, title, completed, folder_id, folders(color)")\
        .eq("user_id", uid).execute()
    
    tasks = []
    for row in response.data or []:
        folder_color = None
        if row.get("folders"):
            folder_color = row["folders"].get("color")
        tasks.append((
            row["id"],
            row["title"],
            row["completed"],
            row.get("folder_id"),
            folder_color
        ))
    return tasks

# populates the task list UI for a given user and folder
def populate_task_list(task_list, uid, folder_id="all", show_completed=True):
    task_list.clear()

    client = get_user_client()
    query = client.table("tasks").select("id, title, completed, folder_id, folders(color)").eq("user_id", uid)

    if folder_id == "all":
        pass
    elif folder_id is None:
        query = query.is_("folder_id", None)
    else:
        query = query.eq("folder_id", folder_id)

    response = query.execute()

    for row in response.data or []:
        if not show_completed and row.get("completed"):
            continue  # skip completed tasks if toggle off
        item = QListWidgetItem(row["title"])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if row["completed"] else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, row["id"])
        item.setData(Qt.ItemDataRole.UserRole + 1, (row.get("folders") or {}).get("color"))
        task_list.addItem(item)

# updates the completed status of a task in the database
def update_task_completion(task_id, completed):
    client = get_client()
    client.table("tasks").update({"completed": completed}).eq("id", task_id).execute()

# shows a context menu for folders with options to delete, rename, or change color
def show_folder_menu(folder_list, pos, colors, CircleDelegate, folder_dropdown, uid):
    item = folder_list.itemAt(pos)
    if not item or item.text() in ["all", "uncategorized"]:
        return

    client = get_client()
    folder_name = item.text()
    row = folder_list.row(item)

    menu = QMenu()
    delete_action = menu.addAction("Delete folder")
    change_color_action = menu.addAction("Change color")
    rename_action = menu.addAction("Rename folder")

    action = menu.exec(folder_list.mapToGlobal(pos))

    if action == delete_action:
        msg = QMessageBox(folder_list)
        msg.setWindowTitle("Delete folder")
        msg.setText("Manage tasks in '{folder_name}")
        delete_tasks_btn = msg.addButton("Delete all tasks", QMessageBox.ButtonRole.DestructiveRole)
        move_tasks_btn = msg.addButton("Move to uncategorized", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg.addButton(QMessageBox.StandardButton.Cancel)
        msg.exec()

        if msg.clickedButton() == cancel_btn:
            return

        folder_res = (
            client.table("folders")
            .select("id")
            .eq("user_id", uid)
            .eq("name", folder_name)
            .execute()
        )

        if not folder_res.data:
            return

        folder_id = folder_res.data[0]["id"]

        if msg.clickedButton() == delete_tasks_btn:
            client.table("tasks").delete().eq("folder_id", folder_id).execute()

        elif msg.clickedButton() == move_tasks_btn:
            client.table("tasks").update(
                {"folder_id": None}
            ).eq("folder_id", folder_id).execute()

        client.table("folders").delete().eq("id", folder_id).execute()

        for i in range(folder_dropdown.count()):
            if folder_dropdown.itemText(i) == folder_name:
                folder_dropdown.removeItem(i)
                break

        folder_list.takeItem(row)
        colors.pop(row)
        folder_list.setItemDelegate(CircleDelegate(colors, folder_list))

    elif action == change_color_action:
        color = QColorDialog.getColor()
        if color.isValid():
            new_color = color.name()
            client.table("folders").update({"color": new_color}).eq("user_id", uid).eq("name", item.text()).execute()
            colors[row] = new_color
            folder_list.setItemDelegate(CircleDelegate(colors, folder_list))
            
    elif action == rename_action:
        new_name, ok = QInputDialog.getText(folder_list, "Rename Folder", "New folder name:", text=item.text())
        if ok and new_name.strip():
            client.table("folders").update({"name": new_name.strip()}).eq("user_id", uid).eq("name", item.text()).execute()
            item.setText(new_name.strip())

# shows a context menu for tasks with option to delete
def show_task_menu(task_list, pos):
    item = task_list.itemAt(pos)
    if not item:
        return

    client = get_client()
    menu = QMenu()
    delete_action = menu.addAction("Delete task")
    action = menu.exec(task_list.mapToGlobal(pos))
    if action == delete_action:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            client.table("tasks").delete().eq("id", task_id).execute()
        task_list.takeItem(task_list.row(item))

# recolors an SVG file with the specified color and returns a QPixmap
def recolor(color, svg_path):
    renderer = QSvgRenderer(svg_path)
    size = renderer.defaultSize()
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()
    return pixmap

# opens a color picker dialog and calls a callback with the chosen color
def pick_color(set_color_callback):
    color = QColorDialog.getColor()
    if color.isValid():
        set_color_callback(color.name())