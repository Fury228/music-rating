import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QLineEdit, QTableWidget, QDoubleSpinBox, QMessageBox,
    QHeaderView, QWidget
)
from PySide6.QtCore import Qt
import database as db

class RatingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Оценка альбома")
        self.setModal(True)
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout(self)

        album_group = QGroupBox("Выберите альбом")
        album_group.setMaximumHeight(80)
        album_group.setStyleSheet("QGroupBox { margin-top: 5px; }")
        album_layout = QHBoxLayout(album_group)
        album_layout.setContentsMargins(10, 10, 10, 10)
        album_layout.setSpacing(10)

        self.album_combo = QComboBox()
        self.load_albums()
        self.album_combo.currentIndexChanged.connect(self.on_album_selected)

        album_layout.addWidget(QLabel("Альбом:"))
        album_layout.addWidget(self.album_combo)
        layout.addWidget(album_group)

        self.participants_group = QGroupBox("Участники (от 2 до 6)")
        self.participants_layout = QVBoxLayout(self.participants_group)
        self.participant_fields = []
        btn_add_participant = QPushButton("Добавить участника")
        btn_add_participant.clicked.connect(self.add_participant)
        self.participants_layout.addWidget(btn_add_participant)
        layout.addWidget(self.participants_group)

        self.ratings_group = QGroupBox("Оценки треков")
        self.ratings_layout = QVBoxLayout(self.ratings_group)
        self.ratings_table = None
        layout.addWidget(self.ratings_group)

        self.info_label = QLabel("")
        layout.addWidget(self.info_label)

        btn_layout = QHBoxLayout()
        btn_calc = QPushButton("Пересчитать средние")
        btn_calc.clicked.connect(self.update_preview)
        btn_save = QPushButton("Сохранить оценки")
        btn_save.clicked.connect(self.save_ratings)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self.update_ratings_table)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_calc)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.add_participant()
        self.add_participant()
        self.update_ratings_table()

    def load_albums(self):
        albums = db.get_albums_without_ratings()
        self.album_combo.clear()
        self.album_combo.addItem("-- Выберите альбом --", None)
        for album_id, title, year, cover_path in albums:
            text = title
            if year:
                text += f" ({year})"
            self.album_combo.addItem(text, album_id)

    def on_album_selected(self):
        self.update_ratings_table()

    def add_participant(self):
        if len(self.participant_fields) >= 6:
            QMessageBox.warning(self, "Ограничение", "Нельзя добавить более 6 участников.")
            return
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        edit = QLineEdit()
        edit.setPlaceholderText(f"Участник {len(self.participant_fields)+1}")
        btn_remove = QPushButton("✖")
        btn_remove.setFixedWidth(30)
        btn_remove.clicked.connect(lambda: self.remove_participant(row_widget))
        row_layout.addWidget(edit)
        row_layout.addWidget(btn_remove)
        self.participants_layout.insertWidget(self.participants_layout.count() - 1, row_widget)
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
        album_id = self.album_combo.currentData()
        if not album_id:
            return []
        conn = sqlite3.connect(db.DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, title, track_number FROM tracks WHERE album_id=? ORDER BY track_number", (album_id,))
        tracks = cur.fetchall()
        conn.close()
        return tracks

    def update_ratings_table(self):
        if self.ratings_table is not None:
            self.ratings_table.deleteLater()
            self.ratings_table = None
        while self.ratings_layout.count():
            child = self.ratings_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        tracks = self.get_tracks()
        participants = [edit.text().strip() for edit in self.participant_fields if edit.text().strip()]
        if not tracks:
            label = QLabel("Для выбранного альбома нет треков. Сначала добавьте треки в альбом.")
            self.ratings_layout.addWidget(label)
            self.ratings_table = label
            return
        if len(participants) < 2:
            label = QLabel("Добавьте минимум 2 участника для оценивания.")
            self.ratings_layout.addWidget(label)
            self.ratings_table = label
            return

        table = QTableWidget(len(tracks), len(participants))
        table.setHorizontalHeaderLabels(participants)
        vertical_headers = [f"{num}. {title}" for _, title, num in tracks]
        table.setVerticalHeaderLabels(vertical_headers)

        for i in range(len(tracks)):
            for j in range(len(participants)):
                spin = QDoubleSpinBox()
                spin.setRange(0, 11)
                spin.setSingleStep(0.1)
                spin.setDecimals(1)
                spin.setValue(0.0)
                spin.valueChanged.connect(self.update_preview)
                table.setCellWidget(i, j, spin)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ratings_table = table
        self.ratings_layout.addWidget(table)
        self.update_preview()

    def update_preview(self):
        if not isinstance(self.ratings_table, QTableWidget):
            return
        n_tracks = self.ratings_table.rowCount()
        n_parts = self.ratings_table.columnCount()
        if n_tracks == 0 or n_parts == 0:
            return

        participant_sums = [0.0] * n_parts
        participant_counts = [0] * n_parts
        for i in range(n_tracks):
            for j in range(n_parts):
                spin = self.ratings_table.cellWidget(i, j)
                if spin:
                    val = spin.value()
                    participant_sums[j] += val
                    participant_counts[j] += 1

        participant_averages = []
        for j in range(n_parts):
            avg = participant_sums[j] / participant_counts[j] if participant_counts[j] > 0 else 0.0
            participant_averages.append(avg)
        overall = sum(participant_averages) / n_parts if n_parts > 0 else 0.0

        names = [self.ratings_table.horizontalHeaderItem(j).text() for j in range(n_parts)]
        avg_text = ", ".join([f"{names[j]}: {participant_averages[j]:.2f}" for j in range(n_parts)])
        self.info_label.setText(f"Средние по участникам: {avg_text}  |  Общая оценка альбома: {overall:.2f}")

    def save_ratings(self):
        album_id = self.album_combo.currentData()
        if not album_id:
            QMessageBox.warning(self, "Ошибка", "Выберите альбом.")
            return
        participants = [edit.text().strip() for edit in self.participant_fields]
        if len(participants) < 2:
            QMessageBox.warning(self, "Ошибка", "Добавьте минимум 2 участника.")
            return
        if any(not name for name in participants):
            QMessageBox.warning(self, "Ошибка", "Имена участников не могут быть пустыми.")
            return

        tracks = self.get_tracks()
        if not tracks:
            QMessageBox.warning(self, "Ошибка", "В альбоме нет треков. Добавьте треки через редактирование альбома.")
            return

        if not isinstance(self.ratings_table, QTableWidget):
            QMessageBox.warning(self, "Ошибка", "Таблица оценок не создана. Проверьте треки и участников.")
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
                QMessageBox.warning(self, "Ошибка", f"Участник {participants[j]} использовал оценку 11 {cnt} раз. Разрешена только одна 11 на участника за альбом.")
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