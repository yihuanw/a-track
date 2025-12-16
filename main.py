import sys
from PyQt5.QtWidgets import QApplication
from ui import MainWindow

app = QApplication(sys.argv)

window = MainWindow()

# apply QSS
with open("style.qss", "r") as f:
    app.setStyleSheet(f.read())

window.showMaximized()

sys.exit(app.exec_())