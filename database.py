import sqlite3

DB_NAME = "music_ratings.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            photo_path TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year INTEGER,
            genre TEXT,
            cover_path TEXT,
            overall_rating REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS album_artists (
            album_id INTEGER NOT NULL,
            artist_id INTEGER NOT NULL,
            FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
            FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
            PRIMARY KEY (album_id, artist_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            track_number INTEGER,
            FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            participant_id INTEGER NOT NULL,
            rating REAL NOT NULL,
            is_secret BOOLEAN DEFAULT 0,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
            FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
            UNIQUE(track_id, participant_id)
        )
    """)
    conn.commit()
    conn.close()

def get_all_artists():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, name, photo_path FROM artists ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_or_update_artist(artist_id, name, photo_path):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if artist_id is None:
        cur.execute("INSERT INTO artists (name, photo_path) VALUES (?, ?)", (name, photo_path))
    else:
        cur.execute("UPDATE artists SET name=?, photo_path=? WHERE id=?", (name, photo_path, artist_id))
    conn.commit()
    conn.close()

def delete_artist(artist_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM artists WHERE id=?", (artist_id,))
    conn.commit()
    conn.close()

def get_artist_by_id(artist_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, name, photo_path FROM artists WHERE id=?", (artist_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_all_albums():
    """Возвращает список альбомов (id, title, year, cover_path, overall_rating)"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, title, year, cover_path, overall_rating FROM albums ORDER BY title")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_album_by_id(album_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, title, year, genre, cover_path, overall_rating FROM albums WHERE id=?", (album_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_album_artists(album_id):
    """Возвращает список (artist_id, name, photo_path) для альбома"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.name, a.photo_path FROM artists a
        JOIN album_artists aa ON a.id = aa.artist_id
        WHERE aa.album_id = ?
        ORDER BY a.name
    """, (album_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_or_update_album(album_id, title, year, genre, cover_path, artist_ids):
    """
    Сохраняет альбом (создание или обновление).
    artist_ids: список id артистов.
    Возвращает album_id.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        if album_id is None:
            cur.execute("""
                INSERT INTO albums (title, year, genre, cover_path, overall_rating)
                VALUES (?, ?, ?, ?, NULL)
            """, (title, year, genre, cover_path))
            album_id = cur.lastrowid
        else:
            cur.execute("""
                UPDATE albums SET title=?, year=?, genre=?, cover_path=?
                WHERE id=?
            """, (title, year, genre, cover_path, album_id))
            cur.execute("DELETE FROM album_artists WHERE album_id=?", (album_id,))

        for artist_id in artist_ids:
            cur.execute("INSERT INTO album_artists (album_id, artist_id) VALUES (?, ?)", (album_id, artist_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return album_id

def delete_album(album_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM albums WHERE id=?", (album_id,))
    conn.commit()
    conn.close()

def search_albums(query):
    """Поиск по названию альбома, имени любого артиста, названию трека"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    q = f"%{query}%"
    cur.execute("""
        SELECT DISTINCT a.id, a.title, a.year, a.cover_path, a.overall_rating
        FROM albums a
        LEFT JOIN album_artists aa ON a.id = aa.album_id
        LEFT JOIN artists art ON aa.artist_id = art.id
        LEFT JOIN tracks t ON t.album_id = a.id
        WHERE a.title LIKE ? OR art.name LIKE ? OR t.title LIKE ?
        ORDER BY a.title
    """, (q, q, q))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_tracks_by_album(album_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, title, track_number FROM tracks WHERE album_id=? ORDER BY track_number", (album_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def save_tracks(album_id, tracks):
    """tracks: список (title, track_number)"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM tracks WHERE album_id=?", (album_id,))
    for title, number in tracks:
        cur.execute("INSERT INTO tracks (album_id, title, track_number) VALUES (?, ?, ?)", (album_id, title, number))
    conn.commit()
    conn.close()

def album_has_ratings(album_id):
    """Проверяет, есть ли оценки для альбома (есть ли записи в ratings через треки)"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM ratings r
        JOIN tracks t ON r.track_id = t.id
        WHERE t.album_id = ? LIMIT 1
    """, (album_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None

def get_albums_without_ratings():
    """Возвращает список альбомов, у которых нет оценок (нет записей в ratings)"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.title, a.year, a.cover_path
        FROM albums a
        WHERE NOT EXISTS (
            SELECT 1 FROM ratings r
            JOIN tracks t ON r.track_id = t.id
            WHERE t.album_id = a.id
        )
        ORDER BY a.title
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_album_rating_data(album_id):
    """Возвращает все данные для отображения оценок: треки, участники, оценки, средние"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM participants WHERE album_id=?", (album_id,))
    participants = cur.fetchall()
    cur.execute("SELECT id, title, track_number FROM tracks WHERE album_id=? ORDER BY track_number", (album_id,))
    tracks = cur.fetchall()
    ratings = {}
    for track_id, _, _ in tracks:
        for part_id, _ in participants:
            cur.execute("SELECT rating FROM ratings WHERE track_id=? AND participant_id=?", (track_id, part_id))
            row = cur.fetchone()
            ratings[(track_id, part_id)] = row[0] if row else None
    conn.close()
    return {
        "participants": participants,
        "tracks": tracks,
        "ratings": ratings
    }