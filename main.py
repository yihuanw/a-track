import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QFontDatabase
from ui import MainWindow
 
app = QApplication(sys.argv)
 
QCoreApplication.setOrganizationName("a-track")
QCoreApplication.setApplicationName("a-track")
 
app.setStyle("windows11")
 
# pyinstaller
if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)
 
# apply font before creating window
font_path = os.path.join(
    base_path,
    "assets/Inter/Inter-VariableFont_opsz,wght.ttf"
)
QFontDatabase.addApplicationFont(font_path)
 
# apply QSS before  creating window so first paint
qss_path = os.path.join(base_path, "style.qss")
with open(qss_path, "r", encoding="utf-8") as f:
    app.setStyleSheet(f.read())
 
window = MainWindow()
window.showMaximized()
 
sys.exit(app.exec())