import sqlite3


class RatingRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_or_create_album_rating(self, album_id: int) -> int:
        self.conn.execute(
            "INSERT OR IGNORE INTO album_ratings(album_id) VALUES (?)", (album_id,)
        )
        row = self.conn.execute(
            "SELECT id FROM album_ratings WHERE album_id=?", (album_id,)
        ).fetchone()
        return row["id"]

    def get_or_create_participant_link(self, album_rating_id: int, participant_id: int) -> int:
        self.conn.execute(
            """INSERT OR IGNORE INTO album_rating_participants
               (album_rating_id, participant_id) VALUES (?, ?)""",
            (album_rating_id, participant_id),
        )
        row = self.conn.execute(
            """SELECT id FROM album_rating_participants
               WHERE album_rating_id=? AND participant_id=?""",
            (album_rating_id, participant_id),
        ).fetchone()
        return row["id"]

    def list_rating_participants(self, album_id: int):
        return self.conn.execute(
            """SELECT arp.id AS link_id, p.id AS participant_id, p.name
               FROM album_rating_participants arp
               JOIN album_ratings ar ON ar.id=arp.album_rating_id
               JOIN participants p ON p.id=arp.participant_id
               WHERE ar.album_id=? ORDER BY p.name COLLATE NOCASE""",
            (album_id,),
        ).fetchall()

    def list_ratings(self, album_id: int):
        return self.conn.execute(
            """SELECT arp.participant_id, r.track_id, r.value, r.is_secret
               FROM ratings r
               JOIN album_rating_participants arp ON arp.id=r.album_rating_participant_id
               JOIN album_ratings ar ON ar.id=arp.album_rating_id
               WHERE ar.album_id=?""",
            (album_id,),
        ).fetchall()

    def clear_participants(self, album_rating_id: int, participant_ids: list[int]) -> None:
        if participant_ids:
            placeholders = ",".join("?" for _ in participant_ids)
            self.conn.execute(
                f"""DELETE FROM album_rating_participants
                    WHERE album_rating_id=? AND participant_id NOT IN ({placeholders})""",
                [album_rating_id, *participant_ids],
            )
        else:
            self.conn.execute(
                "DELETE FROM album_rating_participants WHERE album_rating_id=?",
                (album_rating_id,),
            )

    def delete_all_ratings(self, link_id: int) -> None:
        self.conn.execute(
            "DELETE FROM ratings WHERE album_rating_participant_id=?", (link_id,)
        )

    def upsert_rating(self, link_id: int, track_id: int, value: float, is_secret: bool) -> None:
        self.conn.execute(
            """INSERT INTO ratings(album_rating_participant_id, track_id, value, is_secret)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(album_rating_participant_id, track_id)
               DO UPDATE SET value=excluded.value, is_secret=excluded.is_secret""",
            (link_id, track_id, value, int(is_secret)),
        )

    def update_timestamp(self, album_rating_id: int) -> None:
        self.conn.execute(
            "UPDATE album_ratings SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (album_rating_id,),
        )
