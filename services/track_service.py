import sqlite3
from database.repositories.albums import AlbumRepository
from database.repositories.tracks import TrackRepository

class TrackService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.repo = TrackRepository(conn)
        self.albums = AlbumRepository(conn)

    def list_for_album(self, album_id: int):
        self._album(album_id)
        return self.repo.list_for_album(album_id)

    def create(self, album_id: int, title: str, track_number: int) -> int:
        self._album(album_id)
        title = self._title(title)
        number = self._number(track_number)
        with self.conn:
            return self.repo.create(album_id, title, number)

    def update(self, track_id: int, title: str, track_number: int) -> None:
        if self.repo.get_by_id(track_id) is None:
            raise ValueError("Track does not exist.")
        with self.conn:
            self.repo.update(track_id, self._title(title), self._number(track_number))

    def delete(self, track_id: int) -> None:
        if self.repo.get_by_id(track_id) is None:
            raise ValueError("Track does not exist.")
        with self.conn:
            self.repo.delete(track_id)

    @staticmethod
    def _title(title):
        title = title.strip()
        if not title:
            raise ValueError("Track title cannot be empty.")
        return title

    @staticmethod
    def _number(number):
        number = int(number)
        if number < 1:
            raise ValueError("Track number must be at least 1.")
        return number

    def _album(self, album_id):
        if self.albums.get_by_id(album_id) is None:
            raise ValueError("Album does not exist.")
