from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QFont, QFontMetrics, QIcon, QColor

from . import layout
from .delegates import CircleDelegate, SimpleSVGCheckDelegate
import logic_folders
import logic_tasks


# ---------- FolderPanel — lives in the main window's left panel ----------
class FolderPanel(QWidget):
    folderSelected = pyqtSignal(str, object)   # (folder_name, folder_id | "All" | None)

    def __init__(self, uid, folders_from_db, colors, left_width,
                 header_font=None, header_height=None, parent=None):
        super().__init__(parent)
        self.uid = uid
        self.colors = colors
        self._task_list_ref = None
        self._dropdown_ref = None

        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(10, 0, 10, 0)
        panel_layout.setSpacing(8)

        _base_font = header_font if header_font is not None else QFont()
        self.header_height = header_height if header_height is not None else QFontMetrics(_base_font).height()

        # Folder list
        self.folder_list = QListWidget()
        self.folder_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.folder_list.setObjectName("tasks_folderList")
        self.folder_list.setSpacing(3)   # slight spacing between folder items

        font = QFont(_base_font)
        font.setPointSize(int(_base_font.pointSize() * 0.75))
        self.folder_list.setFont(font)
        self.font = font

        for name, folder_id, _ in folders_from_db:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, folder_id)
            self.folder_list.addItem(item)

        self.folder_list.setItemDelegate(CircleDelegate(self.colors, self.folder_list))
        panel_layout.addWidget(self.folder_list, stretch=1)

        # Add folder row
        folder_input_layout = QHBoxLayout()
        folder_input_layout.setContentsMargins(10, 0, 10, 0)

        self.folder_input = QLineEdit()
        self.folder_input.setFixedHeight(self.header_height)
        self.folder_input.setPlaceholderText("Add folder")
        self.folder_input.setObjectName("tasks_folderInput")
        folder_input_layout.addWidget(self.folder_input)

        self.selected_color = "#ebe6e8"
        self.color_button = QPushButton()
        self.color_button.setFixedSize(self.header_height, self.header_height)
        self.color_button.setObjectName("tasks_colorButton")
        self.color_button.clicked.connect(
            lambda: logic_tasks.pick_color(
                lambda c: (setattr(self, "selected_color", c),
                           self.color_button.setStyleSheet(f"background-color: {c}"))
            )
        )

        self.folder_input.returnPressed.connect(self._add_folder)
        folder_input_layout.addWidget(self.color_button)
        panel_layout.addLayout(folder_input_layout)

        self.folder_list.currentRowChanged.connect(lambda _: self._on_folder_changed())
        self.folder_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_list.customContextMenuRequested.connect(self._on_context_menu)

    def link(self, task_list, folder_dropdown):
        self._task_list_ref = task_list
        self._dropdown_ref = folder_dropdown
        self.folder_list.setCurrentRow(0)

    def _on_folder_changed(self):
        item = self.folder_list.currentItem()
        if not item or not self._task_list_ref:
            return

        folder_name = item.text()
        folder_id = item.data(Qt.ItemDataRole.UserRole)
        show = getattr(self, "_show_completed", True)

        if folder_name == "All":
            logic_tasks.populate_task_list(self._task_list_ref, self.uid, "All", show_completed=show)
            if self._dropdown_ref:
                self._dropdown_ref.clear()
                for i in range(self.folder_list.count()):
                    it = self.folder_list.item(i)
                    if it.text() != "All":
                        self._dropdown_ref.addItem(
                            it.text(),
                            userData=(it.data(Qt.ItemDataRole.UserRole), self.colors[i])
                        )

        elif folder_name == "Uncategorized":
            logic_tasks.populate_task_list(self._task_list_ref, self.uid, None, show_completed=show)
            if self._dropdown_ref:
                self._dropdown_ref.clear()
                self._dropdown_ref.addItem("Uncategorized", userData=(None, "#ebe6e8"))

        else:
            logic_tasks.populate_task_list(self._task_list_ref, self.uid, folder_id, show_completed=show)
            if self._dropdown_ref:
                self._dropdown_ref.clear()
                self._dropdown_ref.addItem(
                    folder_name,
                    userData=(folder_id, self.colors[self.folder_list.row(item)])
                )

        self.folderSelected.emit(folder_name, folder_id)

    def refresh_tasks(self, show_completed):
        self._show_completed = show_completed
        self._on_folder_changed()

    def current_folder_id(self):
        item = self.folder_list.currentItem()
        if not item:
            return "All"
        name = item.text()
        if name == "All":
            return "All"
        if name == "Uncategorized":
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _add_folder(self):
        if self._dropdown_ref:
            logic_folders.add_folder(
                self.folder_input, self.selected_color,
                self.folder_list, self.colors,
                CircleDelegate, self._dropdown_ref, self.uid
            )

    def _on_context_menu(self, pos):

        def refresh_tasks():
            self.refresh_tasks(
                getattr(self, "_show_completed", True)
            )

        if self._dropdown_ref:
            logic_folders.show_folder_menu(
                self.folder_list,
                pos,
                self.colors,
                CircleDelegate,
                self._dropdown_ref,
                self.uid,
                refresh_tasks_callback=refresh_tasks
            )


