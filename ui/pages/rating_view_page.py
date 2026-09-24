from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout, QLabel,
)


class RatingViewPage(QWidget):
    back_requested = Signal()

    def __init__(self, album, rating_data, summary, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        top = QHBoxLayout()
        back = QPushButton("← Назад")
        back.clicked.connect(self.back_requested.emit)
        top.addWidget(back)
        title = QLabel(f"Просмотр оценок — {album['title']}")
        title.setObjectName("PageTitle")
        top.addWidget(title)
        top.addStretch()
        root.addLayout(top)

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
            item = QTableWidgetItem(f"{track['track_number']:02d}  {track['title']}")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row, 0, item)
            for col, participant in enumerate(participants, start=1):
                value = ratings.get((participant["participant_id"], track["id"]))
                text = "—" if value is None else f"{float(value[0]):.1f}"
                cell = QTableWidgetItem(text)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
                table.setItem(row, col, cell)
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
