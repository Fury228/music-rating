import sqlite3
from typing import Optional


class AlbumRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _base_query():
        return """
            SELECT a.*, MIN(10.0, AVG(r.value)) AS rating_average
            FROM albums a
            LEFT JOIN album_artists aa ON aa.album_id=a.id
            LEFT JOIN artists ar ON ar.id=aa.artist_id
            LEFT JOIN tracks t ON t.album_id=a.id
            LEFT JOIN album_ratings alr ON alr.album_id=a.id
            LEFT JOIN album_rating_participants arp ON arp.album_rating_id=alr.id
            LEFT JOIN participants p ON p.id=arp.participant_id
            LEFT JOIN ratings r ON r.album_rating_participant_id=arp.id
        """

    def get_by_id(self, album_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM albums WHERE id = ?", (album_id,)).fetchone()

    def list_all(self, filters=None) -> list[sqlite3.Row]:
        return self._query(filters or {})

    def search(self, query: str, filters=None) -> list[sqlite3.Row]:
        filters = dict(filters or {})
        filters["search"] = query.strip()
        return self._query(filters)

    def _query(self, filters):
        clauses = []
        params = []
        search = filters.get("search", "").strip()
        if search:
            pattern = f"%{search}%"
            clauses.append("(a.title LIKE ? COLLATE NOCASE OR ar.name LIKE ? COLLATE NOCASE OR t.title LIKE ? COLLATE NOCASE)")
            params.extend([pattern, pattern, pattern])

        year = filters.get("year")
        if year not in (None, "", "Все"):
            clauses.append("a.year = ?")
            params.append(int(year))

        region = filters.get("region")
        if region not in (None, "", "Все"):
            clauses.append("a.region = ?")
            params.append(region)

        genre = filters.get("genre")
        if genre not in (None, "", "Все"):
            clauses.append("a.genre = ?")
            params.append(genre)

        artist_id = filters.get("artist_id")
        if artist_id not in (None, "", "Все"):
            clauses.append("EXISTS (SELECT 1 FROM album_artists aa2 WHERE aa2.album_id=a.id AND aa2.artist_id=?)")
            params.append(int(artist_id))

        participant_count = filters.get("participant_count")
        if participant_count not in (None, "", "Все"):
            clauses.append("(SELECT COUNT(DISTINCT arp_c.participant_id) FROM album_rating_participants arp_c JOIN album_ratings ar_c ON ar_c.id=arp_c.album_rating_id WHERE ar_c.album_id=a.id) = ?")
            params.append(int(participant_count))

        participant_id = filters.get("participant_id")
        if participant_id not in (None, "", "Все"):
            clauses.append("EXISTS (SELECT 1 FROM album_rating_participants arp2 JOIN album_ratings ar2 ON ar2.id=arp2.album_rating_id WHERE ar2.album_id=a.id AND arp2.participant_id=?)")
            params.append(int(participant_id))

        rating = filters.get("rating")
        if rating == "unrated":
            clauses.append("NOT EXISTS (SELECT 1 FROM ratings r2 JOIN album_rating_participants arp2 ON arp2.id=r2.album_rating_participant_id JOIN album_ratings ar2 ON ar2.id=arp2.album_rating_id WHERE ar2.album_id=a.id)")
        elif rating not in (None, "", "Все"):
            clauses.append("EXISTS (SELECT 1 FROM ratings r2 JOIN album_rating_participants arp2 ON arp2.id=r2.album_rating_participant_id JOIN album_ratings ar2 ON ar2.id=arp2.album_rating_id WHERE ar2.album_id=a.id GROUP BY ar2.album_id HAVING MIN(10.0, AVG(r2.value)) >= ?)")
            params.append(float(rating))

        sql = self._base_query()
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " GROUP BY a.id ORDER BY a.title COLLATE NOCASE, a.year"
        return self.conn.execute(sql, params).fetchall()

    def filter_options(self):
        years = [r["year"] for r in self.conn.execute("SELECT DISTINCT year FROM albums WHERE year IS NOT NULL ORDER BY year DESC").fetchall()]
        regions = [r["region"] for r in self.conn.execute("SELECT DISTINCT region FROM albums WHERE region IS NOT NULL ORDER BY region").fetchall()]
        genres = [r["genre"] for r in self.conn.execute("SELECT DISTINCT genre FROM albums WHERE genre IS NOT NULL AND TRIM(genre) <> '' ORDER BY genre COLLATE NOCASE").fetchall()]
        artists = self.conn.execute(
            "SELECT id, name FROM artists WHERE EXISTS (SELECT 1 FROM album_artists aa WHERE aa.artist_id=artists.id) ORDER BY name COLLATE NOCASE"
        ).fetchall()
        participants = self.conn.execute(
            "SELECT DISTINCT p.id, p.name FROM participants p JOIN album_rating_participants arp ON arp.participant_id=p.id ORDER BY p.name COLLATE NOCASE"
        ).fetchall()
        participant_counts = [r["participant_count"] for r in self.conn.execute("SELECT COUNT(DISTINCT arp.participant_id) AS participant_count FROM album_ratings ar JOIN album_rating_participants arp ON arp.album_rating_id=ar.id GROUP BY ar.album_id ORDER BY participant_count").fetchall()]
        return {"years": years, "genres": genres, "regions": regions, "artists": artists, "participants": participants, "participant_counts": participant_counts}

    def create(self, title: str, year=None, genre=None, region=None, cover_path=None) -> int:
        cur = self.conn.execute(
            "INSERT INTO albums(title, year, genre, region, cover_path) VALUES (?, ?, ?, ?, ?)",
            (title, year, genre, region, cover_path),
        )
        return cur.lastrowid

    def update(self, album_id: int, title: str, year=None, genre=None, region=None, cover_path=None) -> None:
        self.conn.execute(
            "UPDATE albums SET title=?, year=?, genre=?, region=?, cover_path=? WHERE id=?",
            (title, year, genre, region, cover_path, album_id),
        )

    def delete(self, album_id: int) -> None:
        self.conn.execute("DELETE FROM albums WHERE id = ?", (album_id,))

    def list_artists(self, album_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT ar.* FROM artists ar
               JOIN album_artists aa ON aa.artist_id=ar.id
               WHERE aa.album_id=? ORDER BY ar.name COLLATE NOCASE""",
            (album_id,),
        ).fetchall()

    def list_artist_ids(self, album_id: int) -> list[int]:
        rows = self.conn.execute(
            "SELECT artist_id FROM album_artists WHERE album_id=? ORDER BY artist_id",
            (album_id,),
        ).fetchall()
        return [r["artist_id"] for r in rows]

    def set_artists(self, album_id: int, artist_ids: list[int]) -> None:
        self.conn.execute("DELETE FROM album_artists WHERE album_id=?", (album_id,))
        for artist_id in dict.fromkeys(artist_ids):
            self.conn.execute(
                "INSERT INTO album_artists(album_id, artist_id) VALUES (?, ?)",
                (album_id, artist_id),
            )

    def get_with_artists(self, album_id: int):
        album = self.get_by_id(album_id)
        if album is None:
            return None
        return {"album": album, "artists": self.list_artists(album_id)}
