import sqlite3
import unittest

from database.migrations import migrate
from services.artist_service import ArtistService
from services.album_service import AlbumService
from services.participant_service import ParticipantService
from services.rating_service import RatingService


class RatingServiceTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        migrate(self.conn)
        artists = ArtistService(self.conn)
        albums = AlbumService(self.conn)
        artist = artists.create("Artist")
        self.album_id = albums.create(
            "After Hours", [artist], 2020,
            tracks=[("Intro", 1), ("Finale", 2)],
        )
        self.tracks = albums.get_details(self.album_id)["tracks"]
        self.participants = ParticipantService(self.conn)
        self.ratings = RatingService(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_save_and_load_rating_with_one_secret(self):
        p1 = self.participants.create("Alice")
        self.ratings.save_rating(self.album_id, {
            p1: [
                (self.tracks[0]["id"], 7.8, False),
                (self.tracks[1]["id"], 11.0, True),
            ]
        })
        data = self.ratings.get_rating(self.album_id)
        self.assertEqual(data["ratings"][(p1, self.tracks[0]["id"])], (7.8, False))
        self.assertEqual(data["ratings"][(p1, self.tracks[1]["id"])], (11.0, True))


    def test_save_without_secret_rating_is_allowed(self):
        p1 = self.participants.create("Alice")
        self.ratings.save_rating(self.album_id, {
            p1: [
                (self.tracks[0]["id"], 4.0, False),
                (self.tracks[1]["id"], 5.0, False),
            ]
        })
        data = self.ratings.get_rating(self.album_id)
        self.assertEqual(data["ratings"][(p1, self.tracks[0]["id"])], (4.0, False))
        self.assertEqual(data["ratings"][(p1, self.tracks[1]["id"])], (5.0, False))

    def test_secret_is_independent_per_participant(self):
        p1 = self.participants.create("Volodya")
        p2 = self.participants.create("Goga")
        self.ratings.save_rating(self.album_id, {
            p1: [
                (self.tracks[0]["id"], 11.0, True),
                (self.tracks[1]["id"], 7.0, False),
            ],
            p2: [
                (self.tracks[0]["id"], 10.0, False),
                (self.tracks[1]["id"], 8.0, False),
            ],
        })
        data = self.ratings.get_rating(self.album_id)
        self.assertEqual(data["ratings"][(p1, self.tracks[0]["id"])], (11.0, True))
        self.assertEqual(data["ratings"][(p2, self.tracks[0]["id"])], (10.0, False))

    def test_second_secret_for_same_participant_is_rejected(self):
        p1 = self.participants.create("Alice")
        with self.assertRaises(Exception):
            self.ratings.save_rating(self.album_id, {
                p1: [
                    (self.tracks[0]["id"], 11.0, True),
                    (self.tracks[1]["id"], 11.0, True),
                ]
            })

    def test_rating_can_be_edited(self):
        p1 = self.participants.create("Alice")
        self.ratings.save_rating(self.album_id, {
            p1: [
                (self.tracks[0]["id"], 7.0, False),
                (self.tracks[1]["id"], 11.0, True),
            ]
        })
        self.ratings.save_rating(self.album_id, {
            p1: [
                (self.tracks[0]["id"], 11.0, True),
                (self.tracks[1]["id"], 9.2, False),
            ]
        })
        data = self.ratings.get_rating(self.album_id)
        self.assertEqual(data["ratings"][(p1, self.tracks[0]["id"])], (11.0, True))
        self.assertEqual(data["ratings"][(p1, self.tracks[1]["id"])], (9.2, False))

    def test_duplicate_album_titles_are_allowed(self):
        artists = ArtistService(self.conn)
        artist2 = artists.create("Another Artist")
        albums = AlbumService(self.conn)
        second = albums.create("After Hours", [artist2], 2024, tracks=[("One", 1)])
        self.assertNotEqual(second, self.album_id)


if __name__ == "__main__":
    unittest.main()

class RatingSummaryCapTests(RatingServiceTests):
    def test_secret_eleven_is_capped_to_ten_in_album_and_participant_average(self):
        p1 = self.participants.create("Alice")
        self.ratings.save_rating(self.album_id, {
            p1: [
                (self.tracks[0]["id"], 11.0, True),
                (self.tracks[1]["id"], 10.0, False),
            ]
        })
        summary = self.ratings.get_summary(self.album_id)
        self.assertEqual(summary["average"], 10.0)
        self.assertEqual(summary["participants_detail"][0]["average"], 10.0)
