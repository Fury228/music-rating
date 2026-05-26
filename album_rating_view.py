import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QHeaderView, QPushButton, QMessageBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import database as db
import image_utils as img

class AlbumRatingViewDialog(QDialog):
    def __init__(self, album_id, parent=None):
        super().__init__(parent)
        self.album_id = album_id
        self.setWindowTitle("Оценки альбома")
        self.setModal(True)
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        album_info = db.get_album_by_id(album_id)
        if not album_info:
            QMessageBox.warning(self, "Ошибка", "Альбом не найден")
            self.close()
            return
        _, title, year, genre, cover_path, overall_rating = album_info
        artists = db.get_album_artists(album_id)
        artist_names = ", ".join([a[1] for a in artists])

        info_group = QGroupBox("Информация")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Название:", QLabel(title))
        info_layout.addRow("Исполнители:", QLabel(artist_names))
        if year:
            info_layout.addRow("Год:", QLabel(str(year)))
        if genre:
            info_layout.addRow("Жанр:", QLabel(genre))
        if overall_rating is not None:
            info_layout.addRow("Общая оценка:", QLabel(f"{overall_rating:.2f}"))
        if cover_path:
            pix = img.load_scaled_image(cover_path, size=128)
            cover_label = QLabel()
            cover_label.setPixmap(pix)
            info_layout.addRow("Обложка:", cover_label)
        layout.addWidget(info_group)

        rating_data = db.get_album_rating_data(album_id)
        participants = rating_data["participants"]
        tracks = rating_data["tracks"]
        ratings = rating_data["ratings"]

        if not participants:
            layout.addWidget(QLabel("Этот альбом ещё не оценён."))
        else:
            track_count = len(tracks)
            part_count = len(participants)
            table = QTableWidget(track_count, part_count)
            table.setHorizontalHeaderLabels([p[1] for p in participants])
            table.setVerticalHeaderLabels([f"{t[2]}. {t[1]}" for t in tracks])

            for i, (track_id, _, _) in enumerate(tracks):
                for j, (part_id, _) in enumerate(participants):
                    rating = ratings.get((track_id, part_id))
                    if rating is not None:
                        item = QTableWidgetItem(f"{rating:.1f}")
                        item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(i, j, item)
                    else:
                        table.setItem(i, j, QTableWidgetItem("-"))

            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            layout.addWidget(QLabel("Оценки треков участниками:"))
            layout.addWidget(table)

            participant_avgs = []
            for j, (part_id, part_name) in enumerate(participants):
                total = 0.0
                count = 0
                for i, (track_id, _, _) in enumerate(tracks):
                    rating = ratings.get((track_id, part_id))
                    if rating is not None:
                        total += rating
                        count += 1
                avg = total / count if count > 0 else 0.0
                participant_avgs.append((part_name, avg))
            avg_text = ", ".join([f"{name}: {avg:.2f}" for name, avg in participant_avgs])
            layout.addWidget(QLabel(f"Средние по участникам: {avg_text}"))

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)