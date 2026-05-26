import os
import shutil
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QLabel, QPushButton, QFileDialog, QMessageBox
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
import database as db
import image_utils as img

class ArtistDialog(QDialog):
    def __init__(self, artist_id=None, parent=None):
        super().__init__(parent)
        self.artist_id = artist_id
        self.setWindowTitle("Редактирование артиста" if artist_id else "Новый артист")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        layout.addRow("Имя:", self.name_edit)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(128, 128)
        self.preview_label.setScaledContents(True)
        layout.addRow("Фото:", self.preview_label)

        self.select_btn = QPushButton("Выбрать изображение...")
        self.select_btn.clicked.connect(self.select_image)
        layout.addRow(self.select_btn)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        layout.addRow(self.save_btn)

        self.photo_path = None

        if artist_id:
            self.load_data()

    def load_data(self):
        import sqlite3
        conn = sqlite3.connect(db.DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name, photo_path FROM artists WHERE id=?", (self.artist_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            self.name_edit.setText(row[0])
            self.photo_path = row[1]
            if self.photo_path:
                pix = img.load_scaled_image(self.photo_path, size=128)
                self.preview_label.setPixmap(pix)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            os.makedirs("imgs/artists", exist_ok=True)
            new_name = f"artist_{self.artist_id if self.artist_id else 'temp'}_{os.path.basename(file_path)}"
            dest = os.path.join("imgs/artists", new_name)
            shutil.copy2(file_path, dest)
            self.photo_path = os.path.join("artists", new_name)
            pix = img.load_scaled_image(self.photo_path, size=128)
            self.preview_label.setPixmap(pix)

    def save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя артиста")
            return
        db.add_or_update_artist(self.artist_id, name, self.photo_path)
        self.accept()