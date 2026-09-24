from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QDialogButtonBox, QComboBox, QPushButton, QFileDialog, QHBoxLayout
)

from ui.modern_combo import ModernComboBox

GENRES = [
    "Поп", "Рок", "Хип-хоп", "Рэп", "Электронная музыка", "Джаз",
    "Блюз", "Соул", "R&B", "Фанк", "Метал", "Панк", "Инди",
    "Альтернатива", "Классическая музыка", "Фолк", "Кантри", "Регги",
    "Пост-рок", "Другое",
]


class ArtistDialog(QDialog):
    def __init__(self, parent=None, artist=None):
        super().__init__(parent)
        self.artist = artist
        self.setWindowTitle("Изменить исполнителя" if artist else "Добавить исполнителя")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
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
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if artist:
            self.name.setText(artist["name"])
            if artist["age"] is not None:
                self.age.setValue(artist["age"])
            self.region.setCurrentText(artist["region"] or "")
            self.genre.setCurrentText(artist["main_genre"] or "")
            self.photo.setText(artist["photo_path"] or "")

    def _choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "", "Изображения (*.png *.jpg *.jpeg *.webp *.bmp);;Все файлы (*)"
        )
        if path:
            self.photo.setText(path)

    def data(self):
        return {
            "name": self.name.text(),
            "photo_path": self.photo.text() or None,
            "age": self.age.value() or None,
            "main_genre": self.genre.currentText().strip() or None,
            "region": self.region.currentText().strip() or None,
        }
