from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QPushButton, QFileDialog, QHBoxLayout, QLabel,
)

from ui.modern_combo import ModernComboBox

GENRES = [
    "Поп", "Рок", "Хип-хоп", "Рэп", "Электронная музыка", "Джаз",
    "Блюз", "Соул", "R&B", "Фанк", "Метал", "Панк", "Инди",
    "Альтернатива", "Классическая музыка", "Фолк", "Кантри", "Регги",
    "Пост-рок", "Другое",
]


class ArtistFormPage(QWidget):
    back_requested = Signal()
    save_requested = Signal(dict)

    def __init__(self, artist=None, parent=None):
        super().__init__(parent)
        self.artist = artist
        self.setObjectName("EditorPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        top = QHBoxLayout()
        back = QPushButton("← Назад")
        back.clicked.connect(self.back_requested.emit)
        top.addWidget(back)
        title = QLabel("Изменить исполнителя" if artist else "Добавить исполнителя")
        title.setObjectName("PageTitle")
        top.addWidget(title)
        top.addStretch()
        root.addLayout(top)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.name = QLineEdit()
        self.age = QSpinBox()
        self.age.setRange(0, 150)
        self.age.setSpecialValueText("")
        self.age.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.age.setValue(0)

        self.region = ModernComboBox()
        self.region.addItems(["", "RU", "WW"])

        self.genre = ModernComboBox()
        self.genre.setEditable(True)
        self.genre.addItem("")
        self.genre.addItems(GENRES)

        self.photo = QLineEdit()
        self.photo.setPlaceholderText("Необязательно")
        photo_row = QHBoxLayout()
        photo_row.addWidget(self.photo, 1)
        browse = QPushButton("Выбрать…")
        browse.clicked.connect(self._choose_photo)
        photo_row.addWidget(browse)

        form.addRow("Имя", self.name)
        form.addRow("Возраст", self.age)
        form.addRow("Страна", self.region)
        form.addRow("Основной жанр", self.genre)
        form.addRow("Фото", photo_row)
        root.addLayout(form)
        root.addStretch(1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.back_requested.emit)
        save = QPushButton("Сохранить")
        save.clicked.connect(self._save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        root.addLayout(buttons)

        if artist:
            self.name.setText(artist["name"])
            if artist["age"] is not None:
                self.age.setValue(artist["age"])
            self.region.setCurrentText(artist["region"] or "")
            self.genre.setCurrentText(artist["main_genre"] or "")
            self.photo.setText(artist["photo_path"] or "")

        self.name.setFocus()

    def _choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "",
            "Изображения (*.png *.jpg *.jpeg *.webp *.bmp);;Все файлы (*)",
        )
        if path:
            self.photo.setText(path)

    def _save(self):
        name = self.name.text().strip()
        if not name:
            self.name.setFocus()
            return
        self.save_requested.emit({
            "name": name,
            "photo_path": self.photo.text().strip() or None,
            "age": self.age.value() or None,
            "main_genre": self.genre.currentText().strip() or None,
            "region": self.region.currentText().strip() or None,
        })
