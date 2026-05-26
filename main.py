import sys
import os
from PySide6.QtWidgets import QApplication
import database as db

if __name__ == "__main__":
    os.makedirs("imgs/artists", exist_ok=True)
    os.makedirs("imgs/albums", exist_ok=True)
    default_none = "imgs/none.png"
    if not os.path.exists(default_none):
        from PySide6.QtGui import QPixmap, QColor
        pix = QPixmap(64, 64)
        pix.fill(QColor(200, 200, 200))
        pix.save(default_none)

    db.init_db()
    app = QApplication(sys.argv)
    from main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())