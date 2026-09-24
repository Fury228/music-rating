import sqlite3
from typing import Optional

class TrackRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_by_id(self, track_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM tracks WHERE id=?", (track_id,)).fetchone()

    def list_for_album(self, album_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM tracks WHERE album_id=? ORDER BY track_number", (album_id,)
        ).fetchall()

    def create(self, album_id: int, title: str, track_number: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO tracks(album_id, title, track_number) VALUES (?, ?, ?)",
            (album_id, title, track_number),
        )
        return cur.lastrowid

    def update(self, track_id: int, title: str, track_number: int) -> None:
        self.conn.execute(
            "UPDATE tracks SET title=?, track_number=? WHERE id=?",
            (title, track_number, track_id),
        )

    def delete(self, track_id: int) -> None:
        self.conn.execute("DELETE FROM tracks WHERE id=?", (track_id,))

    def delete_for_album(self, album_id: int) -> None:
        self.conn.execute("DELETE FROM tracks WHERE album_id=?", (album_id,))
