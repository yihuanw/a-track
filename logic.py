from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QDateTime, QTime
from PyQt6.QtGui import QPixmap, QPainter, QColor, QTextCharFormat
from PyQt6.QtSvg import QSvgRenderer
from db import get_user_client
import sys, os


# ---------------- client ----------------
def get_client():
    return get_user_client()


# ---------------- path helper ----------------
def path(*paths):
    base = getattr(sys, "frozen", False) and sys._MEIPASS or os.path.dirname(__file__)
    return os.path.join(base, *paths)


# ---------------- folders ----------------
def get_folders(uid):
    client = get_client()
    response = client.table("folders") \
        .select("name,id,color") \
        .eq("user_id", uid) \
        .order("name") \
        .execute()

    folders = [(f["name"], f["id"], f["color"]) for f in (response.data or [])]
    folders.insert(0, ("All", None, None))
    folders.append(("Uncategorized", None, "#ebe6e8"))
    return folders


def add_folder(folder_input, color, folder_list, color_list,
               CircleDelegate, folder_dropdown, uid):

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

    item = QListWidgetItem(folder_name)
    item.setData(Qt.ItemDataRole.UserRole, folder_id)

    folder_list.insertItem(folder_list.count() - 1, item)
    color_list.insert(folder_list.count() - 2, color)

    folder_list.setItemDelegate(CircleDelegate(color_list, folder_list))

    if folder_dropdown:
        folder_dropdown.addItem(folder_name, userData=(folder_id, color))


# ---------------- tasks ----------------
def add_task(add_task_input, folder_dropdown, task_list, uid, deadline_qdt=None):
    text = add_task_input.text().strip()
    if not text:
        return

    folder_id, folder_color = folder_dropdown.currentData() or (None, "#ebe6e8")
    client = get_client()

    payload = {
        "user_id": uid,
        "title": text,
        "folder_id": folder_id
    }

    if deadline_qdt:
        payload["deadline"] = deadline_qdt.toUTC().toString(Qt.DateFormat.ISODate)

    response = client.table("tasks").insert(payload).execute()

    if not response.data:
        return

    task_data = response.data[0]

    item = QListWidgetItem(task_data["title"])
    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
    item.setCheckState(
        Qt.CheckState.Checked if task_data.get("completed")
        else Qt.CheckState.Unchecked
    )

    item.setData(Qt.ItemDataRole.UserRole, task_data["id"])
    item.setData(Qt.ItemDataRole.UserRole + 1, folder_color)
    item.setData(Qt.ItemDataRole.UserRole + 2, deadline_qdt)

    task_list.addItem(item)
    task_list.viewport().update()

    add_task_input.clear()


def fetch_tasks(uid):
    client = get_client()

    response = client.table("tasks") \
        .select("id, title, completed, folder_id, folders(color)") \
        .eq("user_id", uid) \
        .execute()

    tasks = []

    for row in response.data or []:
        folder_color = (row.get("folders") or {}).get("color")

        tasks.append((
            row["id"],
            row["title"],
            row["completed"],
            row.get("folder_id"),
            folder_color
        ))

    return tasks


def populate_task_list(task_list, uid, folder_id="All", show_completed=True):
    task_list.clear()

    client = get_client()

    query = client.table("tasks") \
        .select("id, title, completed, folder_id, folders(color), deadline") \
        .eq("user_id", uid)

    if folder_id == "All":
        pass
    elif folder_id is None:
        query = query.is_("folder_id", None)
    else:
        query = query.eq("folder_id", folder_id)

    response = query.execute()

    tasks = []

    for row in response.data or []:
        if not show_completed and row.get("completed"):
            continue

        deadline = row.get("deadline")

        if deadline:
            dt = QDateTime.fromString(deadline, Qt.DateFormat.ISODate).toLocalTime()
        else:
            dt = None

        tasks.append((row, dt))

    tasks.sort(key=lambda x: (x[1] is not None, x[1] or QDateTime()))

    for row, deadline_dt in tasks:
        item = QListWidgetItem(row["title"])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(
            Qt.CheckState.Checked if row.get("completed")
            else Qt.CheckState.Unchecked
        )

        item.setData(Qt.ItemDataRole.UserRole, row["id"])
        item.setData(Qt.ItemDataRole.UserRole + 1, (row.get("folders") or {}).get("color"))
        item.setData(Qt.ItemDataRole.UserRole + 2, deadline_dt)

        task_list.addItem(item)


# ---------------- task update ----------------
def update_task_completion(task_id, completed):
    client = get_client()
    client.table("tasks") \
        .update({"completed": completed}) \
        .eq("id", task_id) \
        .execute()


def delete_completed_tasks(uid, folder_id="All"):
    client = get_client()

    query = client.table("tasks") \
        .delete() \
        .eq("user_id", uid) \
        .eq("completed", True)

    if folder_id == "All":
        pass
    elif folder_id is None:
        query = query.is_("folder_id", None)
    else:
        query = query.eq("folder_id", folder_id)

    query.execute()