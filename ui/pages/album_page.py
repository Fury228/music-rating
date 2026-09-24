from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget


class AlbumPage(QWidget):
    back_requested = Signal()
    edit_requested = Signal(int)
    rate_requested = Signal(int)
    edit_rating_requested = Signal(int)
    view_ratings_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.album_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top = QHBoxLayout()
        back = QPushButton("← Библиотека")
        back.clicked.connect(self.back_requested.emit)
        top.addWidget(back)
        top.addStretch()

        self.view_ratings_button = QPushButton("Просмотр оценок")
        self.view_ratings_button.clicked.connect(self._view_ratings)
        top.addWidget(self.view_ratings_button)

        self.edit_rating_button = QPushButton("Редактировать оценку")
        self.edit_rating_button.clicked.connect(self._edit_rating)
        top.addWidget(self.edit_rating_button)

        self.rating_button = QPushButton("Оценить альбом")
        self.rating_button.clicked.connect(self._rate)
        top.addWidget(self.rating_button)

        self.edit = QPushButton("Изменить альбом")
        self.edit.clicked.connect(self._edit)
        top.addWidget(self.edit)
        layout.addLayout(top)

        self.title = QLabel()
        self.title.setObjectName("PageTitle")
        layout.addWidget(self.title)

        self.meta = QLabel()
        self.meta.setObjectName("Muted")
        layout.addWidget(self.meta)

        self.artists = QLabel()
        self.artists.setObjectName("AlbumArtists")
        layout.addWidget(self.artists)

        self.rating_summary = QLabel("Оценка ещё не выставлена")
        self.rating_summary.setObjectName("Muted")
        layout.addWidget(self.rating_summary)

        self.tracks = QListWidget()
        layout.addWidget(self.tracks, 1)

    def set_album(self, details, rating_summary=None):
        album = details["album"]
        self.album_id = album["id"]
        self.title.setText(album["title"])

        meta = []
        if album["year"] is not None:
            meta.append(str(album["year"]))
        if album["genre"]:
            meta.append(album["genre"])
        if album["region"]:
            meta.append(album["region"])
        self.meta.setText(" • ".join(meta))

        names = ", ".join(a["name"] for a in details["artists"])
        self.artists.setText(names)

        self.tracks.clear()
        for track in details["tracks"]:
            self.tracks.addItem(f'{track["track_number"]:02d}  {track["title"]}')

        has_rating = bool(rating_summary and rating_summary.get("participants", 0) > 0)
        self.rating_button.setEnabled(not has_rating)
        self.edit_rating_button.setEnabled(has_rating)
        self.view_ratings_button.setEnabled(has_rating)

        if rating_summary and rating_summary["average"] is not None:
            self.rating_summary.setText(
                f'Средняя оценка: {rating_summary["average"]:.1f} • '
                f'Участников: {rating_summary["participants"]}'
            )
        else:
            self.rating_summary.setText("Оценка ещё не выставлена")

    def _edit(self):
        if self.album_id is not None:
            self.edit_requested.emit(self.album_id)

    def _edit_rating(self):
        if self.album_id is not None:
            self.edit_rating_requested.emit(self.album_id)

    def _view_ratings(self):
        if self.album_id is not None:
            self.view_ratings_requested.emit(self.album_id)

    def _rate(self):
        if self.album_id is not None:
            self.rate_requested.emit(self.album_id)
