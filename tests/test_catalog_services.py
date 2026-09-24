import sqlite3
import unittest
from database.migrations import migrate
from services.artist_service import ArtistService
from services.album_service import AlbumService
from services.track_service import TrackService

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        migrate(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_album_with_artists_and_tracks(self):
        artists = ArtistService(self.conn)
        albums = AlbumService(self.conn)
        tracks = TrackService(self.conn)

        a1 = artists.create("Artist One")
        a2 = artists.create("Artist Two")
        album = albums.create("Album", [a1, a2], 2020, tracks=[("Intro", 1), ("Finale", 2)])

        data = albums.get_details(album)
        self.assertEqual(data["album"]["title"], "Album")
        self.assertEqual([x["id"] for x in data["artists"]], [a1, a2])
        self.assertEqual([x["title"] for x in data["tracks"]], ["Intro", "Finale"])

        tracks.update(data["tracks"][0]["id"], "Opening", 1)
        self.assertEqual(tracks.list_for_album(album)[0]["title"], "Opening")

    def test_duplicate_artist_is_rejected(self):
        artists = ArtistService(self.conn)
        artists.create("Artist")
        with self.assertRaises(ValueError):
            artists.create("artist")

    def test_album_requires_artist(self):
        albums = AlbumService(self.conn)
        with self.assertRaises(ValueError):
            albums.create("Album", [])

if __name__ == "__main__":
    unittest.main()

class LibraryFilterTests(CatalogTests):
    def test_search_matches_track_title_and_preserves_rating_field(self):
        artists = ArtistService(self.conn)
        albums = AlbumService(self.conn)
        artist = artists.create("Search Artist")
        album = albums.create("Some Album", [artist], 2024, "Rock", tracks=[("Unique Track", 1)])
        rows = albums.search("Unique Track")
        self.assertEqual([row["id"] for row in rows], [album])
        self.assertIn("rating_average", rows[0].keys())

    def test_library_filters_by_year_genre_and_artist(self):
        artists = ArtistService(self.conn)
        albums = AlbumService(self.conn)
        a1 = artists.create("A")
        a2 = artists.create("B")
        first = albums.create("First", [a1], 2020, "Rock", tracks=[("One", 1)])
        albums.create("Second", [a2], 2021, "Jazz", tracks=[("Two", 1)])
        rows = albums.list_albums({"year": 2020, "genre": "Rock", "artist_id": a1})
        self.assertEqual([row["id"] for row in rows], [first])


class ExtendedCatalogTests(CatalogTests):
    def test_artist_search_matches_album_and_track(self):
        artists = ArtistService(self.conn)
        albums = AlbumService(self.conn)
        artist = artists.create("Alpha", age=30, main_genre="Rock", region="RU")
        albums.create("Moon Album", [artist], 2020, "Rock", "RU", tracks=[("Unique Song", 1)])
        self.assertEqual([r["id"] for r in artists.search("Moon Album")], [artist])
        self.assertEqual([r["id"] for r in artists.search("Unique Song")], [artist])

    def test_artist_filters_and_album_region_and_participant_count(self):
        artists = ArtistService(self.conn)
        albums = AlbumService(self.conn)
        ru = artists.create("RU Artist", age=30, main_genre="Rock", region="RU")
        ww = artists.create("WW Artist", age=25, main_genre="Jazz", region="WW")
        ru_album = albums.create("RU Album", [ru], 2020, "Rock", "RU", tracks=[("One", 1)])
        ww_album = albums.create("WW Album", [ww], 2021, "Jazz", "WW", tracks=[("Two", 1)])
        self.assertEqual([r["id"] for r in artists.repo.list_all({"region": "RU", "age": 30, "genre": "Rock", "album_count": 1})], [ru])
        self.assertEqual([r["id"] for r in albums.list_albums({"region": "RU"})], [ru_album])
        self.assertEqual([r["id"] for r in albums.list_albums({"region": "WW"})], [ww_album])
        self.assertEqual([r["id"] for r in albums.list_albums({"participant_count": 0})], [ru_album, ww_album])