# ---------- TasksPanel — lives in the main window's right panel ----------
class TasksPanel(QWidget):
    def __init__(self, uid, folder_panel: FolderPanel,
                 prefetch_tasks=None, parent=None):
        super().__init__(parent)

        if not uid:
            return

        self.uid = uid
        self.folder_panel = folder_panel
        self.show_completed = True
        self.selected_deadline = None

        screen = QGuiApplication.primaryScreen().geometry()
        panel_w = int(screen.width() * 5 / 6)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        font = folder_panel.font
        header_height = folder_panel.header_height

        # ---------- Task input row ----------
        task_input_layout = QHBoxLayout()
        task_input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        task_input_layout.setContentsMargins(0, int(header_height // 2), 0, 0)

        add_task_input = QLineEdit()
        add_task_input.setPlaceholderText("Add task")
        add_task_input.setFixedHeight(header_height)
        add_task_input.setFont(font)
        add_task_input.setObjectName("tasks_addTaskInput")

        folder_dropdown = QComboBox()
        folder_dropdown.setFixedHeight(header_height)
        folder_dropdown.setObjectName("tasks_folderDropdown")

        deadline_btn = QPushButton()
        deadline_btn.setIcon(QIcon(logic_tasks.path("assets/icon/calendar.png")))
        deadline_btn.setFixedSize(header_height, header_height)
        deadline_btn.setObjectName("tasks_deadlineBtn")
        deadline_btn.clicked.connect(
            lambda: setattr(self, "selected_deadline", logic_tasks.pick_deadline(self))
        )

        add_task_input.returnPressed.connect(
            lambda: logic_tasks.add_task(
                add_task_input, folder_dropdown, task_list, uid, self.selected_deadline
            )
        )

        task_input_layout.addWidget(add_task_input, stretch=1)
        task_input_layout.addWidget(folder_dropdown)
        task_input_layout.addWidget(deadline_btn)

        input_container = QWidget()
        input_container.setLayout(task_input_layout)
        input_container.setContentsMargins(
            int(panel_w * 0.05), int(header_height // 2), int(panel_w * 0.05), 0
        )
        main_layout.addWidget(input_container)

        # ---------- Task list ----------
        task_list = QListWidget()
        task_list.setFont(font)
        task_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        task_list.setObjectName("tasks_taskList")

        delegate = SimpleSVGCheckDelegate(parent=task_list)
        task_list.setItemDelegate(delegate)

        if prefetch_tasks is not None:
            logic_tasks.populate_task_list_from_data(task_list, prefetch_tasks)
        else:
            logic_tasks.populate_task_list(task_list, uid)

        task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        def refresh_current_tasks():
            folder_panel.refresh_tasks(self.show_completed)


        task_list.customContextMenuRequested.connect(
            lambda pos: logic_tasks.show_task_menu(
                task_list=task_list,
                pos=pos,
                folder_list=folder_panel.folder_list,
                uid=uid,
                current_folder_id=folder_panel.current_folder_id(),
                show_completed=self.show_completed,
                refresh_callback=refresh_current_tasks
            )
        )

        task_list_container = QWidget()
        tcl = QVBoxLayout(task_list_container)
        tcl.setContentsMargins(int(panel_w * 0.05), 8, int(panel_w * 0.05), 0)
        tcl.addWidget(task_list)
        main_layout.addWidget(task_list_container, stretch=1)

        # ---------- Bottom buttons ----------
        bottom_btn_layout = QHBoxLayout()
        bottom_btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_btn_layout.setContentsMargins(0, 0, 0, 0)

        show_completed_btn = QPushButton(
            "Hide completed tasks" if self.show_completed else "Show completed tasks"
        )
        show_completed_btn.setFixedHeight(header_height)
        show_completed_btn.setObjectName("tasks_showCompletedBtn")
        bottom_btn_layout.addWidget(show_completed_btn)

        delete_completed_btn = QPushButton("Delete completed tasks")
        delete_completed_btn.setFixedHeight(header_height)
        delete_completed_btn.setObjectName("tasks_deleteCompletedBtn")
        bottom_btn_layout.addWidget(delete_completed_btn)

        bottom_container = QWidget()
        bcl = QVBoxLayout(bottom_container)
        bcl.setContentsMargins(0, 8, 0, int(header_height // 2))
        bcl.addLayout(bottom_btn_layout)
        main_layout.addWidget(bottom_container)
        main_layout.addStretch()

        # Populate dropdown from folder_panel's list
        fl = folder_panel.folder_list
        for i in range(fl.count()):
            it = fl.item(i)
            if it.text() != "All":
                folder_dropdown.addItem(
                    it.text(),
                    userData=(it.data(Qt.ItemDataRole.UserRole), folder_panel.colors[i])
                )

        folder_panel.link(task_list, folder_dropdown)

        # ---------- Callbacks ----------
        def refresh_tasks():
            if not self.show_completed:
                folder_panel.refresh_tasks(self.show_completed)

        delegate.taskToggled.connect(refresh_tasks)

        def toggle_show_completed():
            self.show_completed = not self.show_completed
            show_completed_btn.setText(
                "Hide completed tasks" if self.show_completed else "Show completed tasks"
            )
            folder_panel.refresh_tasks(self.show_completed)

        show_completed_btn.clicked.connect(toggle_show_completed)

        def delete_completed_tasks_confirm():
            msg = QMessageBox(self)
            msg.setWindowTitle("Delete completed tasks")
            msg.setText("Are you sure you want to delete all completed tasks?")
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
            )
            msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
            if msg.exec() != QMessageBox.StandardButton.Yes:
                return
            folder_id = folder_panel.current_folder_id()
            logic_tasks.delete_completed_tasks(uid, folder_id)
            logic_tasks.populate_task_list(task_list, uid, folder_id, show_completed=self.show_completed)

        delete_completed_btn.clicked.connect(delete_completed_tasks_confirm)