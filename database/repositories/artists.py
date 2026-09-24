import sqlite3
from typing import Optional

class ArtistRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_by_id(self, artist_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM artists WHERE id = ?", (artist_id,)).fetchone()

    def get_by_name(self, name: str) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM artists WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()

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
            clauses.append("(ar.name LIKE ? COLLATE NOCASE OR EXISTS (SELECT 1 FROM album_artists aa_s JOIN albums a_s ON a_s.id=aa_s.album_id WHERE aa_s.artist_id=ar.id AND a_s.title LIKE ? COLLATE NOCASE) OR EXISTS (SELECT 1 FROM album_artists aa_s JOIN albums a_s ON a_s.id=aa_s.album_id JOIN tracks t_s ON t_s.album_id=a_s.id WHERE aa_s.artist_id=ar.id AND t_s.title LIKE ? COLLATE NOCASE))")
            params.extend([pattern, pattern, pattern])

        genre = filters.get("genre")
        if genre not in (None, "", "Все"):
            clauses.append("ar.main_genre = ?")
            params.append(genre)

        age = filters.get("age")
        if age not in (None, "", "Все"):
            clauses.append("ar.age = ?")
            params.append(int(age))

        region = filters.get("region")
        if region not in (None, "", "Все"):
            clauses.append("ar.region = ?")
            params.append(region)

        album_count = filters.get("album_count")
        if album_count not in (None, "", "Все"):
            clauses.append("(SELECT COUNT(DISTINCT aa_c.album_id) FROM album_artists aa_c WHERE aa_c.artist_id=ar.id) = ?")
            params.append(int(album_count))

        rating = filters.get("rating")
        if rating not in (None, "", "Все"):
            clauses.append("EXISTS (SELECT 1 FROM album_artists aa_r JOIN album_ratings alr_r ON alr_r.album_id=aa_r.album_id JOIN album_rating_participants arp_r ON arp_r.album_rating_id=alr_r.id JOIN ratings r_r ON r_r.album_rating_participant_id=arp_r.id WHERE aa_r.artist_id=ar.id GROUP BY aa_r.artist_id HAVING MIN(10.0, AVG(r_r.value)) >= ?)")
            params.append(float(rating))

        sql = """
            SELECT ar.*,
                   (SELECT COUNT(DISTINCT aa.album_id) FROM album_artists aa WHERE aa.artist_id=ar.id) AS album_count,
                   MIN(10.0, AVG(r.value)) AS rating_average
            FROM artists ar
            LEFT JOIN album_artists aa ON aa.artist_id=ar.id
            LEFT JOIN album_ratings alr ON alr.album_id=aa.album_id
            LEFT JOIN album_rating_participants arp ON arp.album_rating_id=alr.id
            LEFT JOIN ratings r ON r.album_rating_participant_id=arp.id
        """
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " GROUP BY ar.id ORDER BY ar.name COLLATE NOCASE"
        return self.conn.execute(sql, params).fetchall()

    def filter_options(self):
        genres = [r["main_genre"] for r in self.conn.execute("SELECT DISTINCT main_genre FROM artists WHERE main_genre IS NOT NULL AND TRIM(main_genre) <> '' ORDER BY main_genre COLLATE NOCASE").fetchall()]
        ages = [r["age"] for r in self.conn.execute("SELECT DISTINCT age FROM artists WHERE age IS NOT NULL ORDER BY age").fetchall()]
        album_counts = [r["album_count"] for r in self.conn.execute("SELECT COUNT(DISTINCT aa.album_id) AS album_count FROM artists ar LEFT JOIN album_artists aa ON aa.artist_id=ar.id GROUP BY ar.id ORDER BY album_count").fetchall()]
        return {"genres": genres, "ages": ages, "regions": ["RU", "WW"], "album_counts": album_counts}

    def create(self, name: str, photo_path=None, age=None, main_genre=None, region=None) -> int:
        cur = self.conn.execute(
            "INSERT INTO artists(name, photo_path, age, main_genre, region) VALUES (?, ?, ?, ?, ?)",
            (name, photo_path, age, main_genre, region),
        )
        return cur.lastrowid

    def update(self, artist_id: int, name: str, photo_path=None, age=None, main_genre=None, region=None) -> None:
        self.conn.execute(
            "UPDATE artists SET name=?, photo_path=?, age=?, main_genre=?, region=? WHERE id=?",
            (name, photo_path, age, main_genre, region, artist_id),
        )

    def delete(self, artist_id: int) -> None:
        self.conn.execute("DELETE FROM artists WHERE id = ?", (artist_id,))
