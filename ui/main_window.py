from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QGridLayout, QStackedWidget, QMessageBox,
    QFrame, QComboBox
)

from services.artist_service import ArtistService
from services.album_service import AlbumService
from services.rating_service import RatingService
from services.participant_service import ParticipantService
from ui.pages.library_page import LibraryPage
from ui.modern_combo import ModernComboBox
from ui.pages.album_page import AlbumPage
from ui.pages.artist_form_page import ArtistFormPage
from ui.pages.album_form_page import AlbumFormPage
from ui.pages.rating_page import RatingPage
from ui.pages.rating_view_page import RatingViewPage
from ui.widgets import ImageTileCard
from ui.modern_combo import ModernComboBox


class MainWindow(QMainWindow):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.artist_service = ArtistService(conn)
        self.album_service = AlbumService(conn)
        self.rating_service = RatingService(conn)
        self.participant_service = ParticipantService(conn)

        self.setWindowTitle("MusicRating — Оценка музыки")
        self.resize(1200, 760)
        self.setMinimumSize(900, 600)
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

        self._active_form_page = None
        self._form_origin_widget = None
        self._build_ui()
        self._refresh_library()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 22, 18, 18)
        side.setSpacing(10)

        title = QLabel("MusicRating")
        title.setObjectName("AppTitle")
        side.addWidget(title)
        side.addSpacing(18)

        self.library_button = QPushButton("Библиотека")
        self.library_button.setObjectName("NavButton")
        self.library_button.clicked.connect(self.show_library)
        side.addWidget(self.library_button)

        self.artists_button = QPushButton("Исполнители")
        self.artists_button.setObjectName("NavButton")
        self.artists_button.clicked.connect(self.show_artists)
        side.addWidget(self.artists_button)

        side.addStretch()

        add_artist = QPushButton("+  Добавить исполнителя")
        add_artist.clicked.connect(self.add_artist)
        side.addWidget(add_artist)

        add_album = QPushButton("+  Добавить альбом")
        add_album.clicked.connect(self.add_album)
        side.addWidget(add_album)

        layout.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 24)

        self.pages = QStackedWidget()
        self.library_page = LibraryPage()
        self.library_page.album_selected.connect(self.open_album)
        self.library_page.search_changed.connect(self._search_albums)
        self.library_page.filters_changed.connect(self._filters_changed)
        self.pages.addWidget(self.library_page)

        self.artists_page = self._create_artists_page()
        self.pages.addWidget(self.artists_page)

        self.album_page = AlbumPage()
        self.album_page.back_requested.connect(self.show_library)
        self.album_page.edit_requested.connect(self.edit_album)
        self.album_page.rate_requested.connect(self.rate_album)
        self.album_page.edit_rating_requested.connect(self.edit_rating)
        self.album_page.view_ratings_requested.connect(self.view_ratings)
        self.pages.addWidget(self.album_page)

        content_layout.addWidget(self.pages)
        layout.addWidget(content, 1)

        self.setStyleSheet((Path(__file__).with_name("styles.qss")).read_text(encoding="utf-8"))

    def _create_artists_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Исполнители")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()

        self.artist_search = QLineEdit()
        self.artist_search.setFixedWidth(300)
        self.artist_search.setPlaceholderText("Поиск по имени, альбому и треку…")
        self.artist_search.textChanged.connect(self._search_artists)
        header.addWidget(self.artist_search)
        layout.addLayout(header)

        artist_filters = QHBoxLayout()
        self.artist_genre_filter = ModernComboBox()
        self.artist_genre_filter.setProperty("filter_label", "Жанр")
        self.artist_age_filter = ModernComboBox()
        self.artist_age_filter.setProperty("filter_label", "Возраст")
        self.artist_region_filter = ModernComboBox()
        self.artist_region_filter.setProperty("filter_label", "Страна")
        self.artist_album_count_filter = ModernComboBox()
        self.artist_album_count_filter.setProperty("filter_label", "Альбомов")
        self.artist_rating_filter = ModernComboBox()
        self.artist_rating_filter.setProperty("filter_label", "Средняя оценка")
        for combo in (self.artist_genre_filter, self.artist_age_filter, self.artist_region_filter, self.artist_album_count_filter, self.artist_rating_filter):
            combo.setMinimumWidth(125)
            combo.addItem(combo.property("filter_label"), None)
            combo.popup_closed.connect(self._artist_filters_changed)
            artist_filters.addWidget(combo)
        artist_filters.addStretch()
        layout.addLayout(artist_filters)

        self.artist_count = QLabel()
        self.artist_count.setObjectName("Muted")
        layout.addWidget(self.artist_count)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.artist_container = QWidget()
        self.artist_grid = QGridLayout(self.artist_container)
        self.artist_grid.setContentsMargins(2, 2, 2, 16)
        self.artist_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.artist_grid.setHorizontalSpacing(16)
        self.artist_grid.setVerticalSpacing(16)
        scroll.setWidget(self.artist_container)
        layout.addWidget(scroll, 1)
        return page

    def _refresh_library(self):
        self.library_page.set_filter_options(self.album_service.filter_options())
        self._apply_library_filters()

    def _apply_library_filters(self):
        query = self.library_page.search.text()
        filters = self.library_page.filters()
        if query.strip():
            albums = self.album_service.search(query, filters)
        else:
            albums = self.album_service.list_albums(filters)
        self.library_page.set_albums(albums)

    def _search_albums(self, text):
        self._apply_library_filters()

    def _filters_changed(self):
        # ModernComboBox emits this only after hidePopup() has completed.
        # Rebuild the library immediately now that the popup is no longer being painted.
        if getattr(self, "_filter_refresh_pending", False):
            return
        self._filter_refresh_pending = True
        try:
            self._apply_library_filters()
        finally:
            self._filter_refresh_pending = False

    def _artist_filters_changed(self):
        if getattr(self, "_artist_filter_refresh_pending", False):
            return
        self._artist_filter_refresh_pending = True
        try:
            self._search_artists(self.artist_search.text())
        finally:
            self._artist_filter_refresh_pending = False

    def _fill_artist_filter(self, combo, values):
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(combo.property("filter_label") or "Все", None)
        for text, data in values:
            combo.addItem(text, data)
        index = combo.findData(current)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def _refresh_artist_filters(self):
        options = self.artist_service.filter_options()
        self._fill_artist_filter(self.artist_genre_filter, [(x, x) for x in options["genres"]])
        self._fill_artist_filter(self.artist_age_filter, [(str(x), x) for x in options["ages"]])
        self._fill_artist_filter(self.artist_region_filter, [(x, x) for x in options["regions"]])
        self._fill_artist_filter(self.artist_album_count_filter, [(str(x), x) for x in options["album_counts"]])
        self._fill_artist_filter(self.artist_rating_filter, [(f"≥ {x:.1f}", x) for x in (5.0, 6.0, 7.0, 8.0, 9.0, 10.0)])

    def _artist_filters(self):
        return {
            "genre": self.artist_genre_filter.currentData(),
            "age": self.artist_age_filter.currentData(),
            "region": self.artist_region_filter.currentData(),
            "album_count": self.artist_album_count_filter.currentData(),
            "rating": self.artist_rating_filter.currentData(),
        }

    def _search_artists(self, text):
        cards = getattr(self, "_artist_card_pool", [])

        for card in cards:
            self.artist_grid.removeWidget(card)
            card.setVisible(False)
            card.stop_animations()

        rows = self.artist_service.search(text, self._artist_filters())

        while len(cards) < len(rows):
            card = ImageTileCard(0, "", None, "artist", parent=self.artist_container)
            cards.append(card)

        for index, row in enumerate(rows):
            card = cards[index]
            card.update_card(row["id"], row["name"], row["photo_path"], "artist")
            card.setVisible(True)
            self.artist_grid.addWidget(card, index // 5, index % 5)

        self._artist_card_pool = cards
        self.artist_count.setText(f"Исполнителей: {len(rows)}")
        self.artist_grid.invalidate()
        self.artist_container.updateGeometry()
        self.artist_container.update()

    def show_library(self):
        self._refresh_library()
        self.pages.setCurrentWidget(self.library_page)

    def show_artists(self):
        self.artist_search.clear()
        self._refresh_artist_filters()
        self._search_artists("")
        self.pages.setCurrentWidget(self.artists_page)

    def open_album(self, album_id):
        details = self.album_service.get_details(album_id)
        if details is None:
            QMessageBox.warning(self, "Альбом", "Альбом больше не существует.")
            self.show_library()
            return
        self.album_page.set_album(details, self.rating_service.get_summary(album_id))
        self.pages.setCurrentWidget(self.album_page)


    def _show_form_page(self, page, origin_widget):
        self._active_form_page = page
        self._form_origin_widget = origin_widget
        self.pages.addWidget(page)
        self.pages.setCurrentWidget(page)

    def _close_form_page(self, page, target_widget=None):
        if self.pages.indexOf(page) >= 0:
            self.pages.removeWidget(page)
        page.deleteLater()
        if self._active_form_page is page:
            self._active_form_page = None
        if target_widget is None:
            target_widget = self._form_origin_widget
        self._form_origin_widget = None
        if target_widget is not None:
            self.pages.setCurrentWidget(target_widget)

    def _open_rating_page(self, album_id, editing=False):
        details = self.album_service.get_details(album_id)
        if details is None:
            return
        rating_data = self.rating_service.get_rating(album_id)
        has_rating = bool(rating_data.get("participants"))
        if not editing and has_rating:
            QMessageBox.information(
                self, "Оценка",
                "Этот альбом уже оценён. Для изменения используйте «Редактировать оценку»."
            )
            return
        if editing and not has_rating:
            QMessageBox.information(
                self, "Оценка",
                "У этого альбома ещё нет сохранённой оценки."
            )
            return

        rating_album = dict(details["album"])
        rating_album["tracks"] = details["tracks"]
        page = RatingPage(
            self,
            rating_album,
            self.participant_service.list_all(),
            rating_data,
            self.participant_service,
        )
        page.back_requested.connect(lambda p=page: self._close_form_page(p, self.album_page))
        page.save_requested.connect(lambda result, p=page: self._save_rating_page(p, album_id, result))
        self._show_form_page(page, self.album_page)

    def _save_rating_page(self, page, album_id, result):
        try:
            self.rating_service.save_rating(album_id, result)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка сохранения", str(exc))
            return
        self._close_form_page(page, self.album_page)
        self.open_album(album_id)

    def rate_album(self, album_id):
        self._open_rating_page(album_id, editing=False)

    def edit_rating(self, album_id):
        self._open_rating_page(album_id, editing=True)

    def view_ratings(self, album_id):
        details = self.album_service.get_details(album_id)
        if details is None:
            return
        rating_data = self.rating_service.get_rating(album_id)
        if not rating_data.get("participants"):
            QMessageBox.information(self, "Оценки", "У этого альбома ещё нет сохранённой оценки.")
            return
        rating_album = dict(details["album"])
        rating_album["tracks"] = details["tracks"]
        page = RatingViewPage(
            rating_album,
            rating_data,
            self.rating_service.get_summary(album_id),
        )
        page.back_requested.connect(lambda p=page: self._close_form_page(p, self.album_page))
        self._show_form_page(page, self.album_page)

    def edit_album(self, album_id):
        album = self.album_service.get_details(album_id)
        if album is None:
            return
        page = AlbumFormPage(self.artist_service, album=album)
        page.back_requested.connect(lambda p=page: self._close_form_page(p, self.album_page))
        page.save_requested.connect(lambda data, p=page: self._save_album_page(p, album_id, data))
        self._show_form_page(page, self.album_page)

    def _save_album_page(self, page, album_id, data):
        try:
            self.album_service.update(album_id, **data)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка сохранения", str(exc))
            return
        self._refresh_library()
        self._close_form_page(page, self.album_page)
        self.open_album(album_id)

    def add_album(self):
        origin = self.pages.currentWidget()
        page = AlbumFormPage(self.artist_service)
        page.back_requested.connect(lambda p=page, o=origin: self._close_form_page(p, o))
        page.save_requested.connect(lambda data, p=page: self._create_album_from_page(p, data))
        self._show_form_page(page, origin)

    def _create_album_from_page(self, page, data):
        try:
            album_id = self.album_service.create(**data)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка создания", str(exc))
            return
        self._refresh_library()
        self._close_form_page(page, self.library_page)
        self.open_album(album_id)

    def add_artist(self):
        origin = self.pages.currentWidget()
        page = ArtistFormPage()
        page.back_requested.connect(lambda p=page, o=origin: self._close_form_page(p, o))
        page.save_requested.connect(lambda data, p=page: self._create_artist_from_page(p, data))
        self._show_form_page(page, origin)

    def _create_artist_from_page(self, page, data):
        try:
            self.artist_service.create(**data)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка создания", str(exc))
            return
        self._refresh_artist_filters()
        self._search_artists(self.artist_search.text())
        self._close_form_page(page, self.artists_page)
        self.pages.setCurrentWidget(self.artists_page)

