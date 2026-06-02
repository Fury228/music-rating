from PySide6.QtGui import QPixmap, QColor, QPainter
from PySide6.QtCore import Qt
import os

def load_scaled_image(path, size=64, as_pixmap=True):
    if path and os.path.exists(path):
        pixmap = QPixmap(path)
    else:
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(200, 200, 200))
    if pixmap.isNull():
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(200, 200, 200))
    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    square = QPixmap(size, size)
    square.fill(Qt.transparent)
    x = (size - scaled.width()) // 2
    y = (size - scaled.height()) // 2
    painter = QPainter(square)
    painter.drawPixmap(x, y, scaled)
    painter.end()
    if as_pixmap:
        return square
    else:
        from PySide6.QtGui import QIcon
        return QIcon(square)