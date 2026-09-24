import random

from PySide6.QtCore import (
    Qt,
    Signal,

    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
    QTimer,
    Property,
)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QValidator
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QWidget,
    QFrame,
    QAbstractItemView,
    QGridLayout,
)


class RatingInputValidator(QValidator):
    """Allows 0.0-10.0 and the special value 11, but nothing from 10 to 11."""

    def validate(self, input_text, pos):
        text = input_text.strip().replace(",", ".")
        if not text:
            return QValidator.State.Intermediate, input_text, pos

        if text in {".", "10."}:
            return QValidator.State.Intermediate, input_text, pos

        try:
            value = float(text)
        except ValueError:
            return QValidator.State.Invalid, input_text, pos

        if value < 0 or value > 11:
            return QValidator.State.Invalid, input_text, pos

        if 10.0 < value < 11.0:
            return QValidator.State.Invalid, input_text, pos

        if value == 11.0:
            return QValidator.State.Acceptable, input_text, pos

        if "." in text and len(text.split(".", 1)[1]) > 1:
            return QValidator.State.Invalid, input_text, pos

        return QValidator.State.Acceptable, input_text, pos


class StreakBadge(QWidget):
    """Animated "Streak! Nx" badge with a small random tilt and optional rainbow text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setFixedSize(92, 36)
        self.setObjectName("StreakBadge")

        self._text = ""
        self._opacity = 0.0
        self._scale = 0.55
        self._angle = 0.0
        self._rainbow = False
        self._phase = 0
        self._animation = None
        self.hide()

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = float(value)
        self.update()

    opacity = Property(float, get_opacity, set_opacity)

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = float(value)
        self.update()

    scale = Property(float, get_scale, set_scale)

    def set_phase(self, phase):
        self._phase = int(phase) % 360
        self.update()

    def show_streak(self, count, rainbow=False, phase=0):
        if self._animation is not None:
            self._animation.stop()

        self._text = f"Streak! {count}x"
        self._rainbow = bool(rainbow)
        self._phase = int(phase) % 360
        self._angle = random.uniform(-7.0, 7.0)
        self.set_opacity(0.0)
        self.set_scale(0.55)
        self.show()

        fade_in = QPropertyAnimation(self, b"opacity", self)
        fade_in.setDuration(380)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        grow = QPropertyAnimation(self, b"scale", self)
        grow.setDuration(470)
        grow.setStartValue(0.55)
        grow.setEndValue(1.0)
        grow.setEasingCurve(QEasingCurve.Type.OutBack)

        in_group = QParallelAnimationGroup(self)
        in_group.addAnimation(fade_in)
        in_group.addAnimation(grow)

        fade_out = QPropertyAnimation(self, b"opacity", self)
        fade_out.setDuration(600)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)

        shrink = QPropertyAnimation(self, b"scale", self)
        shrink.setDuration(600)
        shrink.setStartValue(1.0)
        shrink.setEndValue(0.96)
        shrink.setEasingCurve(QEasingCurve.Type.InCubic)

        out_group = QParallelAnimationGroup(self)
        out_group.addAnimation(fade_out)
        out_group.addAnimation(shrink)

        sequence = QSequentialAnimationGroup(self)
        sequence.addAnimation(in_group)
        sequence.addPause(160)
        sequence.addAnimation(out_group)
        sequence.finished.connect(self._finish_animation)

        self._animation = sequence
        sequence.start()

    def _finish_animation(self):
        self.hide()
        self._animation = None
        self.set_opacity(0.0)

    def hide_streak(self):
        if self._animation is not None:
            self._animation.stop()
            self._animation = None
        self.hide()
        self.set_opacity(0.0)

    def paintEvent(self, event):
        if not self._text or self._opacity <= 0.0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setOpacity(self._opacity)

        painter.translate(self.width() / 2.0, self.height() / 2.0)
        painter.rotate(self._angle)
        painter.scale(self._scale, self._scale)

        font = QFont(self.font())
        font.setBold(True)
        font.setPointSizeF(10.5)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(self._text)
        baseline = (metrics.ascent() - metrics.descent()) / 2.0

        if self._rainbow:
            x = -text_width / 2.0
            for index, char in enumerate(self._text):
                char_width = metrics.horizontalAdvance(char)
                color = QColor.fromHsv(
                    (self._phase + index * 32) % 360,
                    225,
                    255,
                )
                painter.setPen(color)
                painter.setFont(font)
                painter.drawText(x, baseline, char)
                x += char_width
        else:
            painter.setPen(QColor("#F2F4F7"))
            painter.setFont(font)
            painter.drawText(
                -text_width / 2.0,
                baseline,
                self._text,
            )
        painter.end()


class RainbowTrackTitle(QLabel):
    """Track title label that can continuously paint its text with a rainbow gradient."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._rainbow = False
        self._phase = 0
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setWordWrap(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_rainbow(self, enabled):
        enabled = bool(enabled)
        if self._rainbow != enabled:
            self._rainbow = enabled
            self.update()

    def set_phase(self, phase):
        self._phase = int(phase) % 360
        if self._rainbow:
            self.update()

    def paintEvent(self, event):
        if not self._rainbow:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        font = QFont(self.font())
        font.setBold(True)
        metrics = QFontMetrics(font)
        text = metrics.elidedText(
            self.text(),
            Qt.TextElideMode.ElideRight,
            max(1, self.width() - 8),
        )
        total_width = metrics.horizontalAdvance(text)
        x = 4
        y = (self.height() + metrics.ascent() - metrics.descent()) / 2.0

        for index, char in enumerate(text):
            char_width = metrics.horizontalAdvance(char)
            color = QColor.fromHsv(
                (self._phase + index * 11) % 360,
                225,
                255,
            )
            painter.setPen(color)
            painter.setFont(font)
            painter.drawText(x, y, char)
            x += char_width

        painter.end()




class ParticipantTile(QFrame):
    """Compact selectable participant tile with the same hover growth as media cards."""

    BASE_WIDTH = 112
    HOVER_WIDTH = 126
    BASE_HEIGHT = 34
    HOVER_HEIGHT = 40
    HOVER_DURATION_MS = 170

    clicked = Signal(int)

    def __init__(self, participant_id, name, parent=None):
        super().__init__(parent)
        self.participant_id = participant_id
        self._selected = False
        self.setObjectName("ParticipantTile")
        self.setMinimumSize(self.BASE_WIDTH, self.BASE_HEIGHT)
        self.setMaximumSize(self.BASE_WIDTH, self.BASE_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)

        self.name_label = QLabel(name, self)
        self.name_label.setObjectName("ParticipantTileName")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(self.name_label)

        self._hover_animations = []
        for prop, base, hover in (
            (b"minimumWidth", self.BASE_WIDTH, self.HOVER_WIDTH),
            (b"maximumWidth", self.BASE_WIDTH, self.HOVER_WIDTH),
            (b"minimumHeight", self.BASE_HEIGHT, self.HOVER_HEIGHT),
            (b"maximumHeight", self.BASE_HEIGHT, self.HOVER_HEIGHT),
        ):
            animation = QPropertyAnimation(self, prop, self)
            animation.setDuration(self.HOVER_DURATION_MS)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._hover_animations.append((animation, prop, base, hover))

    @property
    def selected(self):
        return self._selected

    def set_selected(self, selected):
        self._selected = bool(selected)
        self.setProperty("selected", self._selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _animate_hover(self, hovered):
        for animation, prop, base, hover in self._hover_animations:
            animation.stop()
            current = self.width() if prop in (b"minimumWidth", b"maximumWidth") else self.height()
            animation.setStartValue(current)
            animation.setEndValue(hover if hovered else base)
            animation.start()

    def enterEvent(self, event):
        self._animate_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.participant_id)
        super().mousePressEvent(event)


class RatingCell(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("0.0–10.0 или 11")
        self.input.setValidator(RatingInputValidator(self.input))
        self.input.setFixedWidth(96)
        self.input.setMinimumHeight(34)
        self.input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input.setClearButtonEnabled(False)
        layout.addWidget(self.input, 0, Qt.AlignmentFlag.AlignCenter)

        # Overlay: badge is deliberately NOT part of the layout, so showing
        # it can never change the width/position of the rating input.
        self.streak_badge = StreakBadge(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        badge_w = self.streak_badge.width()
        badge_h = self.streak_badge.height()
        input_rect = self.input.geometry()

        # Put the badge immediately to the right of the fixed input.
        # When the cell is narrow, keep it inside the cell instead of
        # changing the input geometry.
        x = min(input_rect.right() + 4, max(0, self.width() - badge_w))
        y = max(0, input_rect.top() - (badge_h - 6))
        self.streak_badge.move(int(x), int(y))

    def set_value(self, value, is_secret):
        self.input.blockSignals(True)
        if is_secret:
            self.input.setText("11")
        else:
            self.input.setText(f"{float(value):.1f}")
        self.input.blockSignals(False)

    def value(self):
        text = self.input.text().strip().replace(",", ".")
        if not text:
            return 0.0
        return float(text)

    def is_secret(self):
        return abs(self.value() - 11.0) < 1e-9

    def show_streak(self, count, rainbow=False, phase=0):
        self.streak_badge.show_streak(count, rainbow=rainbow, phase=phase)

    def hide_streak(self):
        self.streak_badge.hide_streak()

    def set_rainbow_phase(self, phase):
        self.streak_badge.set_phase(phase)


class RatingPage(QWidget):
    back_requested = Signal()
    save_requested = Signal(dict)
    def __init__(self, parent, album, participants, existing, participant_service=None):
        super().__init__(parent)
        self.album = album
        self.all_participants = participants
        self.existing = existing
        self.participant_service = participant_service
        self.cells = {}

        self._selected_participant_ids = []
        self._track_row_by_id = {}
        self._rainbow_rows = set()
        self._rainbow_phase = 0
        self._rainbow_timer = QTimer(self)
        self._rainbow_timer.setInterval(45)
        self._rainbow_timer.timeout.connect(self._advance_rainbow)

        root = QVBoxLayout(self)
        title = QLabel(album["title"])
        title.setObjectName("PageTitle")
        root.addWidget(title)
        hint = QLabel(
            "Для каждого участника заполните оценки всех треков. "
            "Обычная оценка: 0–10 с шагом 0.1. Значение 11 вводится вручную "
            "и может использоваться не более одного раза для каждого участника."
        )
        hint.setObjectName("Muted")
        root.addWidget(hint)

        participant_row = QHBoxLayout()
        participant_row.addWidget(QLabel("Участники"))
        self.participant_search = QLineEdit()
        self.participant_search.setPlaceholderText("Имя участника")
        self.participant_search.setFixedWidth(210)
        participant_row.addWidget(self.participant_search)
        add = QPushButton("Добавить")
        add.clicked.connect(self._add_participant)
        participant_row.addWidget(add)
        participant_row.addStretch()
        root.addLayout(participant_row)

        self.participant_tiles_widget = QWidget()
        self.participant_tiles_grid = QGridLayout(self.participant_tiles_widget)
        self.participant_tiles_grid.setContentsMargins(2, 4, 2, 6)
        self.participant_tiles_grid.setHorizontalSpacing(10)
        self.participant_tiles_grid.setVerticalSpacing(10)
        self.participant_tiles_grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.participant_tiles = {}
        self._selected_participant_ids = []
        self.participant_tiles_widget.setMinimumHeight(58)
        self.participant_tiles_widget.setMaximumHeight(118)
        root.addWidget(self.participant_tiles_widget)
        self._fill_participants()

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(54)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(150)
        root.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        back = QPushButton("Отмена")
        back.clicked.connect(self.back_requested.emit)
        save = QPushButton("Сохранить")
        save.clicked.connect(self._validate_and_accept)
        buttons.addWidget(back)
        buttons.addWidget(save)
        root.addLayout(buttons)

        self._rebuild_table()

    def _relayout_participant_tiles(self):
        for i in reversed(range(self.participant_tiles_grid.count())):
            item = self.participant_tiles_grid.takeAt(i)
            if item.widget() is not None:
                item.widget().setParent(self.participant_tiles_widget)
        tiles = list(self.participant_tiles.values())
        for index, tile in enumerate(tiles):
            row, col = divmod(index, 6)
            self.participant_tiles_grid.addWidget(tile, row, col)

    def _add_participant_tile(self, participant_id, name, selected=False):
        tile = ParticipantTile(participant_id, name, self.participant_tiles_widget)
        tile.clicked.connect(self._participant_tile_clicked)
        tile.set_selected(selected)
        self.participant_tiles[participant_id] = tile
        if selected and participant_id not in self._selected_participant_ids:
            self._selected_participant_ids.append(participant_id)

    def _fill_participants(self):
        existing_ids = {row["participant_id"] for row in self.existing["participants"]}
        for participant in self.all_participants:
            self._add_participant_tile(
                participant["id"],
                participant["name"],
                participant["id"] in existing_ids,
            )
        self._relayout_participant_tiles()

    def _participant_tile_clicked(self, participant_id):
        tile = self.participant_tiles.get(participant_id)
        if tile is None:
            return
        selected = not tile.selected
        tile.set_selected(selected)
        if selected:
            if participant_id not in self._selected_participant_ids:
                self._selected_participant_ids.append(participant_id)
        else:
            self._selected_participant_ids = [
                pid for pid in self._selected_participant_ids if pid != participant_id
            ]
        self._rebuild_table()

    def _add_participant(self):
        name = self.participant_search.text().strip()
        if not name:
            return
        for participant in self.all_participants:
            if participant["name"].casefold() == name.casefold():
                tile = self.participant_tiles.get(participant["id"])
                if tile is not None:
                    tile.set_selected(True)
                if participant["id"] not in self._selected_participant_ids:
                    self._selected_participant_ids.append(participant["id"])
                self.participant_search.clear()
                self._rebuild_table()
                return
        if self.participant_service is None:
            return
        try:
            participant_id = self.participant_service.create(name)
        except Exception as exc:
            QMessageBox.warning(self, "Участник", str(exc))
            return
        self.all_participants.append({"id": participant_id, "name": name})
        self._add_participant_tile(participant_id, name, selected=True)
        self._relayout_participant_tiles()
        self.participant_search.clear()
        self._rebuild_table()

    def _rebuild_table(self):
        self._stop_rainbow_timer()
        self._rainbow_rows.clear()
        self._selected_participant_ids = [
            pid for pid in self._selected_participant_ids
            if pid in self.participant_tiles and self.participant_tiles[pid].selected
        ]
        self._track_row_by_id.clear()

        selected = [
            self.participant_tiles[pid]
            for pid in self._selected_participant_ids
            if pid in self.participant_tiles
        ]
        self.table.clear()
        self.cells.clear()
        self.table.setColumnCount(len(selected) + 1)
        self.table.setRowCount(len(self.album["tracks"]))
        headers = ["Трек"] + [tile.name_label.text() for tile in selected]
        self.table.setHorizontalHeaderLabels(headers)

        existing_values = self.existing["ratings"]
        for row, track in enumerate(self.album["tracks"]):
            self._track_row_by_id[track["id"]] = row
            title_label = RainbowTrackTitle(f"{track['track_number']:02d}  {track['title']}")
            title_label.setObjectName("RatingTrackTitle")
            self.table.setCellWidget(row, 0, title_label)

            for col, participant_item in enumerate(selected, start=1):
                participant_id = participant_item.participant_id
                cell = RatingCell()
                if (participant_id, track["id"]) in existing_values:
                    value, secret = existing_values[(participant_id, track["id"])]
                    cell.set_value(value, secret)
                cell.input.textChanged.connect(
                    lambda _text, pid=participant_id, tid=track["id"]: self._on_rating_changed(pid, tid)
                )
                self.table.setCellWidget(row, col, cell)
                self.cells[(participant_id, track["id"])] = cell

        self._refresh_all_streaks(animate=False)

    def _on_rating_changed(self, participant_id, track_id):
        row = self._track_row_by_id.get(track_id)
        if row is None:
            return
        self._refresh_streak_row(row, changed_participant_id=participant_id, animate=True)

    def _secret_cells_for_row(self, row):
        tracks = self.album["tracks"]
        if row < 0 or row >= len(tracks):
            return []
        track_id = tracks[row]["id"]
        return [
            (pid, self.cells[(pid, track_id)])
            for pid in self._selected_participant_ids
            if (pid, track_id) in self.cells and self.cells[(pid, track_id)].is_secret()
        ]

    def _refresh_streak_row(self, row, changed_participant_id=None, animate=True):
        tracks = self.album["tracks"]
        if row < 0 or row >= len(tracks):
            return
        track_id = tracks[row]["id"]

        row_cells = [
            self.cells[(pid, track_id)]
            for pid in self._selected_participant_ids
            if (pid, track_id) in self.cells
        ]
        for cell in row_cells:
            cell.hide_streak()

        secret_cells = self._secret_cells_for_row(row)
        secret_count = len(secret_cells)
        full_streak = (
            len(self._selected_participant_ids) >= 3
            and secret_count == len(self._selected_participant_ids)
        )

        if full_streak:
            self._rainbow_rows.add(row)
        else:
            self._rainbow_rows.discard(row)
            title_label = self.table.cellWidget(row, 0)
            if isinstance(title_label, RainbowTrackTitle):
                title_label.set_rainbow(False)

        if (
            animate
            and changed_participant_id is not None
            and secret_count >= 3
        ):
            changed_cell = self.cells.get((changed_participant_id, track_id))
            if changed_cell is not None and changed_cell.is_secret():
                changed_cell.show_streak(
                    secret_count,
                    rainbow=full_streak and secret_count == len(self._selected_participant_ids),
                    phase=self._rainbow_phase,
                )

        self._sync_rainbow_timer()
        if self._rainbow_rows:
            self._apply_rainbow_colors()
    def _refresh_all_streaks(self, animate=False):
        self._rainbow_rows.clear()
        for row in range(self.table.rowCount()):
            self._refresh_streak_row(row, changed_participant_id=None, animate=animate)
        self._sync_rainbow_timer()
        if self._rainbow_rows:
            self._apply_rainbow_colors()

    def _sync_rainbow_timer(self):
        if self._rainbow_rows:
            if not self._rainbow_timer.isActive():
                self._rainbow_timer.start()
        else:
            self._stop_rainbow_timer()

    def _stop_rainbow_timer(self):
        if self._rainbow_timer.isActive():
            self._rainbow_timer.stop()
        for row in range(self.table.rowCount()):
            if row in self._rainbow_rows:
                continue
            title_label = self.table.cellWidget(row, 0)
            if isinstance(title_label, RainbowTrackTitle):
                title_label.set_rainbow(False)

    def _advance_rainbow(self):
        self._rainbow_phase = (self._rainbow_phase + 7) % 360
        self._apply_rainbow_colors()

    def _apply_rainbow_colors(self):
        for row in tuple(self._rainbow_rows):
            title_label = self.table.cellWidget(row, 0)
            if not isinstance(title_label, RainbowTrackTitle):
                continue
            title_label.set_rainbow(True)
            title_label.set_phase(self._rainbow_phase)

            if self._selected_participant_ids:
                track_id = self.album["tracks"][row]["id"]
                last_pid = self._selected_participant_ids[-1]
                last_cell = self.cells.get((last_pid, track_id))
                if last_cell is not None:
                    last_cell.set_rainbow_phase(self._rainbow_phase)

    def _validate_and_accept(self):
        selected = list(self._selected_participant_ids)
        if not selected:
            QMessageBox.warning(self, "Оценка", "Выберите хотя бы одного участника.")
            return
        result = {}
        for participant_id in selected:
            ratings = []
            secret_count = 0
            for track in self.album["tracks"]:
                cell = self.cells.get((participant_id, track["id"]))
                if cell is None:
                    QMessageBox.warning(self, "Оценка", "Не удалось собрать оценки.")
                    return
                ratings.append((track["id"], cell.value(), cell.is_secret()))
                secret_count += int(cell.is_secret())
            if secret_count > 1:
                name = self.participant_tiles[participant_id].name_label.text()
                QMessageBox.warning(
                    self,
                    "Оценка",
                    f"У участника «{name}» оценка 11 может быть использована только один раз.",
                )
                return
            result[participant_id] = ratings
        self.result = result
        self.save_requested.emit(self.result)
