from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QFileDialog,
    QHBoxLayout, QGroupBox, QMessageBox,
)

from ui.modern_combo import ModernComboBox

GENRES = [
    "Поп", "Рок", "Хип-хоп", "Рэп", "Электронная музыка", "Джаз",
    "Блюз", "Соул", "R&B", "Фанк", "Метал", "Панк", "Инди",
    "Альтернатива", "Классическая музыка", "Фолк", "Кантри", "Регги",
    "Пост-рок", "Другое",
]


class AlbumFormPage(QWidget):
    back_requested = Signal()
    save_requested = Signal(dict)

    def __init__(self, artist_service, album=None, parent=None):
        super().__init__(parent)
        self.artist_service = artist_service
        self.album = album
        self.setObjectName("EditorPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        top = QHBoxLayout()
        back = QPushButton("← Назад")
        back.clicked.connect(self.back_requested.emit)
        top.addWidget(back)
        title = QLabel("Изменить альбом" if album else "Добавить альбом")
        title.setObjectName("PageTitle")
        top.addWidget(title)
        top.addStretch()
        root.addLayout(top)

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
        root.addLayout(form)

        root.addWidget(QLabel("Исполнители"))
        self.artist_list = QListWidget()
        self.artist_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.artist_list.setMinimumHeight(90)
        self.artist_list.setMaximumHeight(150)
        root.addWidget(self.artist_list)

        tracks_box = QGroupBox("Треки")
        tracks_layout = QVBoxLayout(tracks_box)
        self.tracks = QListWidget()
        tracks_layout.addWidget(self.tracks, 1)
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
        root.addWidget(tracks_box, 1)

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

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.back_requested.emit)
        save = QPushButton("Сохранить")
        save.clicked.connect(self._validate_and_save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        root.addLayout(buttons)
        self.title.setFocus()

    def _choose_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "",
            "Изображения (*.png *.jpg *.jpeg *.webp *.bmp);;Все файлы (*)",
        )
        if path:
            self.cover.setText(path)

    def _insert_track(self, number, title):
        item = QListWidgetItem(f"{number:02d}  {title}")
        item.setData(Qt.ItemDataRole.UserRole, (number, title))
        self.tracks.addItem(item)

    def _add_track(self):
        title = self.track_title.text().strip()
        number = self.track_number.value()
        if not title:
            return
        for i in range(self.tracks.count()):
            existing = self.tracks.item(i).data(Qt.ItemDataRole.UserRole)
            if existing and existing[0] == number:
                QMessageBox.warning(self, "Трек", f"Номер трека {number} уже используется.")
                return
        self._insert_track(number, title)
        self.track_title.clear()
        self.track_number.setValue(min(number + 1, 999))
        self.tracks.sortItems()

    def _remove_track(self):
        row = self.tracks.currentRow()
        if row >= 0:
            self.tracks.takeItem(row)

    def _validate_and_save(self):
        title = self.title.text().strip()
        if not title:
            QMessageBox.warning(self, "Альбом", "Введите название альбома.")
            self.title.setFocus()
            return
        if not self.artist_list.selectedItems():
            QMessageBox.warning(self, "Альбом", "Выберите хотя бы одного исполнителя.")
            return

        tracks = []
        for i in range(self.tracks.count()):
            value = self.tracks.item(i).data(Qt.ItemDataRole.UserRole)
            if value:
                tracks.append((value[1], value[0]))
        tracks.sort(key=lambda x: x[1])

        self.save_requested.emit({
            "title": title,
            "artist_ids": [
                item.data(Qt.ItemDataRole.UserRole)
                for item in self.artist_list.selectedItems()
            ],
            "year": self.year.value() or None,
            "genre": self.genre.currentText().strip() or None,
            "region": self.region.currentText().strip() or None,
            "cover_path": self.cover.text().strip() or None,
            "tracks": tracks,
        })
