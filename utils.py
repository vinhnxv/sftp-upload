from PySide2.QtWidgets import QMessageBox


def message_box(window, title, message, icon):
    msg_box = QMessageBox(window)
    msg_box.setText(message)
    msg_box.setWindowTitle(title)
    msg_box.setIcon(icon)
    msg_box.exec()
