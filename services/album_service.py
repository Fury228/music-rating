from database.repositories.albums import AlbumRepository
from database.repositories.tracks import TrackRepository
from database.repositories.artists import ArtistRepository


class AlbumService:
    def __init__(self, conn):
        self.conn = conn
        self.repo = AlbumRepository(conn)
        self.tracks = TrackRepository(conn)
        self.artists = ArtistRepository(conn)

    def list_albums(self, filters=None):
        return self.repo.list_all(filters or {})

    def search(self, query: str, filters=None):
        filters = filters or {}
        return self.repo.search(query, filters)

    def filter_options(self):
        return self.repo.filter_options()

    def get(self, album_id: int):
        return self.repo.get_by_id(album_id)

    def get_details(self, album_id: int):
        data = self.repo.get_with_artists(album_id)
        if data is None:
            return None
        data["tracks"] = self.tracks.list_for_album(album_id)
        return data

    def create(self, title, artist_ids, year=None, genre=None, region=None, cover_path=None, tracks=None):
        title, artist_ids, year = self._validate(title, artist_ids, year)
        self._artists_exist(artist_ids)
        with self.conn:
            album_id = self.repo.create(title, year, genre, self._region(region), cover_path)
            self.repo.set_artists(album_id, artist_ids)
            if tracks is not None:
                self._replace_tracks(album_id, tracks)
            return album_id

    def update(self, album_id, title, artist_ids, year=None, genre=None, region=None, cover_path=None, tracks=None):
        if self.repo.get_by_id(album_id) is None:
            raise ValueError("Album does not exist.")
        title, artist_ids, year = self._validate(title, artist_ids, year)
        self._artists_exist(artist_ids)
        with self.conn:
            self.repo.update(album_id, title, year, genre, self._region(region), cover_path)
            self.repo.set_artists(album_id, artist_ids)
            if tracks is not None:
                self._replace_tracks(album_id, tracks)

    def delete(self, album_id):
        if self.repo.get_by_id(album_id) is None:
            raise ValueError("Album does not exist.")
        with self.conn:
            self.repo.delete(album_id)

    def _replace_tracks(self, album_id, tracks):
        normalized, numbers = [], set()
        for title, number in tracks:
            title = title.strip()
            number = int(number)
            if not title:
                raise ValueError("Track title cannot be empty.")
            if number < 1:
                raise ValueError("Track number must be at least 1.")
            if number in numbers:
                raise ValueError(f"Duplicate track number: {number}.")
            numbers.add(number)
            normalized.append((title, number))
        normalized.sort(key=lambda x: x[1])
        self.tracks.delete_for_album(album_id)
        for title, number in normalized:
            self.tracks.create(album_id, title, number)

    @staticmethod
    def _region(region):
        if region in (None, ""):
            return None
        region = str(region).upper()
        if region not in {"RU", "WW"}:
            raise ValueError("Album region must be RU or WW.")
        return region

    @staticmethod
    def _validate(title, artist_ids, year):
        title = title.strip()
        if not title:
            raise ValueError("Album title cannot be empty.")
        artist_ids = list(dict.fromkeys(int(x) for x in artist_ids))
        if not artist_ids:
            raise ValueError("Album must have at least one artist.")
        if year is not None:
            year = int(year)
            if not 0 <= year <= 3000:
                raise ValueError("Album year is out of range.")
        return title, artist_ids, year

    def _artists_exist(self, artist_ids):
        missing = [x for x in artist_ids if self.artists.get_by_id(x) is None]
        if missing:
            raise ValueError(f"Unknown artist IDs: {missing}.")
