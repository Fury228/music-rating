from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QDialogButtonBox, QListWidget, QListWidgetItem, QLabel, QComboBox,
    QPushButton, QFileDialog, QHBoxLayout, QGroupBox, QMessageBox
)

from ui.modern_combo import ModernComboBox

GENRES = [
    "Поп", "Рок", "Хип-хоп", "Рэп", "Электронная музыка", "Джаз",
    "Блюз", "Соул", "R&B", "Фанк", "Метал", "Панк", "Инди",
    "Альтернатива", "Классическая музыка", "Фолк", "Кантри", "Регги",
    "Пост-рок", "Другое",
]


class AlbumDialog(QDialog):
    def __init__(self, parent, artist_service, album=None):
        super().__init__(parent)
        self.artist_service = artist_service
        self.album = album
        self.setWindowTitle("Изменить альбом" if album else "Добавить альбом")
        self.setMinimumSize(620, 760)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title = QLineEdit()
        self.year = QSpinBox()
        self.year.setRange(0, 3000)
        self.year.setSpecialValueText("")
        self.year.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.year.setValue(0)

        self.genre = ModernComboBox()
        self.genre.setEditable(True)
        self.genre.addItem("")
        self.genre.addItems(GENRES)

        self.region = ModernComboBox()
        self.region.addItems(["", "RU", "WW"])

        self.cover = QLineEdit()
        self.cover.setPlaceholderText("Необязательно")
        cover_row = QHBoxLayout()
        cover_row.addWidget(self.cover, 1)
        browse = QPushButton("Выбрать…")
        browse.clicked.connect(self._choose_cover)
        cover_row.addWidget(browse)

        form.addRow("Название", self.title)
        form.addRow("Год", self.year)
        form.addRow("Жанр", self.genre)
        form.addRow("Регион", self.region)
        form.addRow("Обложка", cover_row)
        layout.addLayout(form)

        layout.addWidget(QLabel("Исполнители"))
        self.artist_list = QListWidget()
        self.artist_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.artist_list.setMaximumHeight(130)
        layout.addWidget(self.artist_list)

        tracks_box = QGroupBox("Треки")
        tracks_layout = QVBoxLayout(tracks_box)
        self.tracks = QListWidget()
        tracks_layout.addWidget(self.tracks)

        track_controls = QHBoxLayout()
        self.track_number = QSpinBox()
        self.track_number.setRange(1, 999)
        self.track_number.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.track_number.setValue(1)
        self.track_title = QLineEdit()
        self.track_title.setPlaceholderText("Название трека")
        add_track = QPushButton("Добавить трек")
        add_track.clicked.connect(self._add_track)
        remove_track = QPushButton("Удалить выбранный")
        remove_track.clicked.connect(self._remove_track)
        track_controls.addWidget(QLabel("№"))
        track_controls.addWidget(self.track_number)
        track_controls.addWidget(self.track_title, 1)
        track_controls.addWidget(add_track)
        track_controls.addWidget(remove_track)
        tracks_layout.addLayout(track_controls)
        layout.addWidget(tracks_box, 1)

        for artist in self.artist_service.list_artists():
            item = QListWidgetItem(artist["name"])
            item.setData(Qt.ItemDataRole.UserRole, artist["id"])
            self.artist_list.addItem(item)

        if album:
            a = album["album"]
            self.title.setText(a["title"])
            if a["year"] is not None:
                self.year.setValue(a["year"])
            self.genre.setCurrentText(a["genre"] or "")
            self.region.setCurrentText(a["region"] or "")
            self.cover.setText(a["cover_path"] or "")

            selected = {x["id"] for x in album["artists"]}
            for i in range(self.artist_list.count()):
                item = self.artist_list.item(i)
                item.setSelected(item.data(Qt.ItemDataRole.UserRole) in selected)

            for track in album["tracks"]:
                self._insert_track(track["track_number"], track["title"])

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "", "Изображения (*.png *.jpg *.jpeg *.webp *.bmp);;Все файлы (*)"
        )
        if path:
            self.cover.setText(path)

    def _insert_track(self, number: int, title: str):
        item = QListWidgetItem(f"{number:02d}  {title}")
        item.setData(Qt.ItemDataRole.UserRole, (number, title))
        self.tracks.addItem(item)

    def _add_track(self):
        title = self.track_title.text().strip()
        number = self.track_number.value()
        if not title:
            QMessageBox.warning(self, "Трек", "Введите название трека.")
            return
        for i in range(self.tracks.count()):
            existing = self.tracks.item(i).data(Qt.ItemDataRole.UserRole)
            if existing and existing[0] == number:
                QMessageBox.warning(self, "Трек", f"Номер трека {number} уже используется.")
                return
        self._insert_track(number, title)
        self.track_title.clear()
        self.track_number.setValue(number + 1)
        self.tracks.sortItems()

    def _remove_track(self):
        row = self.tracks.currentRow()
        if row >= 0:
            self.tracks.takeItem(row)

    def _validate_and_accept(self):
        if not self.title.text().strip():
            QMessageBox.warning(self, "Альбом", "Введите название альбома.")
            return
        if not self.artist_list.selectedItems():
            QMessageBox.warning(self, "Альбом", "Выберите хотя бы одного исполнителя.")
            return
        self.accept()

    def data(self):
        artist_ids = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.artist_list.selectedItems()
        ]
        tracks = []
        for i in range(self.tracks.count()):
            value = self.tracks.item(i).data(Qt.ItemDataRole.UserRole)
            if value:
                # UI stores (номер, название), сервис ожидает (название, номер).
                tracks.append((value[1], value[0]))
        tracks.sort(key=lambda x: x[1])
        return {
            "title": self.title.text(),
            "artist_ids": artist_ids,
            "year": self.year.value() or None,
            "genre": self.genre.currentText().strip() or None,
            "region": self.region.currentText().strip() or None,
            "cover_path": self.cover.text() or None,
            "tracks": tracks,
        }
