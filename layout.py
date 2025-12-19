from PyQt6.QtWidgets import QSizePolicy, QPushButton
from PyQt6.QtGui import QIcon, QFontMetrics
from PyQt6.QtCore import Qt

# helper to scale font to target width
def scale_font_to_width(widget, text, target_width):
    lines = text.split("\n")  # split into lines
    font = widget.font()
    size = 1
    while True:
        font.setPointSize(size)
        # measure widest line
        widest = max(QFontMetrics(font).horizontalAdvance(line) for line in lines)
        if widest > target_width:
            font.setPointSize(size - 1 if size > 1 else 1)
            break
        size += 1
    return font


# scales header size
def scale_header(header_label, left_width):
    target_width = int(left_width * 0.70)  # 70% of panel
    header_label.setFont(scale_font_to_width(header_label, header_label.text(), target_width))


# icon & text button
class IconTextButton(QPushButton):
    def __init__(self, icon_path, text):
        super().__init__()
        self.text_str = text
        self.icon_path = icon_path
        self.setText("")

        from PyQt6.QtWidgets import QHBoxLayout, QLabel
        self.layout = QHBoxLayout(self)

        # icon
        self.icon_label = QLabel()
        self.icon = QIcon(icon_path)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.layout.addWidget(self.icon_label)

        # text
        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.layout.addWidget(self.text_label, 1)

    def scale_icon(self, left_width):
        icon_size = int(left_width * 0.1)  # 10% of panel
        self.icon_label.setPixmap(self.icon.pixmap(icon_size, icon_size))


# scales button text based on the longest label
def scale_buttons(buttons, left_width, header_width):
    if not buttons:
        return

    # find the longest button text
    max_text_length = max(len(btn.text_str) for btn in buttons)
    target_text_width = int(left_width * 0.55)  # 55% of panel

    for btn in buttons:
        btn.text_label.setFont(scale_font_to_width(btn.text_label, 'W'*max_text_length, target_text_width))
        btn.scale_icon(left_width)
        btn.setFixedWidth(int(left_width * 0.8))
        btn.setFixedHeight(int(left_width * 0.2))