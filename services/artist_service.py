import sqlite3
from typing import Optional
from database.repositories.artists import ArtistRepository

class ArtistService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.repo = ArtistRepository(conn)

    def list_artists(self):
        return self.repo.list_all()

    def search(self, query: str):
        return self.repo.list_all() if not query.strip() else self.repo.search(query)

    def get(self, artist_id: int):
        return self.repo.get_by_id(artist_id)

    def create(self, name: str, photo_path=None, age: Optional[int]=None, main_genre=None, region=None) -> int:
        name = self._name(name)
        age = self._age(age)
        self._unique(name)
        with self.conn:
            return self.repo.create(name, photo_path, age, main_genre, self._region(region))

    def update(self, artist_id: int, name: str, photo_path=None, age=None, main_genre=None, region=None) -> None:
        if self.repo.get_by_id(artist_id) is None:
            raise ValueError("Artist does not exist.")
        name = self._name(name)
        age = self._age(age)
        self._unique(name, artist_id)
        with self.conn:
            self.repo.update(artist_id, name, photo_path, age, main_genre, self._region(region))

    def search(self, query: str, filters=None):
        return self.repo.list_all(filters or {}) if not query.strip() else self.repo.search(query, filters or {})

    def filter_options(self):
        return self.repo.filter_options()

    def delete(self, artist_id: int) -> None:
        if self.repo.get_by_id(artist_id) is None:
            raise ValueError("Artist does not exist.")
        with self.conn:
            self.repo.delete(artist_id)

    @staticmethod
    def _name(name):
        name = name.strip()
        if not name:
            raise ValueError("Artist name cannot be empty.")
        return name

    @staticmethod
    def _age(age):
        if age is None:
            return None
        age = int(age)
        if not 0 <= age <= 150:
            raise ValueError("Artist age must be between 0 and 150.")
        return age

    @staticmethod
    def _region(region):
        if region in (None, ""):
            return None
        region = str(region).upper()
        if region not in {"RU", "WW"}:
            raise ValueError("Artist region must be RU or WW.")
        return region

    def _unique(self, name, exclude_id=None):
        row = self.repo.get_by_name(name)
        if row is not None and row["id"] != exclude_id:
            raise ValueError(f"Artist '{name}' already exists.")
