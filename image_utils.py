from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt
import os

def load_scaled_image(path, size=64, as_pixmap=True):
    if path and os.path.exists(path):
        pixmap = QPixmap(path)
    else:
        # Генерация заглушки
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(200, 200, 200))
    if pixmap.isNull():
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(200, 200, 200))
    pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if as_pixmap:
        return pixmap
    else:
        from PySide6.QtGui import QIcon
        return QIcon(pixmap)