from pathlib import Path
import sqlite3

CURRENT_SCHEMA_VERSION = 2
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

def migrate(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        )
    """)

    row = conn.execute(
        "SELECT MAX(version) AS version FROM schema_version"
    ).fetchone()
    current = row["version"] if row and row["version"] is not None else 0

    if current > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database version {current} is newer than supported "
            f"version {CURRENT_SCHEMA_VERSION}."
        )

    if current == 0:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.execute(
            "INSERT OR REPLACE INTO schema_version(version) VALUES (?)",
            (CURRENT_SCHEMA_VERSION,),
        )
        conn.commit()
        return

    if current < 2:
        conn.execute("ALTER TABLE artists ADD COLUMN region TEXT")
        conn.execute("ALTER TABLE albums ADD COLUMN region TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_artists_region ON artists(region)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_albums_region ON albums(region)")
        conn.execute("UPDATE schema_version SET version = 2")
        conn.commit()
