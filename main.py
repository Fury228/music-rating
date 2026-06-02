import sys
import os
import tempfile
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QLockFile
import database as db
from PySide6.QtGui import QFont

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def load_stylesheet(app):
    style_path = resource_path("styles.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        app.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QPushButton { background-color: #3c3c3c; border: 1px solid #555; border-radius: 4px; padding: 4px; }
            QPushButton:hover { background-color: #4a4a4a; }
        """)

def main():
    lock_file = QLockFile(os.path.join(tempfile.gettempdir(), "MusicRatingApp.lock"))
    if not lock_file.tryLock(0):
        QMessageBox.critical(None, "Уже запущено", "Приложение уже запущено.")
        sys.exit(1)

    db.init_db()
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    load_stylesheet(app) 
    
    from main_window import MainWindow
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()