import os
import shutil
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QLabel, QPushButton, QFileDialog, QMessageBox,
    QSpinBox, QListWidget, QListWidgetItem, QHBoxLayout, QVBoxLayout, QWidget, QInputDialog
)
from PySide6.QtCore import Qt
import database as db
import image_utils as img

class AlbumDialog(QDialog):
    def __init__(self, album_id=None, parent=None):
        super().__init__(parent)
        self.album_id = album_id
        self.setWindowTitle("Редактирование альбома" if album_id else "Новый альбом")
        self.setModal(True)
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)

        form_widget = QWidget()
        form = QFormLayout(form_widget)

        self.title_edit = QLineEdit()
        form.addRow("Название альбома:", self.title_edit)

        self.year_edit = QSpinBox()
        self.year_edit.setRange(1900, 2100)
        self.year_edit.setSpecialValueText("")
        form.addRow("Год:", self.year_edit)

        self.genre_edit = QLineEdit()
        form.addRow("Жанр:", self.genre_edit)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(128, 128)
        self.cover_label.setScaledContents(True)
        form.addRow("Обложка:", self.cover_label)

        self.select_cover_btn = QPushButton("Выбрать обложку...")
        self.select_cover_btn.clicked.connect(self.select_cover)
        form.addRow(self.select_cover_btn)

        layout.addWidget(form_widget)

        layout.addWidget(QLabel("Исполнители:"))
        self.artists_list = QListWidget()
        self.artists_list.setSelectionMode(QListWidget.MultiSelection)
        self.load_artists()
        layout.addWidget(self.artists_list)

        btn_add_artist = QPushButton("+ Новый исполнитель")
        btn_add_artist.clicked.connect(self.add_new_artist)
        layout.addWidget(btn_add_artist)

        layout.addWidget(QLabel("Треки:"))
        self.tracks_list = QListWidget()
        self.tracks_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.tracks_list.itemDoubleClicked.connect(self.edit_track)
        layout.addWidget(self.tracks_list)

        track_buttons = QHBoxLayout()
        add_track_btn = QPushButton("Добавить трек")
        add_track_btn.clicked.connect(self.add_track)
        remove_track_btn = QPushButton("Удалить выбранные")
        remove_track_btn.clicked.connect(self.remove_tracks)
        track_buttons.addWidget(add_track_btn)
        track_buttons.addWidget(remove_track_btn)
        layout.addLayout(track_buttons)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if self.album_id:
            delete_btn = QPushButton("Удалить альбом")
            delete_btn.clicked.connect(self.delete_album)
            btn_layout.addWidget(delete_btn)

        self.cover_path = None
        self.selected_artist_ids = []

        if album_id:
            self.load_data()

    def load_artists(self):
        artists = db.get_all_artists()
        self.artists_list.clear()
        for artist_id, name, photo_path in artists:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, artist_id)
            self.artists_list.addItem(item)

    def load_data(self):
        data = db.get_album_by_id(self.album_id)
        if not data:
            return
        _, title, year, genre, cover_path, _ = data
        self.title_edit.setText(title or "")
        self.year_edit.setValue(year or 0)
        self.genre_edit.setText(genre or "")
        self.cover_path = cover_path
        if cover_path:
            pix = img.load_scaled_image(cover_path, size=128)
            self.cover_label.setPixmap(pix)

        album_artists = db.get_album_artists(self.album_id)
        artist_ids = [a[0] for a in album_artists]
        for i in range(self.artists_list.count()):
            item = self.artists_list.item(i)
            artist_id = item.data(Qt.UserRole)
            if artist_id in artist_ids:
                item.setSelected(True)

        tracks = db.get_tracks_by_album(self.album_id)
        for track_id, title, number in tracks:
            item = QListWidgetItem(f"{number}. {title}")
            item.setData(Qt.UserRole, {"id": track_id, "number": number, "title": title})
            self.tracks_list.addItem(item)

    def add_new_artist(self):
        name, ok = QInputDialog.getText(self, "Новый исполнитель", "Имя исполнителя:")
        if ok and name.strip():
            db.add_or_update_artist(None, name.strip(), None)
            self.load_artists()
            for i in range(self.artists_list.count()):
                if self.artists_list.item(i).text() == name.strip():
                    self.artists_list.item(i).setSelected(True)
                    break

    def add_track(self):
        title, ok = QInputDialog.getText(self, "Новый трек", "Название трека:")
        if ok and title.strip():
            number = self.tracks_list.count() + 1
            item = QListWidgetItem(f"{number}. {title.strip()}")
            item.setData(Qt.UserRole, {"id": None, "number": number, "title": title.strip()})
            self.tracks_list.addItem(item)
            self.renumber_tracks()

    def remove_tracks(self):
        for item in self.tracks_list.selectedItems():
            row = self.tracks_list.row(item)
            self.tracks_list.takeItem(row)
        self.renumber_tracks()

    def renumber_tracks(self):
        for i in range(self.tracks_list.count()):
            item = self.tracks_list.item(i)
            data = item.data(Qt.UserRole)
            data["number"] = i + 1
            item.setData(Qt.UserRole, data)
            item.setText(f"{i+1}. {data['title']}")

    def select_cover(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать обложку", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.cover_path = file_path
            pix = img.load_scaled_image(self.cover_path, size=128)
            self.cover_label.setPixmap(pix)

    def save(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите название альбома")
            return
        year = self.year_edit.value() if self.year_edit.value() != 0 else None
        genre = self.genre_edit.text().strip() or None

        selected = self.artists_list.selectedItems()
        artist_ids = [item.data(Qt.UserRole) for item in selected]
        if not artist_ids:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одного исполнителя")
            return

        new_album_id = db.add_or_update_album(self.album_id, title, year, genre, self.cover_path, artist_ids)

        tracks = []
        for i in range(self.tracks_list.count()):
            item = self.tracks_list.item(i)
            data = item.data(Qt.UserRole)
            tracks.append((data["title"], data["number"]))
        db.save_tracks(new_album_id, tracks)

        self.accept()
    
    def edit_track(self, item):
        from PySide6.QtWidgets import QInputDialog
        data = item.data(Qt.UserRole)
        new_title, ok = QInputDialog.getText(self, "Редактировать трек", "Новое название:", text=data["title"])
        if ok and new_title.strip():
            data["title"] = new_title.strip()
            item.setData(Qt.UserRole, data)
            item.setText(f"{data['number']}. {data['title']}")
    
    def delete_album(self):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Удаление", "Удалить альбом и все его оценки?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db.delete_album(self.album_id)
            self.accept()