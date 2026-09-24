from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)


class RatingSummaryDialog(QDialog):
    """Read-only summary of an album rating."""

    def __init__(self, parent, album, summary):
        super().__init__(parent)
        self.setWindowTitle(f"Итоги оценки — {album['title']}")
        self.setMinimumSize(700, 420)

        root = QVBoxLayout(self)

        title = QLabel(album["title"])
        title.setObjectName("PageTitle")
        root.addWidget(title)

        participants = summary.get("participants_detail", [])
        table = QTableWidget(len(participants), 3)
        table.setHorizontalHeaderLabels(["Участник", "Оценок", "Средняя"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(38)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for row, participant in enumerate(participants):
            table.setItem(row, 0, QTableWidgetItem(participant["name"]))
            table.setItem(row, 1, QTableWidgetItem(str(participant["rated"])))
            average = participant["average"]
            item = QTableWidgetItem("—" if average is None else f"{average:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 2, item)

        root.addWidget(table, 1)

        average = summary.get("average")
        rated = summary.get("rated", 0)
        participants_count = summary.get("participants", 0)
        overall_text = (
            f"Средняя оценка альбома: {average:.2f}  •  "
            f"Участников: {participants_count}  •  Оценок: {rated}"
            if average is not None
            else "Оценок пока нет"
        )
        overall = QLabel(overall_text)
        overall.setAlignment(Qt.AlignmentFlag.AlignRight)
        overall.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 8px;")
        root.addWidget(overall)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close = QPushButton("Закрыть")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)
