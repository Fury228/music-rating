import os
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

IMGS_ROOT = "imgs"
DEFAULT_IMG = os.path.join(IMGS_ROOT, "none.png")

def load_scaled_image(path, size=64, as_pixmap=True):
    """
    Загружает изображение, масштабирует до size x size.
    Если path не существует или не задан – возвращает заглушку.
    size: int (ширина и высота)
    """
    full_path = os.path.join(IMGS_ROOT, path) if path and not os.path.isabs(path) else path
    if not full_path or not os.path.exists(full_path):
        full_path = DEFAULT_IMG
    pixmap = QPixmap(full_path)
    if pixmap.isNull():
        pixmap = QPixmap(DEFAULT_IMG)
    pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if as_pixmap:
        return pixmap
    else:
        return pixmap