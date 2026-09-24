from pathlib import Path

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class ImageTileCard(QFrame):
    clicked = Signal(int)

    BASE_WIDTH = 196
    BASE_HEIGHT = 246
    HOVER_WIDTH = 210
    HOVER_HEIGHT = 263
    BASE_IMAGE_SIZE = 174
    HOVER_IMAGE_SIZE = 187
    HOVER_DURATION_MS = 170

    def __init__(self, item_id: int, title: str, image_path: str | None, kind: str, parent=None, rating=None):
        super().__init__(parent)
        self.item_id = item_id
        self.setObjectName("MediaCard")
        self.setMinimumSize(self.BASE_WIDTH, self.BASE_HEIGHT)
        self.setMaximumSize(self.BASE_WIDTH, self.BASE_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.image = QLabel(self)
        self.image.setObjectName("MediaCardImage")
        self.image.setMinimumSize(self.BASE_IMAGE_SIZE, self.BASE_IMAGE_SIZE)
        self.image.setMaximumSize(self.BASE_IMAGE_SIZE, self.BASE_IMAGE_SIZE)
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_image(image_path, kind)
        layout.addWidget(self.image, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.title = QLabel(title, self)
        self.title.setObjectName("MediaCardTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setMaximumHeight(42)
        layout.addWidget(self.title)

        self.rating = QLabel(self)
        self.rating.setObjectName("MediaCardRating")
        self.rating.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rating.setVisible(kind == "album" and rating is not None)
        if rating is not None and kind == "album":
            self.rating.setText(f"{min(float(rating), 10.0):.1f}")
        layout.addWidget(self.rating)

        layout.addStretch()

        self._hover_animations = []
        for widget, props in (
            (self, ((b"minimumWidth", self.BASE_WIDTH, self.HOVER_WIDTH),
                    (b"maximumWidth", self.BASE_WIDTH, self.HOVER_WIDTH),
                    (b"minimumHeight", self.BASE_HEIGHT, self.HOVER_HEIGHT),
                    (b"maximumHeight", self.BASE_HEIGHT, self.HOVER_HEIGHT))),
            (self.image, ((b"minimumWidth", self.BASE_IMAGE_SIZE, self.HOVER_IMAGE_SIZE),
                          (b"maximumWidth", self.BASE_IMAGE_SIZE, self.HOVER_IMAGE_SIZE),
                          (b"minimumHeight", self.BASE_IMAGE_SIZE, self.HOVER_IMAGE_SIZE),
                          (b"maximumHeight", self.BASE_IMAGE_SIZE, self.HOVER_IMAGE_SIZE))),
        ):
            for prop, base, hover in props:
                animation = QPropertyAnimation(widget, prop, self)
                animation.setDuration(self.HOVER_DURATION_MS)
                animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                self._hover_animations.append((animation, widget, prop, base, hover))

    def stop_animations(self):
        for animation, *_ in self._hover_animations:
            animation.stop()

    def update_card(self, item_id: int, title: str, image_path: str | None, kind: str, rating=None):
        """Update card data without destroying/recreating the widget."""
        self.stop_animations()
        self.item_id = item_id
        self.title.setText(title)

        self.rating.setVisible(kind == "album" and rating is not None)
        if kind == "album" and rating is not None:
            self.rating.setText(f"{min(float(rating), 10.0):.1f}")
        else:
            self.rating.clear()

        self.setMinimumSize(self.BASE_WIDTH, self.BASE_HEIGHT)
        self.setMaximumSize(self.BASE_WIDTH, self.BASE_HEIGHT)
        self.image.setMinimumSize(self.BASE_IMAGE_SIZE, self.BASE_IMAGE_SIZE)
        self.image.setMaximumSize(self.BASE_IMAGE_SIZE, self.BASE_IMAGE_SIZE)
        self._set_image(image_path, kind)
        self.updateGeometry()
        self.update()

    def _animate_hover(self, hovered: bool):
        for animation, widget, prop, base, hover in self._hover_animations:
            animation.stop()
            if prop in (b"minimumWidth", b"maximumWidth"):
                current = widget.width()
            else:
                current = widget.height()
            target = hover if hovered else base
            animation.setStartValue(current)
            animation.setEndValue(target)
            animation.start()

    def enterEvent(self, event):
        self._animate_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(False)
        super().leaveEvent(event)

    def _set_image(self, image_path: str | None, kind: str):
        if image_path and Path(image_path).is_file():
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.image.setPixmap(
                    pixmap.scaled(
                        self.image.size(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return
        self.image.setText("Обложка" if kind == "album" else "Фото")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item_id)
        super().mousePressEvent(event)
