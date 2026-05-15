from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from interface import layout
import logic_folders
import logic_tasks
import db
from interface.tasks import FolderPanel, TasksPanel
from interface.profile import ProfilePanel


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("A-Track")
        self.setWindowIcon(QIcon(logic_tasks.path("assets/icon/logo.png")))

        screen_width = QGuiApplication.primaryScreen().geometry().width()
        self.left_width = screen_width // 6

        # ---------- Panels ----------
        self.left = QWidget()
        self.right = QWidget()
        self.left.setObjectName("leftPanel")
        self.right.setObjectName("rightPanel")

        # ---------- Left Layout ----------
        self.left_layout = QVBoxLayout(self.left)
        self.left_layout.setSpacing(20)
        self.left_layout.setContentsMargins(0, 20, 0, 20)

        self.header = QLabel("A-TRACK")
        self.header.setObjectName("headerLabel")
        self.left_layout.addWidget(self.header, alignment=Qt.AlignmentFlag.AlignLeft)

        # Folder panel placeholder (filled after login)
        self.folder_panel_widget = None

        self.left_layout.addStretch()

        self.logout_button = QPushButton("Log Out")
        self.logout_button.setObjectName("logoutButton")
        self.logout_button.clicked.connect(self.handle_logout)
        self.left_layout.addWidget(self.logout_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ---------- Right Layout ----------
        right_layout = QVBoxLayout(self.right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()

        # Index 0 — login screen
        self.profile_panel = ProfilePanel()
        self.profile_panel.loginSucceeded.connect(self.show_tasks_panel)
        self.stacked_widget.addWidget(self.profile_panel)

        # Index 1+ — TasksPanel (dynamic)
        right_layout.addWidget(self.stacked_widget)

        # ---------- Split Layout ----------
        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(0)
        split_layout.addWidget(self.left, 1)
        split_layout.addWidget(self.right, 5)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(split_layout)

        layout.scale_text(self.header, int(self.left_width * 0.6), 0.7)
        layout.scale_buttons([self.logout_button], self.left_width)

        self.logout_button.hide()

        # Check for existing session
        if db.has_valid_session():
            uid = db.get_uid()
            self._build_panels(uid)
        else:
            self.stacked_widget.setCurrentIndex(0)

    # ---------- Build Panels ----------
    def _build_panels(self, uid):
        # Remove old TasksPanel if any
        while self.stacked_widget.count() > 1:
            self.stacked_widget.removeWidget(self.stacked_widget.widget(1))

        # Remove old FolderPanel from left if any
        if self.folder_panel_widget is not None:
            self.left_layout.removeWidget(self.folder_panel_widget)
            self.folder_panel_widget.deleteLater()
            self.folder_panel_widget = None

        folders_from_db = logic_folders.get_folders(uid)
        colors = [f[2] or QColor(0, 0, 0, 0) for f in folders_from_db]

        # Build FolderPanel, reusing the already-scaled header font/height
        folder_panel = FolderPanel(
            uid, folders_from_db, colors, self.left_width,
            header_font=self.header.font(),
            header_height=self.header.sizeHint().height(),
        )
        self.left_layout.insertWidget(1, folder_panel, stretch=1)
        self.folder_panel_widget = folder_panel

        # Build TasksPanel (right panel, full width)
        tasks_panel = TasksPanel(uid, folder_panel)
        self.stacked_widget.addWidget(tasks_panel)
        self.stacked_widget.setCurrentIndex(1)
        self.logout_button.show()

        # Re-assert maximized geometry after layout changes settle
        QTimer.singleShot(0, self.showMaximized)

    # ---------- Show Tasks Panel ----------
    def show_tasks_panel(self):
        uid = db.get_uid()
        if not uid:
            return
        self._build_panels(uid)

    # ---------- Handle Logout ----------
    def handle_logout(self):
        db.logout()
        self.profile_panel.reset_login_form()
        self.logout_button.hide()

        # Remove all panels except login screen
        while self.stacked_widget.count() > 1:
            self.stacked_widget.removeWidget(self.stacked_widget.widget(1))

        # Remove folder panel from left side
        if self.folder_panel_widget is not None:
            self.left_layout.removeWidget(self.folder_panel_widget)
            self.folder_panel_widget.deleteLater()
            self.folder_panel_widget = None

        self.stacked_widget.setCurrentIndex(0)