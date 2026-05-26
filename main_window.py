import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QMenu
)
from PySide6.QtGui import QIcon
from PySide6 import QtCore
import database as db
import image_utils as img
from artist_dialog import ArtistDialog
from album_dialog import AlbumDialog
from rating_dialog import RatingDialog
from artist_albums_dialog import ArtistAlbumsDialog
from album_rating_view import AlbumRatingViewDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Музыкальный рейтинг")
        self.setMinimumSize(1000, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        btn_layout = QHBoxLayout()
        self.btn_artists = QPushButton("Артисты")
        self.btn_albums = QPushButton("Альбомы")
        self.btn_rate = QPushButton("Оценить")
        self.btn_artists.clicked.connect(lambda: self.switch_mode("artists"))
        self.btn_albums.clicked.connect(lambda: self.switch_mode("albums"))
        self.btn_rate.clicked.connect(self.open_rating)
        btn_layout.addWidget(self.btn_artists)
        btn_layout.addWidget(self.btn_albums)
        btn_layout.addWidget(self.btn_rate)
        layout.addLayout(btn_layout)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск (по артисту, альбому или треку)...")
        self.search_edit.textChanged.connect(self.refresh)
        layout.addWidget(self.search_edit)

        self.btn_add = QPushButton("+ Добавить альбом")
        self.btn_add.clicked.connect(self.add_album)
        self.btn_add.setVisible(False)
        layout.addWidget(self.btn_add)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QtCore.QSize(64, 64))
        self.list_widget.setSpacing(5)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_click)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_widget)

        self.current_mode = "artists"
        self.refresh()

    def switch_mode(self, mode):
        self.current_mode = mode
        self.btn_add.setVisible(mode == "albums")
        self.refresh()

    def refresh(self):
        query = self.search_edit.text().strip().lower()
        self.list_widget.clear()
        if self.current_mode == "artists":
            artists = db.get_all_artists()
            for artist_id, name, photo_path in artists:
                if query in name.lower():
                    item = QListWidgetItem()
                    pixmap = img.load_scaled_image(photo_path, size=64)
                    item.setIcon(QIcon(pixmap))
                    item.setText(name)
                    item.setData(QtCore.Qt.UserRole, {"id": artist_id, "type": "artist"})
                    self.list_widget.addItem(item)
        else:
            albums = db.search_albums(query)
            for album_id, title, year, cover_path, rating in albums:
                item = QListWidgetItem()
                pixmap = img.load_scaled_image(cover_path, size=64)
                item.setIcon(QIcon(pixmap))
                text = title
                if year:
                    text += f" ({year})"
                if rating is not None:
                    text += f" ★ {rating:.2f}"
                item.setText(text)
                item.setData(QtCore.Qt.UserRole, {"id": album_id, "type": "album"})
                self.list_widget.addItem(item)

    def show_context_menu(self, position):
        item = self.list_widget.itemAt(position)
        if not item:
            return
        data = item.data(QtCore.Qt.UserRole)
        menu = QMenu()
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")
        action = menu.exec_(self.list_widget.mapToGlobal(position))
        if action == edit_action:
            self.edit_item(data)
        elif action == delete_action:
            self.delete_item(data)

    def edit_item(self, data):
        if data["type"] == "artist":
            dialog = ArtistDialog(data["id"], self)
            if dialog.exec():
                self.refresh()
        else:
            dialog = AlbumDialog(data["id"], self)
            if dialog.exec():
                self.refresh()

    def delete_item(self, data):
        if data["type"] == "artist":
            reply = QMessageBox.question(
                self, "Удаление",
                f"Удалить артиста и все его альбомы?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                db.delete_artist(data["id"])
                self.refresh()
        else:
            reply = QMessageBox.question(
                self, "Удаление",
                "Удалить альбом и все его оценки?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                db.delete_album(data["id"])
                self.refresh()

    def on_item_double_click(self, item):
        data = item.data(QtCore.Qt.UserRole)
        if data["type"] == "artist":
            dialog = ArtistAlbumsDialog(data["id"], item.text(), self)
            dialog.exec()
        else:
            dialog = AlbumRatingViewDialog(data["id"], self)
            dialog.exec()

    def add_album(self):
        dialog = AlbumDialog(album_id=None, parent=self)
        if dialog.exec():
            self.refresh()

    def open_rating(self):
        dialog = RatingDialog(self)
        if dialog.exec():
            self.refresh()