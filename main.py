import sys
import os
from PySide6.QtWidgets import QApplication
import database as db

if __name__ == "__main__":
    db.init_db()
    app = QApplication(sys.argv)
    from main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())