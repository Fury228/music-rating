import sqlite3
from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QMessageBox
from PySide6.QtGui import QIcon
from PySide6 import QtCore
import database as db
import image_utils as img
from album_rating_view import AlbumRatingViewDialog

class ArtistAlbumsDialog(QDialog):
    def __init__(self, artist_id, artist_name, parent=None):
        super().__init__(parent)
        self.artist_id = artist_id
        self.setWindowTitle(f"Альбомы: {artist_name}")
        self.setMinimumSize(600, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QtCore.QSize(64, 64))
        self.list_widget.setSpacing(5)
        self.list_widget.itemDoubleClicked.connect(self.on_album_double_click)
        layout.addWidget(self.list_widget)

        self.load_albums()

    def load_albums(self):
        conn = sqlite3.connect(db.DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.title, a.year, a.cover_path, a.overall_rating
            FROM albums a
            JOIN album_artists aa ON a.id = aa.album_id
            WHERE aa.artist_id = ?
            ORDER BY a.title
        """, (self.artist_id,))
        albums = cur.fetchall()
        conn.close()

        self.list_widget.clear()
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
            item.setData(QtCore.Qt.UserRole, album_id)
            self.list_widget.addItem(item)

    def on_album_double_click(self, item):
        album_id = item.data(QtCore.Qt.UserRole)
        dialog = AlbumRatingViewDialog(album_id, self)
        dialog.exec()