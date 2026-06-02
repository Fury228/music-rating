import os
import shutil
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QFileDialog, QMessageBox, QComboBox, QTabWidget,
    QWidget, QListWidget, QListWidgetItem, QInputDialog
)
from PySide6.QtCore import Qt
import database as db
import image_utils as img
import sqlite3
from custom_dialogs import show_question
from PySide6.QtGui import QIntValidator

class AlbumDialog(QDialog):
    def __init__(self, album_id=None, parent=None):
        super().__init__(parent)
        self.album_id = album_id
        self.setWindowTitle("Редактирование альбома" if album_id else "Новый альбом")
        self.setModal(True)
        self.setMinimumWidth(650)
        self.setMinimumHeight(550)
        self.resize(650, 550)

        main_layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.info_tab = QWidget()
        self.tab_widget.addTab(self.info_tab, "Информация")
        self.setup_info_tab()

        self.artist_tab = QWidget()
        self.tab_widget.addTab(self.artist_tab, "Исполнитель(-и)")
        self.setup_artist_tab()

        self.tracks_tab = QWidget()
        self.tab_widget.addTab(self.tracks_tab, "Треки")
        self.setup_tracks_tab()

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.confirm_cancel)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)

        self.cover_path = None
        self.selected_artist_ids = []
        self.tracks_data = []

        if album_id:
            self.load_data()

    def setup_info_tab(self):
        layout = QVBoxLayout(self.info_tab)
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(10)

        self.title_edit = QLineEdit()
        form_layout.addRow("Название альбома:", self.title_edit)

        self.year_edit = QLineEdit()
        self.year_edit.setPlaceholderText("например, 2024")
        self.year_edit.setValidator(QIntValidator(1900, 2100))
        form_layout.addRow("Год:", self.year_edit)

        self.genre_combo = QComboBox()
        self.genre_combo.setEditable(True)
        test_genres = ["Rock", "Pop", "Jazz", "Classical", "Hip Hop"]
        self.genre_combo.addItems(test_genres)
        form_layout.addRow("Жанр:", self.genre_combo)

        self.select_cover_btn = QPushButton("Выбрать обложку...")
        self.select_cover_btn.clicked.connect(self.select_cover)
        form_layout.addRow("Обложка:", self.select_cover_btn)

        layout.addWidget(form_widget)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setScaledContents(True)
        self.cover_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)

        layout.addStretch()

    def setup_artist_tab(self):
        layout = QVBoxLayout(self.artist_tab)

        top_layout = QHBoxLayout()
        self.artist_combo = QComboBox()
        self.artist_combo.setEditable(True)
        self.load_artists_into_combo()
        top_layout.addWidget(self.artist_combo, 1)
        self.btn_new_artist = QPushButton("Ещё нет нужного исполнителя?")
        self.btn_new_artist.clicked.connect(self.add_new_artist)
        top_layout.addWidget(self.btn_new_artist)
        layout.addLayout(top_layout)

        btn_layout = QHBoxLayout()
        self.btn_add_artist = QPushButton("Добавить")
        self.btn_add_artist.clicked.connect(self.add_current_artist)
        self.btn_remove_artist = QPushButton("Удалить выбранного исполнителя")
        self.btn_remove_artist.clicked.connect(self.remove_selected_artist)
        btn_layout.addWidget(self.btn_add_artist)
        btn_layout.addWidget(self.btn_remove_artist)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Выбранные исполнители:"))
        self.selected_artists_list = QListWidget()
        self.selected_artists_list.setMaximumHeight(150)
        layout.addWidget(self.selected_artists_list)

        layout.addStretch()

    def setup_tracks_tab(self):
        layout = QVBoxLayout(self.tracks_tab)

        btn_layout = QHBoxLayout()
        self.add_track_btn = QPushButton("Добавить трек")
        self.add_track_btn.clicked.connect(self.add_track)
        self.remove_tracks_btn = QPushButton("Удалить выбранное")
        self.remove_tracks_btn.clicked.connect(self.remove_selected_tracks)
        self.remove_tracks_btn.setVisible(False)
        btn_layout.addWidget(self.add_track_btn)
        btn_layout.addWidget(self.remove_tracks_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.tracks_list = QListWidget()
        self.tracks_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.tracks_list.itemSelectionChanged.connect(self.on_track_selection_changed)
        self.tracks_list.itemDoubleClicked.connect(self.edit_track)
        layout.addWidget(self.tracks_list)

        layout.addStretch()

    def load_artists_into_combo(self):
        self.artist_combo.clear()
        artists = db.get_all_artists()
        for artist in artists:
            artist_id = artist[0]
            name = artist[1]
            self.artist_combo.addItem(name, artist_id)

    def load_data(self):
        data = db.get_album_by_id(self.album_id)
        if not data:
            return
        _, title, year, genre, cover_path, _ = data
        self.title_edit.setText(title or "")
        if year:
            self.year_edit.setText(str(year))
        if genre:
            idx = self.genre_combo.findText(genre)
            if idx >= 0:
                self.genre_combo.setCurrentIndex(idx)
            else:
                self.genre_combo.setEditText(genre)
        self.cover_path = cover_path
        if cover_path:
            pix = img.load_scaled_image(cover_path, size=200)
            self.cover_label.setPixmap(pix)

        album_artists = db.get_album_artists(self.album_id)
        self.selected_artist_ids = [a[0] for a in album_artists]
        for artist_id, name, _ in album_artists:
            self.selected_artists_list.addItem(name)

        tracks = db.get_tracks_by_album(self.album_id)
        for track_id, title, number in tracks:
            self.tracks_data.append({"id": track_id, "title": title, "number": number})
        self.refresh_tracks_list()

    def refresh_tracks_list(self):
        self.tracks_list.clear()
        self.tracks_data.sort(key=lambda x: x["number"])
        for track in self.tracks_data:
            item = QListWidgetItem(f"{track['number']}. {track['title']}")
            item.setData(Qt.UserRole, track["id"])
            self.tracks_list.addItem(item)

    def on_track_selection_changed(self):
        selected = self.tracks_list.selectedItems()
        self.remove_tracks_btn.setVisible(len(selected) > 0)

    def add_track(self):
        title, ok = QInputDialog.getText(self, "Новый трек", "Название трека:")
        if ok and title.strip():
            new_number = len(self.tracks_data) + 1
            self.tracks_data.append({"id": None, "title": title.strip(), "number": new_number})
            self.refresh_tracks_list()

    def edit_track(self, item):
        idx = self.tracks_list.row(item)
        track = self.tracks_data[idx]
        new_title, ok = QInputDialog.getText(self, "Редактировать трек", "Новое название:", text=track["title"])
        if ok and new_title.strip():
            track["title"] = new_title.strip()
            self.refresh_tracks_list()

    def remove_selected_tracks(self):
        selected_items = self.tracks_list.selectedItems()
        if not selected_items:
            return
        rows = [self.tracks_list.row(it) for it in selected_items]
        rows.sort(reverse=True)
        for row in rows:
            del self.tracks_data[row]
        self.renumber_tracks()
        self.refresh_tracks_list()
        self.remove_tracks_btn.setVisible(False)

    def renumber_tracks(self):
        for i, track in enumerate(self.tracks_data):
            track["number"] = i + 1

    def select_cover(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать обложку", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.cover_path = file_path
            pix = img.load_scaled_image(self.cover_path, size=200)
            self.cover_label.setPixmap(pix)

    def add_new_artist(self):
        from artist_dialog import ArtistDialog
        dialog = ArtistDialog(artist_id=None, parent=self)
        if dialog.exec():
            self.load_artists_into_combo()
            new_artist_name = dialog.name_edit.text().strip()
            idx = self.artist_combo.findText(new_artist_name)
            if idx >= 0:
                self.artist_combo.setCurrentIndex(idx)
                self.add_current_artist()

    def add_current_artist(self):
        current_text = self.artist_combo.currentText().strip()
        current_id = self.artist_combo.currentData()
        if not current_text:
            return
        existing_names = [self.selected_artists_list.item(i).text() for i in range(self.selected_artists_list.count())]
        if current_text in existing_names:
            QMessageBox.warning(self, "Повтор", "Этот исполнитель уже добавлен.")
            return
        if current_id is None:
            if db.artist_exists(current_text):
                QMessageBox.warning(self, "Ошибка", "Артист с таким именем уже существует.")
                return
            db.add_or_update_artist(None, current_text, None, None, None)
            conn = sqlite3.connect(db.DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT id FROM artists WHERE name = ?", (current_text,))
            row = cur.fetchone()
            conn.close()
            if row:
                current_id = row[0]
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать исполнителя.")
                return
        self.selected_artists_list.addItem(current_text)
        self.selected_artist_ids.append(current_id)

    def remove_selected_artist(self):
        current_row = self.selected_artists_list.currentRow()
        if current_row >= 0:
            self.selected_artists_list.takeItem(current_row)
            del self.selected_artist_ids[current_row]

    def save(self):
        if not show_question(self, "Подтверждение", "Вы уверены, что хотите сохранить изменения?"):
            return

        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите название альбома.")
            return

        year_text = self.year_edit.text().strip()
        year = int(year_text) if year_text.isdigit() else None
        genre = self.genre_combo.currentText().strip() or None

        artist_ids = self.selected_artist_ids.copy()
        if not artist_ids:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одного исполнителя.")
            return

        final_cover_path = self.cover_path
        if self.cover_path and os.path.exists(self.cover_path):
            app_data_dir = db.get_app_data_dir()
            covers_dir = os.path.join(app_data_dir, "covers")
            os.makedirs(covers_dir, exist_ok=True)
            ext = os.path.splitext(self.cover_path)[1]
            dest = os.path.join(covers_dir, f"cover_{self.album_id or 'new'}{ext}")
            try:
                shutil.copy2(self.cover_path, dest)
                final_cover_path = dest
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось скопировать обложку: {e}\nБудет использован исходный путь.")
                final_cover_path = self.cover_path

        album_id = db.add_or_update_album(self.album_id, title, year, genre, final_cover_path, artist_ids)

        tracks = [(t["title"], t["number"]) for t in self.tracks_data]
        db.save_tracks(album_id, tracks)

        self.accept()

    def confirm_cancel(self):
        if show_question(self, "Подтверждение", "Отменить изменения? Все несохранённые данные будут потеряны."):
            self.reject()