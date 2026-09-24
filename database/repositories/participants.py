import sqlite3
from typing import Optional


class ParticipantRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_all(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM participants ORDER BY name COLLATE NOCASE"
        ).fetchall()

    def get_by_id(self, participant_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM participants WHERE id=?", (participant_id,)
        ).fetchone()

    def get_or_create(self, name: str) -> int:
        cur = self.conn.execute(
            "SELECT id FROM participants WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone()
        if cur:
            return cur["id"]
        result = self.conn.execute(
            "INSERT INTO participants(name) VALUES (?)", (name,)
        )
        return result.lastrowid
