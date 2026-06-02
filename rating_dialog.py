import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QTableWidget, QDoubleSpinBox, QMessageBox,
    QHeaderView, QWidget, QTabWidget, QAbstractSpinBox
)
from PySide6.QtCore import Qt
import database as db
from custom_dialogs import show_question


class RatingSpinBox(QDoubleSpinBox):
    def __init__(self, column_index, parent_table, parent=None):
        super().__init__(parent)
        self.column_index = column_index
        self.parent_table = parent_table
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setRange(0, 11)
        self.setSingleStep(0.1)
        self.setDecimals(1)
        self.setValue(0.0)
        self.previous_value = 0.0

    def wheelEvent(self, event):
        event.ignore()

    def stepBy(self, steps):
        pass

    def focusOutEvent(self, event):
        self.validate_value()
        super().focusOutEvent(event)

    def validate_value(self):
        current = self.value()
        n_rows = self.parent_table.rowCount()
        eleven_count = 0
        for row in range(n_rows):
            spin = self.parent_table.cellWidget(row, self.column_index)
            if spin and spin.value() == 11.0:
                eleven_count += 1
        if current == 11.0 and eleven_count > 1:
            QMessageBox.warning(self, "Ошибка", "Каждый участник может использовать оценку 11 только один раз за альбом.")
            self.setValue(self.previous_value)
        else:
            self.previous_value = current

    def valueChanged(self, value):
        self.validate_value()
        super().valueChanged.emit(value)


class RatingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Оценка альбома")
        self.setModal(True)
        self.setMinimumSize(900, 700)

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.setup_tab = QWidget()
        self.tab_widget.addTab(self.setup_tab, "Настройка")
        self.setup_ui()

        self.rating_tab = QWidget()
        self.tab_widget.addTab(self.rating_tab, "Оценка")
        self.rating_ui()

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_ratings)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.confirm_cancel)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)

        self.participant_fields = []
        self.ratings_table = None
        self.current_album_id = None

        self.add_participant()
        self.load_albums()

        self.album_combo.currentIndexChanged.connect(self.on_album_selected)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self.setup_tab)
        album_layout = QHBoxLayout()
        album_layout.addWidget(QLabel("Выберите альбом:"))
        self.album_combo = QComboBox()
        self.album_combo.setEditable(True)
        album_layout.addWidget(self.album_combo)
        layout.addLayout(album_layout)

        layout.addWidget(QLabel("Участники:"))
        self.participants_widget = QWidget()
        self.participants_layout = QVBoxLayout(self.participants_widget)
        self.participants_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.participants_widget)

        btn_add = QPushButton("Добавить участника")
        btn_add.clicked.connect(lambda: self.add_participant())
        layout.addWidget(btn_add)
        layout.addStretch()

    def rating_ui(self):
        self.rating_tab_layout = QVBoxLayout(self.rating_tab)
        self.ratings_container = None

    def load_albums(self):
        albums = db.get_albums_without_ratings()
        self.album_combo.clear()
        for album_id, title, year, cover_path in albums:
            text = title
            if year:
                text += f" ({year})"
            self.album_combo.addItem(text, album_id)
        if self.album_combo.count() > 0:
            self.current_album_id = self.album_combo.currentData()
            self.update_ratings_table()

    def on_album_selected(self):
        self.current_album_id = self.album_combo.currentData()
        self.update_ratings_table()

    def on_tab_changed(self, index):
        if index == 1:
            self.update_ratings_table()

    def add_participant(self, name=""):
        if len(self.participant_fields) >= 9:
            QMessageBox.warning(self, "Ограничение", "Нельзя добавить более 9 участников.")
            return
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        edit = QLineEdit()
        edit.setPlaceholderText(f"Участник {len(self.participant_fields)+1}")
        edit.setText(name)
        btn_remove = QPushButton("✖")
        btn_remove.setFixedWidth(30)
        btn_remove.clicked.connect(lambda: self.remove_participant(row_widget))
        row_layout.addWidget(edit)
        row_layout.addWidget(btn_remove)
        self.participants_layout.addWidget(row_widget)
        self.participant_fields.append(edit)
        self.update_ratings_table()

    def remove_participant(self, widget):
        for i, field in enumerate(self.participant_fields):
            if field.parent() == widget:
                self.participants_layout.removeWidget(widget)
                widget.deleteLater()
                del self.participant_fields[i]
                break
        self.update_ratings_table()

    def get_tracks(self):
        if not self.current_album_id:
            return []
        conn = sqlite3.connect(db.DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, title, track_number FROM tracks WHERE album_id=? ORDER BY track_number", (self.current_album_id,))
        tracks = cur.fetchall()
        conn.close()
        return tracks

    def update_ratings_table(self):
        if self.ratings_container is not None:
            self.rating_tab_layout.removeWidget(self.ratings_container)
            self.ratings_container.deleteLater()
            self.ratings_container = None

        self.ratings_container = QWidget()
        container_layout = QVBoxLayout(self.ratings_container)
        self.rating_tab_layout.addWidget(self.ratings_container)

        tracks = self.get_tracks()
        participants = [edit.text().strip() for edit in self.participant_fields if edit.text().strip()]

        if not tracks:
            label = QLabel("Для выбранного альбома нет треков. Сначала добавьте треки в альбом.")
            container_layout.addWidget(label)
            self.ratings_table = None
            return

        if len(participants) == 0:
            label = QLabel("Добавьте хотя бы одного участника.")
            container_layout.addWidget(label)
            self.ratings_table = None
            return

        table = QTableWidget(len(tracks), len(participants))
        table.setHorizontalHeaderLabels(participants)
        vertical_headers = [f"{num}. {title}" for _, title, num in tracks]
        table.setVerticalHeaderLabels(vertical_headers)

        for i in range(len(tracks)):
            for j in range(len(participants)):
                spin = RatingSpinBox(j, table)
                table.setCellWidget(i, j, spin)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ratings_table = table
        container_layout.addWidget(table)

    def save_ratings(self):
        if not show_question(self, "Подтверждение", "Сохранить оценки?"):
            return

        album_id = self.current_album_id
        if not album_id:
            QMessageBox.warning(self, "Ошибка", "Выберите альбом.")
            return

        participants = [edit.text().strip() for edit in self.participant_fields]
        if len(participants) == 0:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одного участника.")
            return
        if any(not name for name in participants):
            QMessageBox.warning(self, "Ошибка", "Имена участников не могут быть пустыми.")
            return

        tracks = self.get_tracks()
        if not tracks:
            QMessageBox.warning(self, "Ошибка", "В альбоме нет треков.")
            return

        if not isinstance(self.ratings_table, QTableWidget):
            QMessageBox.warning(self, "Ошибка", "Таблица оценок не создана.")
            return

        n_tracks = len(tracks)
        n_parts = len(participants)
        eleven_counts = [0] * n_parts
        for i in range(n_tracks):
            for j in range(n_parts):
                spin = self.ratings_table.cellWidget(i, j)
                if spin and spin.value() == 11.0:
                    eleven_counts[j] += 1
        for j, cnt in enumerate(eleven_counts):
            if cnt > 1:
                QMessageBox.warning(self, "Ошибка", f"Участник {participants[j]} использовал оценку 11 {cnt} раз. Разрешена только одна 11.")
                return

        conn = sqlite3.connect(db.DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM participants WHERE album_id = ?", (album_id,))
            participant_ids = []
            for name in participants:
                cur.execute("INSERT INTO participants (album_id, name) VALUES (?, ?)", (album_id, name))
                participant_ids.append(cur.lastrowid)

            track_ids = [t[0] for t in tracks]
            for i, track_id in enumerate(track_ids):
                for j, part_id in enumerate(participant_ids):
                    spin = self.ratings_table.cellWidget(i, j)
                    rating = spin.value()
                    is_secret = 1 if rating == 11.0 else 0
                    cur.execute("""
                        INSERT INTO ratings (track_id, participant_id, rating, is_secret)
                        VALUES (?, ?, ?, ?)
                    """, (track_id, part_id, rating, is_secret))

            participant_avgs = []
            for part_id in participant_ids:
                cur.execute("""
                    SELECT AVG(rating) FROM ratings
                    WHERE participant_id = ? AND track_id IN (SELECT id FROM tracks WHERE album_id = ?)
                """, (part_id, album_id))
                avg = cur.fetchone()[0]
                if avg is not None:
                    participant_avgs.append(avg)
            overall = sum(participant_avgs) / len(participant_avgs) if participant_avgs else 0.0
            cur.execute("UPDATE albums SET overall_rating = ? WHERE id = ?", (overall, album_id))

            conn.commit()
            QMessageBox.information(self, "Успех", f"Оценки сохранены. Общая оценка альбома: {overall:.2f}")
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить оценки: {str(e)}")
        finally:
            conn.close()

    def confirm_cancel(self):
        if show_question(self, "Подтверждение", "Отменить изменения? Все несохранённые данные будут потеряны."):
            self.reject()