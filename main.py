import sys
import os
import tempfile
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QLockFile
import database as db

def main():
    lock_file = QLockFile(os.path.join(tempfile.gettempdir(), "MusicRatingApp.lock"))
    if not lock_file.tryLock(0):
        QMessageBox.critical(None, "Уже запущено", "Приложение уже запущено.")
        sys.exit(1)
    
    os.makedirs("imgs", exist_ok=True)
    db.init_db()
    
    app = QApplication(sys.argv)
    from main_window import MainWindow
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()