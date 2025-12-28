from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem, QColorDialog, QMenu, QInputDialog
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
def get_folders(uid):
    client = get_client()
    response = client.table("folders").select("name,id,color").eq("user_id", uid).order("name").execute()
    folders = [(f["name"], f["id"], f["color"]) for f in (response.data or [])]
    folders.insert(0, ("all", None, None))
    folders.append(("uncategorized", None, "#ebe6e8"))
    return folders

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


def populate_task_list(task_list, uid, folder_id="all"):
    task_list.clear()

    client = get_user_client()
    query = client.table("tasks").select("id, title, completed, folder_id, folders(color)").eq("user_id", uid)

    if folder_id == "all":
        # no additional filter, show all tasks
        pass
    elif folder_id is None:
        # show uncategorized tasks
        query = query.is_("folder_id", None)
    else:
        # show tasks for specific folder
        query = query.eq("folder_id", folder_id)

    response = query.execute()

    for row in response.data or []:
        item = QListWidgetItem(row["title"])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if row["completed"] else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, row["id"])
        item.setData(Qt.ItemDataRole.UserRole + 1, (row.get("folders") or {}).get("color"))
        task_list.addItem(item)

def update_task_completion(task_id, completed):
    client = get_client()
    client.table("tasks").update({"completed": completed}).eq("id", task_id).execute()

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

def show_folder_menu(folder_list, pos, colors, CircleDelegate, uid):
    item = folder_list.itemAt(pos)
    if not item or item.text() in ["all", "uncategorized"]:
        return

    client = get_client()
    menu = QMenu()
    delete_action = menu.addAction("Delete folder")
    change_color_action = menu.addAction("Change color")
    rename_action = menu.addAction("Rename folder")
    action = menu.exec(folder_list.mapToGlobal(pos))
    row = folder_list.row(item)

    if action == delete_action:
        client.table("folders").delete().eq("user_id", uid).eq("name", item.text()).execute()
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

def pick_color(set_color_callback):
    color = QColorDialog.getColor()
    if color.isValid():
        set_color_callback(color.name())

def add_folder(folder_input, color, folder_list, color_list, CircleDelegate, folder_dropdown, uid):
    folder_name = folder_input.text().strip()
    if not folder_name:
        return
    folder_input.clear()

    client = get_client()
    client.table("folders").insert({
        "user_id": uid,
        "name": folder_name,
        "color": color
    }).execute()

    item = QListWidgetItem(folder_name)
    folder_list.insertItem(folder_list.count() - 1, item)
    color_list.insert(folder_list.count() - 2, color)
    folder_list.setItemDelegate(CircleDelegate(color_list, folder_list))

    if folder_dropdown:
        folder_dropdown.insertItem(folder_dropdown.count() - 1, folder_name, userData=(None, color))