from PyQt6.QtWidgets import (
    QListWidgetItem, QMenu, QMessageBox, QColorDialog, QInputDialog
)
from PyQt6.QtCore import Qt
from db import get_user_client


# ---------- Client ----------
def get_client():
    return get_user_client()


# ---------- Folders — DB ----------
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


# ---------- Folder context menu ----------
def show_folder_menu(folder_list, pos, colors, CircleDelegate, folder_dropdown, uid):
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

    if action == delete_action:
        msg = QMessageBox(folder_list)
        msg.setWindowTitle("Delete folder")
        msg.setText("Manage tasks in folder")
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
            client.table("tasks").update({"folder_id": None}).eq("folder_id", folder_id).execute()

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
            client.table("folders").update({"color": new_color}) \
                .eq("user_id", uid).eq("name", item.text()).execute()
            colors[row] = new_color
            folder_list.setItemDelegate(CircleDelegate(colors, folder_list))

    elif action == rename_action:
        new_name, ok = QInputDialog.getText(
            folder_list, "Rename Folder", "New folder name:", text=item.text()
        )
        if ok and new_name.strip():
            client.table("folders").update({"name": new_name.strip()}) \
                .eq("user_id", uid).eq("name", item.text()).execute()
            item.setText(new_name.strip())