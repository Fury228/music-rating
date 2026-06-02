from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt

class ConfirmDialog(QDialog):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        btn_layout = QHBoxLayout()
        self.btn_yes = QPushButton("Да")
        self.btn_no = QPushButton("Нет")
        self.btn_yes.clicked.connect(self.accept)
        self.btn_no.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_yes)
        btn_layout.addWidget(self.btn_no)
        layout.addLayout(btn_layout)
        self.setMinimumWidth(300)

def show_question(parent, title, text):
    dlg = ConfirmDialog(parent, title, text)
    return dlg.exec() == QDialog.Accepted