import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QMenu
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
from custom_dialogs import show_question

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Музыкальный рейтинг")
        self.setWindowIcon(QIcon(resource_path("app_icon.ico")))
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

        add_buttons_layout = QHBoxLayout()
        self.btn_add_artist = QPushButton("+ Добавить артиста")
        self.btn_add_artist.clicked.connect(self.add_artist)
        self.btn_add_artist.setVisible(False)
        self.btn_add_album = QPushButton("+ Добавить альбом")
        self.btn_add_album.clicked.connect(self.add_album)
        self.btn_add_album.setVisible(False)
        add_buttons_layout.addWidget(self.btn_add_artist)
        add_buttons_layout.addWidget(self.btn_add_album)
        add_buttons_layout.addStretch()
        layout.addLayout(add_buttons_layout)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск (по артисту, альбому или треку)...")
        self.search_edit.textChanged.connect(self.refresh)
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QtCore.QSize(64, 64))
        self.list_widget.setSpacing(5)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_click)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_widget)

        self.current_mode = "artists"
        self.switch_mode("artists")
        self.refresh()

    def switch_mode(self, mode):
        self.current_mode = mode
        self.btn_add_artist.setVisible(mode == "artists")
        self.btn_add_album.setVisible(mode == "albums")
        self.refresh()

    def refresh(self):
        query = self.search_edit.text().strip().lower()
        self.list_widget.clear()
        if self.current_mode == "artists":
            artists = db.get_all_artists()
            for artist_id, name, photo_path, age, main_genre in artists:
                if query in name.lower():
                    item = QListWidgetItem()
                    pixmap = img.load_scaled_image(photo_path, size=64)
                    item.setIcon(QIcon(pixmap))
                    lines = [name]
                    if age:
                        lines[0] = f"{name}, {age}"
                    if main_genre:
                        lines.append(main_genre)
                    display_text = "\n".join(lines)

                    item.setText(display_text)
                    item.setData(QtCore.Qt.UserRole, {
                        "id": artist_id,
                        "type": "artist",
                        "name": name
                    })
                    self.list_widget.addItem(item)
        else:
            albums = db.search_albums(query)
            for album_id, title, year, cover_path, rating in albums:
                item = QListWidgetItem()
                pixmap = img.load_scaled_image(cover_path, size=64)
                item.setIcon(QIcon(pixmap))
                top_text = title
                if year:
                    top_text += f" ({year})"
                if rating is not None:
                    top_text += f" ★ {rating:.2f}"
                artists = db.get_album_artists(album_id)
                artist_names = ", ".join([a[1] for a in artists]) if artists else ""
                if artist_names:
                    display_text = f"{top_text}\n{artist_names}"
                else:
                    display_text = top_text
                item.setText(display_text)
                item.setData(QtCore.Qt.UserRole, {"id": album_id, "type": "album"})
                self.list_widget.addItem(item)

    def add_artist(self):
        dialog = ArtistDialog(artist_id=None, parent=self)
        if dialog.exec():
            self.refresh()

    def add_album(self):
        dialog = AlbumDialog(album_id=None, parent=self)
        if dialog.exec():
            self.refresh()

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
            if show_question(self, "Удаление", "Удалить артиста и все его альбомы?"):
                db.delete_artist(data["id"])
                self.refresh()
        else:
            if show_question(self, "Удаление", "Удалить альбом и все его оценки?"):
                db.delete_album(data["id"])
                self.refresh()

    def on_item_double_click(self, item):
        data = item.data(QtCore.Qt.UserRole)
        if data["type"] == "artist":
            dialog = ArtistAlbumsDialog(data["id"], data["name"], self)
            dialog.exec()
        else:
            dialog = AlbumRatingViewDialog(data["id"], self)
            dialog.exec()

    def open_rating(self):
        dialog = RatingDialog(self)
        if dialog.exec():
            self.refresh()