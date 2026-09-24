import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from database.connection import open_connection
from database.migrations import migrate
from ui.main_window import MainWindow

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "music_rating.sqlite3"

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = open_connection(DB_PATH)
    migrate(conn)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("MusicRating")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#121417"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#F2F4F7"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1A1E24"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#20252C"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#F2F4F7"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#252B33"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#3A4654"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#777F8B"))
    app.setPalette(palette)
    window = MainWindow(conn)
    window.show()

    exit_code = app.exec()
    conn.close()
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
