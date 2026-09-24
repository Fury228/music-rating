from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea,
    QGridLayout, QFrame, QComboBox
)

from ui.widgets import ImageTileCard
from ui.modern_combo import ModernComboBox


class LibraryPage(QWidget):
    album_selected = Signal(int)
    filters_changed = Signal()
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Библиотека")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()

        self.search = QLineEdit()
        self.search.setFixedWidth(340)
        self.search.setPlaceholderText("Поиск по названию, исполнителю и треку…")
        self.search.textChanged.connect(self.search_changed.emit)
        header.addWidget(self.search)
        layout.addLayout(header)

        filters = QHBoxLayout()
        filters.setSpacing(8)
        self.year_filter = self._combo("Год")
        self.rating_filter = self._combo("Оценка")
        self.artist_filter = self._combo("Исполнитель")
        self.participant_count_filter = self._combo("Участники")
        self.participant_filter = self._combo("Оценщик")
        self.genre_filter = self._combo("Жанр")
        self.region_filter = self._combo("Регион")
        for combo in (self.year_filter, self.rating_filter, self.artist_filter, self.participant_count_filter, self.participant_filter, self.genre_filter, self.region_filter):
            combo.popup_closed.connect(self.filters_changed.emit)
            filters.addWidget(combo)
        filters.addStretch()
        layout.addLayout(filters)

        self.count = QLabel()
        self.count.setObjectName("Muted")
        layout.addWidget(self.count)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(2, 2, 2, 16)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(16)

        scroll.setWidget(self.container)
        layout.addWidget(scroll, 1)

    @staticmethod
    def _combo(label):
        combo = ModernComboBox()
        combo.setMinimumWidth(125)
        combo.setProperty("filter_label", label)
        combo.addItem(label, None)
        return combo

    def set_filter_options(self, options):
        self._fill(self.year_filter, [(str(y), y) for y in options["years"]])
        self._fill(self.rating_filter, [
            ("Без оценки", "unrated"),
            ("≥ 5.0", 5.0), ("≥ 6.0", 6.0), ("≥ 7.0", 7.0),
            ("≥ 8.0", 8.0), ("≥ 9.0", 9.0), ("≥ 10.0", 10.0),
        ])
        self._fill(self.artist_filter, [(row["name"], row["id"]) for row in options["artists"]])
        self._fill(self.participant_count_filter, [(str(n), n) for n in options.get("participant_counts", [])])
        self._fill(self.participant_filter, [(row["name"], row["id"]) for row in options["participants"]])
        self._fill(self.genre_filter, [(g, g) for g in options["genres"]])
        self._fill(self.region_filter, [(r, r) for r in options.get("regions", [])])

    @staticmethod
    def _fill(combo, values):
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(combo.property("filter_label") or "Все", None)
        for text, data in values:
            combo.addItem(text, data)
        index = combo.findData(current)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def filters(self):
        return {
            "year": self.year_filter.currentData(),
            "rating": self.rating_filter.currentData(),
            "artist_id": self.artist_filter.currentData(),
            "participant_count": self.participant_count_filter.currentData(),
            "participant_id": self.participant_filter.currentData(),
            "genre": self.genre_filter.currentData(),
            "region": self.region_filter.currentData(),
        }

    def set_albums(self, albums):
        # Переиспользуем карточки вместо массового deleteLater()/создания новых
        # QWidget. Это заметно уменьшает перестройку layout/backing store при фильтрации.
        cards = getattr(self, "_card_pool", [])

        # Снимаем карточки с layout, но не уничтожаем их. Они остаются дочерними
        # self.container и могут быть безопасно возвращены в layout позже.
        for card in cards:
            self.grid.removeWidget(card)
            card.setVisible(False)
            card.stop_animations()

        while len(cards) < len(albums):
            card = ImageTileCard(
                0, "", None, "album", parent=self.container, rating=None
            )
            card.clicked.connect(self.album_selected.emit)
            cards.append(card)

        for index, row in enumerate(albums):
            card = cards[index]
            card.update_card(
                row["id"], row["title"], row["cover_path"],
                "album", row["rating_average"]
            )
            card.setVisible(True)
            self.grid.addWidget(card, index // 5, index % 5)

        self._card_pool = cards
        self.count.setText(f"Альбомов: {len(albums)}")
        self.grid.invalidate()
        self.container.updateGeometry()
        self.container.update()
