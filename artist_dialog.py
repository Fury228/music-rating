import os
import shutil
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QLabel, QPushButton, QFileDialog, QMessageBox, QComboBox, QHBoxLayout
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
import database as db
import image_utils as img
from custom_dialogs import show_question
from PySide6.QtGui import QIntValidator

class ArtistDialog(QDialog):
    def __init__(self, artist_id=None, parent=None):
        super().__init__(parent)
        self.artist_id = artist_id
        self.setWindowTitle("Редактирование артиста" if artist_id else "Новый артист")
        self.setModal(True)
        self.setMinimumWidth(450)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        layout.addRow("Имя:", self.name_edit)

        self.age_edit = QLineEdit()
        self.age_edit.setPlaceholderText("необязательно")
        self.age_edit.setValidator(QIntValidator(0, 120))
        layout.addRow("Возраст:", self.age_edit)

        genre_layout = QHBoxLayout()
        self.genre_combo = QComboBox()
        self.genre_combo.setEditable(True)
        self.load_genres()
        genre_layout.addWidget(self.genre_combo, 1)
        self.info_btn = QLabel("ⓘ")
        self.info_btn.setToolTip("Необязательно. Будет использоваться вместо автоматического подбора")
        self.info_btn.setStyleSheet("color: #6a6a6a; font-weight: bold; font-size: 14px;")
        genre_layout.addWidget(self.info_btn)
        layout.addRow("Основной жанр:", genre_layout)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(128, 128)
        self.preview_label.setScaledContents(True)
        layout.addRow("Фото:", self.preview_label)

        self.select_btn = QPushButton("Выбрать изображение...")
        self.select_btn.clicked.connect(self.select_image)
        layout.addRow(self.select_btn)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.confirm_cancel)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        self.photo_path = None

        if artist_id:
            self.load_data()

    def load_genres(self):
        import sqlite3
        conn = sqlite3.connect(db.DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT genre FROM albums WHERE genre IS NOT NULL AND genre != ''")
        genres = [row[0] for row in cur.fetchall()]
        conn.close()
        self.genre_combo.clear()
        for g in genres:
            self.genre_combo.addItem(g)

    def load_data(self):
        row = db.get_artist_by_id(self.artist_id)
        if row:
            _, name, photo_path, age, main_genre = row
            self.name_edit.setText(name or "")
            if age:
                self.age_edit.setText(str(age))
            if main_genre:
                idx = self.genre_combo.findText(main_genre)
                if idx >= 0:
                    self.genre_combo.setCurrentIndex(idx)
                else:
                    self.genre_combo.setEditText(main_genre)
            if not main_genre:
                auto_genre = db.get_most_common_genre_for_artist(self.artist_id)
                if auto_genre:
                    idx = self.genre_combo.findText(auto_genre)
                    if idx >= 0:
                        self.genre_combo.setCurrentIndex(idx)
                    else:
                        self.genre_combo.setEditText(auto_genre)
                    self.genre_combo.setToolTip(f"Автоопределённый жанр: {auto_genre}")
            self.photo_path = photo_path
            if self.photo_path:
                pix = img.load_scaled_image(self.photo_path, size=128)
                self.preview_label.setPixmap(pix)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.photo_path = file_path
            pix = img.load_scaled_image(self.photo_path, size=128)
            self.preview_label.setPixmap(pix)

    def save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя артиста")
            return
        if self.artist_id is None and db.artist_exists(name):
            QMessageBox.warning(self, "Ошибка", "Артист с таким именем уже существует.")
            return
        if not show_question(self, "Подтверждение", "Сохранить изменения?"):
            return
        age_text = self.age_edit.text().strip()
        age = int(age_text) if age_text.isdigit() else None
        main_genre = self.genre_combo.currentText().strip() or None
        db.add_or_update_artist(self.artist_id, name, self.photo_path, age, main_genre)
        self.accept()

    def confirm_cancel(self):
        if show_question(self, "Подтверждение", "Отменить изменения? Все несохранённые данные будут потеряны."):
            self.reject()