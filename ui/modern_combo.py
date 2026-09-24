from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QAbstractItemView


class ModernComboBox(QComboBox):
    popup_closed = Signal()

    """Compact combo box with a classic rectangular drop-down control."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_popup()

    def hidePopup(self):
        super().hidePopup()
        self.popup_closed.emit()

    def _setup_popup(self):
        view = self.view()
        view.setFrameShape(QAbstractItemView.Shape.NoFrame)
        view.setAutoFillBackground(True)
        view.setStyleSheet(
            """
            QListView {
                background: #1A1E24;
                color: #F2F4F7;
                border: 1px solid #343A43;
                outline: none;
                padding: 0px;
            }
            QListView::item {
                min-height: 32px;
                padding: 6px 10px;
                border: none;
                border-radius: 0px;
            }
            QListView::item:hover { background: #252B33; }
            QListView::item:selected { background: #303945; color: #FFFFFF; }
            """
        )
