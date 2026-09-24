from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout, QLabel
)


class RatingViewDialog(QDialog):
    """Read-only track ratings table with the album summary line."""

    def __init__(self, parent, album, rating_data, summary):
        super().__init__(parent)
        self.setWindowTitle(f"Просмотр оценок — {album['title']}")
        self.setMinimumSize(900, 650)
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

        root = QVBoxLayout(self)

        title = QLabel(album["title"])
        title.setObjectName("PageTitle")
        root.addWidget(title)

        participants = rating_data["participants"]
        ratings = rating_data["ratings"]
        tracks = album["tracks"]

        table = QTableWidget(len(tracks), len(participants) + 1)
        table.setHorizontalHeaderLabels(["Трек"] + [p["name"] for p in participants])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(38)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setMinimumSectionSize(150)

        for row, track in enumerate(tracks):
            track_item = QTableWidgetItem(
                f"{track['track_number']:02d}  {track['title']}"
            )
            track_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row, 0, track_item)

            for col, participant in enumerate(participants, start=1):
                value = ratings.get((participant["participant_id"], track["id"]))
                text = "—" if value is None else f"{float(value[0]):.1f}"
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                table.setItem(row, col, item)

        root.addWidget(table, 1)

        average = summary.get("average")
        rated = summary.get("rated", 0)
        participants_count = summary.get("participants", 0)
        overall_text = (
            f"Средняя оценка альбома: {min(float(average), 10.0):.2f}  •  "
            f"Участников: {participants_count}  •  Оценок: {rated}"
            if average is not None else "Оценок пока нет"
        )
        overall = QLabel(overall_text)
        overall.setAlignment(Qt.AlignmentFlag.AlignRight)
        overall.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 4px;")
        root.addWidget(overall)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close = QPushButton("Закрыть")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)
