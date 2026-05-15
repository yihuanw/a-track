from PyQt6.QtWidgets import (
    QListWidgetItem, QDialog, QVBoxLayout, QCalendarWidget,
    QTimeEdit, QDialogButtonBox, QInputDialog, QMenu
)
from PyQt6.QtCore import Qt, QDateTime, QTime
from PyQt6.QtGui import QPixmap, QPainter, QColor, QTextCharFormat
from PyQt6.QtSvg import QSvgRenderer
from db import get_user_client
import sys
import os


# ---------- Client ----------
def get_client():
    return get_user_client()


# ---------- Path helper ----------
def path(*paths):
    base = getattr(sys, "frozen", False) and sys._MEIPASS or os.path.dirname(__file__)
    return os.path.join(base, *paths)


# ---------- SVG recoloring ----------
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


# ---------- Color picker ----------
def pick_color(set_color_callback):
    from PyQt6.QtWidgets import QColorDialog
    color = QColorDialog.getColor()
    if color.isValid():
        set_color_callback(color.name())


# ---------- Deadline selection calendar ----------
def pick_deadline(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Set deadline")
    layout = QVBoxLayout(dialog)

    calendar = QCalendarWidget()
    time_edit = QTimeEdit()
    time_edit.setDisplayFormat("HH:mm")
    time_edit.setTime(QTime(23, 59))

    weekend_format = QTextCharFormat()
    weekend_format.setForeground(QColor("#cf8085"))
    calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
    calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok |
        QDialogButtonBox.StandardButton.Cancel
    )

    layout.addWidget(calendar)
    layout.addWidget(time_edit)
    layout.addWidget(buttons)

    result = {"deadline": None}

    def accept():
        result["deadline"] = QDateTime(calendar.selectedDate(), time_edit.time())
        dialog.accept()

    buttons.accepted.connect(accept)
    buttons.rejected.connect(dialog.reject)
    dialog.exec()
    return result["deadline"]


# ---------- Tasks — DB ----------
def add_task(add_task_input, folder_dropdown, task_list, uid, deadline_qdt=None):
    text = add_task_input.text().strip()
    if not text:
        return

    folder_id, folder_color = folder_dropdown.currentData() or (None, "#ebe6e8")
    client = get_client()

    payload = {"user_id": uid, "title": text, "folder_id": folder_id}
    if deadline_qdt:
        payload["deadline"] = deadline_qdt.toUTC().toString(Qt.DateFormat.ISODate)

    response = client.table("tasks").insert(payload).execute()
    if not response.data:
        return

    task_data = response.data[0]
    item = QListWidgetItem(task_data["title"])
    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
    item.setCheckState(
        Qt.CheckState.Checked if task_data.get("completed") else Qt.CheckState.Unchecked
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

    return [
        (row["id"], row["title"], row["completed"],
         row.get("folder_id"), (row.get("folders") or {}).get("color"))
        for row in response.data or []
    ]


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
        dt = QDateTime.fromString(deadline, Qt.DateFormat.ISODate).toLocalTime() if deadline else None
        tasks.append((row, dt))

    tasks.sort(key=lambda x: (x[1] is not None, x[1] or QDateTime()))

    for row, deadline_dt in tasks:
        item = QListWidgetItem(row["title"])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(
            Qt.CheckState.Checked if row.get("completed") else Qt.CheckState.Unchecked
        )
        item.setData(Qt.ItemDataRole.UserRole, row["id"])
        item.setData(Qt.ItemDataRole.UserRole + 1, (row.get("folders") or {}).get("color"))
        item.setData(Qt.ItemDataRole.UserRole + 2, deadline_dt)
        task_list.addItem(item)


def populate_task_list_from_data(task_list, tasks_data, show_completed=True):
    task_list.clear()
    for task_id, title, completed, folder_id, folder_color in tasks_data:
        if not show_completed and completed:
            continue
        item = QListWidgetItem(title)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if completed else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, task_id)
        item.setData(Qt.ItemDataRole.UserRole + 1, folder_color)
        item.setData(Qt.ItemDataRole.UserRole + 2, None)
        task_list.addItem(item)


def update_task_completion(task_id, completed):
    get_client().table("tasks") \
        .update({"completed": completed}) \
        .eq("id", task_id) \
        .execute()


def delete_completed_tasks(uid, folder_id="All"):
    client = get_client()
    query = client.table("tasks").delete().eq("user_id", uid).eq("completed", True)

    if folder_id == "All":
        pass
    elif folder_id is None:
        query = query.is_("folder_id", None)
    else:
        query = query.eq("folder_id", folder_id)

    query.execute()


# ---------- Task context menu ----------
def show_task_menu(task_list, pos, folder_list):
    item = task_list.itemAt(pos)
    if not item:
        return

    client = get_client()
    menu = QMenu()
    delete_action = menu.addAction("Delete task")
    change_folder_action = menu.addAction("Change folder")
    change_deadline_action = menu.addAction("Change deadline")
    change_title_action = menu.addAction("Change title")

    action = menu.exec(task_list.mapToGlobal(pos))

    if action == delete_action:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            client.table("tasks").delete().eq("id", task_id).execute()
        task_list.takeItem(task_list.row(item))

    elif action == change_folder_action:
        if folder_list is None:
            return
        folders = [
            (folder_list.item(i).text(), folder_list.item(i).data(Qt.ItemDataRole.UserRole))
            for i in range(folder_list.count())
            if folder_list.item(i).text() != "All"
        ]
        if not folders:
            return

        choice, ok = QInputDialog.getItem(
            task_list, "Change Task Folder", "Select new folder:",
            [f[0] for f in folders], 0, False
        )
        if ok:
            sel_name, sel_id = next(f for f in folders if f[0] == choice)
            task_id = item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                client.table("tasks").update({"folder_id": sel_id}).eq("id", task_id).execute()
                for i in range(folder_list.count()):
                    if folder_list.item(i).text() == sel_name:
                        delegate = folder_list.itemDelegate()
                        if delegate and hasattr(delegate, "colors"):
                            item.setData(Qt.ItemDataRole.UserRole + 1, delegate.colors[i])
                            task_list.viewport().update()
                        break

    elif action == change_deadline_action:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if not task_id:
            return
        new_deadline = pick_deadline(task_list)
        if new_deadline is None:
            return
        client.table("tasks").update({
            "deadline": new_deadline.toUTC().toString(Qt.DateFormat.ISODate)
        }).eq("id", task_id).execute()
        item.setData(Qt.ItemDataRole.UserRole + 2, new_deadline)
        task_list.viewport().update()

    elif action == change_title_action:
        new_title, ok = QInputDialog.getText(
            task_list, "Change Task Title", "New title:", text=item.text()
        )
        if ok and new_title.strip():
            task_id = item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                client.table("tasks").update({"title": new_title.strip()}).eq("id", task_id).execute()
            item.setText(new_title.strip())