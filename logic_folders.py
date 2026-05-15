from PyQt6.QtWidgets import (
    QListWidgetItem, QMenu, QMessageBox, QColorDialog, QInputDialog
)
from PyQt6.QtCore import Qt
from db import get_user_client


# ---------- Client ----------
def get_client():
    return get_user_client()


# ---------- Dropdown refresh ----------
def refresh_folder_dropdown(folder_dropdown, folder_list, colors):
    folder_dropdown.clear()

    for i in range(folder_list.count()):
        item = folder_list.item(i)

        if item.text() == "All":
            continue

        color = colors[i] if i < len(colors) else "#ebe6e8"

        folder_dropdown.addItem(
            item.text(),
            userData=(item.data(Qt.ItemDataRole.UserRole), color)
        )


# ---------- Folders — DB ----------
def get_folders(uid):
    client = get_client()

    response = (
        client.table("folders")
        .select("name,id,color")
        .eq("user_id", uid)
        .order("name")
        .execute()
    )

    folders = [(f["name"], f["id"], f["color"]) for f in (response.data or [])]

    folders.insert(0, ("All", None, None))
    folders.append(("Uncategorized", None, "#ebe6e8"))

    return folders


def add_folder(
    folder_input,
    color,
    folder_list,
    color_list,
    CircleDelegate,
    folder_dropdown,
    uid
):
    folder_name = folder_input.text().strip()

    if not folder_name:
        return

    client = get_client()

    res = client.table("folders").insert({
        "user_id": uid,
        "name": folder_name,
        "color": color
    }).execute()

    if not res.data:
        return

    folder_id = res.data[0]["id"]

    insert_row = folder_list.count() - 1

    item = QListWidgetItem(folder_name)
    item.setData(Qt.ItemDataRole.UserRole, folder_id)

    folder_list.insertItem(insert_row, item)
    color_list.insert(insert_row, color)

    folder_list.setItemDelegate(CircleDelegate(color_list, folder_list))

    refresh_folder_dropdown(folder_dropdown, folder_list, color_list)

    folder_input.clear()

    folder_list.viewport().update()


# ---------- Folder context menu ----------
def show_folder_menu(
    folder_list,
    pos,
    colors,
    CircleDelegate,
    folder_dropdown,
    uid,
    refresh_tasks_callback=None
):
    item = folder_list.itemAt(pos)

    if not item or item.text() in ["All", "Uncategorized"]:
        return

    client = get_client()

    folder_name = item.text()
    row = folder_list.row(item)

    menu = QMenu()

    delete_action = menu.addAction("Delete folder")
    change_color_action = menu.addAction("Change color")
    rename_action = menu.addAction("Rename folder")

    action = menu.exec(folder_list.mapToGlobal(pos))

    # ---------- DELETE ----------
    if action == delete_action:

        msg = QMessageBox(folder_list)
        msg.setWindowTitle("Delete folder")
        msg.setText("Manage tasks in folder")

        delete_tasks_btn = msg.addButton(
            "Delete all tasks",
            QMessageBox.ButtonRole.DestructiveRole
        )

        move_tasks_btn = msg.addButton(
            "Move to uncategorized",
            QMessageBox.ButtonRole.ActionRole
        )

        cancel_btn = msg.addButton(QMessageBox.StandardButton.Cancel)

        msg.exec()

        if msg.clickedButton() == cancel_btn:
            return

        folder_id = item.data(Qt.ItemDataRole.UserRole)

        if msg.clickedButton() == delete_tasks_btn:
            client.table("tasks") \
                .delete() \
                .eq("folder_id", folder_id) \
                .execute()

        elif msg.clickedButton() == move_tasks_btn:
            client.table("tasks") \
                .update({"folder_id": None}) \
                .eq("folder_id", folder_id) \
                .execute()

        client.table("folders") \
            .delete() \
            .eq("id", folder_id) \
            .execute()

        folder_list.takeItem(row)

        if row < len(colors):
            colors.pop(row)

        folder_list.setItemDelegate(
            CircleDelegate(colors, folder_list)
        )

        refresh_folder_dropdown(
            folder_dropdown,
            folder_list,
            colors
        )

        folder_list.clearSelection()
        folder_list.setCurrentRow(0)

        folder_list.viewport().update()

        if refresh_tasks_callback:
            refresh_tasks_callback()

    # ---------- CHANGE COLOR ----------
    elif action == change_color_action:

        color = QColorDialog.getColor()

        if color.isValid():

            new_color = color.name()

            client.table("folders") \
                .update({"color": new_color}) \
                .eq("id", item.data(Qt.ItemDataRole.UserRole)) \
                .execute()

            colors[row] = new_color

            folder_list.setItemDelegate(
                CircleDelegate(colors, folder_list)
            )

            refresh_folder_dropdown(
                folder_dropdown,
                folder_list,
                colors
            )

            folder_list.viewport().update()

    # ---------- RENAME ----------
    elif action == rename_action:

        new_name, ok = QInputDialog.getText(
            folder_list,
            "Rename Folder",
            "New folder name:",
            text=item.text()
        )

        if ok and new_name.strip():

            new_name = new_name.strip()

            client.table("folders") \
                .update({"name": new_name}) \
                .eq("id", item.data(Qt.ItemDataRole.UserRole)) \
                .execute()

            item.setText(new_name)

            refresh_folder_dropdown(
                folder_dropdown,
                folder_list,
                colors
            )

            folder_list.viewport().update()