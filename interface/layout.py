from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon, QFontMetrics
from PyQt6.QtCore import Qt

# scale font to target width
def scale_font_to_width(font, text, target_width):
    lines = text.split("\n")
    size = 1
    f = font

    while True:
        f.setPointSize(size)
        widest = max(QFontMetrics(f).horizontalAdvance(line) for line in lines)
        if widest > target_width:
            f.setPointSize(size - 1 if size > 1 else 1)
            break
        size += 1
    return f

# scales text size
def scale_text(widget, width, percent=0.7):
    if hasattr(widget, "text_label"):
        text = widget.text_label.text()
        target_widget = widget.text_label
    elif hasattr(widget, "text"):
        text = widget.text()
        target_widget = widget
    else:
        return

    target_width = int(width * percent)
    # pass the QFont
    scaled_font = scale_font_to_width(target_widget.font(), text, target_width)
    target_widget.setFont(scaled_font)

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
def scale_buttons(buttons, left_width):
    if not buttons:
        return

    # find the longest text
    def get_text(btn):
        if hasattr(btn, "text_label"):
            return btn.text_label.text()
        return btn.text()

    max_text_length = max(len(get_text(btn)) for btn in buttons)
    target_text_width = int(left_width * 0.55)  # 55% of panel

    for btn in buttons:
        # scale font
        font = btn.text_label.font() if hasattr(btn, "text_label") else btn.font()
        text_for_scaling = 'W' * max_text_length
        scaled_font = scale_font_to_width(font, text_for_scaling, target_text_width)

        if hasattr(btn, "text_label"):
            btn.text_label.setFont(scaled_font)
            btn.scale_icon(left_width)
        else:
            btn.setFont(scaled_font)

        # fixed size
        btn.setFixedWidth(int(left_width * 0.8))
        btn.setFixedHeight(int(left_width * 0.2))