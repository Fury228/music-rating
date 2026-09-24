PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    photo_path TEXT,
    age INTEGER,
    main_genre TEXT,
    region TEXT CHECK (region IN ('RU', 'WW') OR region IS NULL)
);

CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    year INTEGER,
    genre TEXT,
    region TEXT CHECK (region IN ('RU', 'WW') OR region IS NULL),
    cover_path TEXT
);

CREATE TABLE IF NOT EXISTS album_artists (
    album_id INTEGER NOT NULL,
    artist_id INTEGER NOT NULL,
    PRIMARY KEY (album_id, artist_id),
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    track_number INTEGER NOT NULL,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    UNIQUE (album_id, track_number)
);

CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS album_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS album_rating_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_rating_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    FOREIGN KEY (album_rating_id) REFERENCES album_ratings(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE RESTRICT,
    UNIQUE (album_rating_id, participant_id)
);

CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_rating_participant_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    value REAL NOT NULL,
    is_secret INTEGER NOT NULL DEFAULT 0 CHECK (is_secret IN (0, 1)),
    FOREIGN KEY (album_rating_participant_id)
        REFERENCES album_rating_participants(id)
        ON DELETE CASCADE,
    FOREIGN KEY (track_id)
        REFERENCES tracks(id)
        ON DELETE CASCADE,
    UNIQUE (album_rating_participant_id, track_id),
    CHECK (value >= 0.0 AND value <= 11.0),
    CHECK (ROUND(value * 10.0) = value * 10.0),
    CHECK (
        (is_secret = 0 AND value < 11.0)
        OR
        (is_secret = 1 AND value = 11.0)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_one_secret_rating_per_participant
ON ratings(album_rating_participant_id)
WHERE is_secret = 1;

CREATE INDEX IF NOT EXISTS ix_albums_title ON albums(title);
CREATE INDEX IF NOT EXISTS ix_tracks_album ON tracks(album_id, track_number);
CREATE INDEX IF NOT EXISTS ix_rating_participants
ON album_rating_participants(album_rating_id);
CREATE INDEX IF NOT EXISTS ix_ratings_track ON ratings(track_id);
CREATE INDEX IF NOT EXISTS ix_ratings_participant
ON ratings(album_rating_participant_id);
