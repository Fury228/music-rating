from domain.rating import validate_rating
from database.repositories.ratings import RatingRepository
from database.repositories.participants import ParticipantRepository


class RatingService:
    def __init__(self, conn):
        self.conn = conn
        self.repo = RatingRepository(conn)
        self.participants = ParticipantRepository(conn)

    def get_rating(self, album_id: int):
        participants = self.repo.list_rating_participants(album_id)
        ratings = self.repo.list_ratings(album_id)
        values = {
            (row["participant_id"], row["track_id"]):
            (float(row["value"]), bool(row["is_secret"]))
            for row in ratings
        }
        return {"participants": participants, "ratings": values}

    def save_rating(self, album_id: int, participant_ratings: dict[int, list[tuple[int, float, bool]]]) -> None:
        if not participant_ratings:
            raise ValueError("Добавьте хотя бы одного участника.")

        # Сначала полностью валидируем входные данные, и только потом
        # начинаем менять БД. Это особенно важно при переключении 11 -> обычная оценка.
        validated = {}
        for participant_id, ratings in participant_ratings.items():
            secret_count = 0
            normalized = []
            for track_id, value, is_secret in ratings:
                is_secret = bool(is_secret)
                value = validate_rating(value, is_secret)
                secret_count += int(is_secret)
                normalized.append((track_id, value, is_secret))
            if secret_count > 1:
                raise ValueError(
                    "У каждого участника оценка 11 может быть использована только один раз."
                )
            validated[participant_id] = normalized

        with self.conn:
            album_rating_id = self.repo.get_or_create_album_rating(album_id)
            participant_ids = list(validated)
            self.repo.clear_participants(album_rating_id, participant_ids)

            for participant_id, ratings in validated.items():
                link_id = self.repo.get_or_create_participant_link(album_rating_id, participant_id)
                self.repo.delete_all_ratings(link_id)
                for track_id, value, is_secret in ratings:
                    self.repo.upsert_rating(link_id, track_id, value, is_secret)

            self.repo.update_timestamp(album_rating_id)

    def get_summary(self, album_id: int):
        rows = self.repo.list_ratings(album_id)
        participants = self.repo.list_rating_participants(album_id)
        if not rows:
            return {
                "participants": 0,
                "rated": 0,
                "average": None,
                "participants_detail": [],
            }

        by_participant = {}
        for row in rows:
            participant_id = row["participant_id"]
            by_participant.setdefault(participant_id, []).append(float(row["value"]))

        details = []
        for participant in participants:
            participant_id = participant["participant_id"]
            values = by_participant.get(participant_id, [])
            details.append({
                "participant_id": participant_id,
                "name": participant["name"],
                "rated": len(values),
                "average": min(sum(values) / len(values), 10.0) if values else None,
            })

        return {
            "participants": len({row["participant_id"] for row in rows}),
            "rated": len(rows),
            "average": min(sum(float(row["value"]) for row in rows) / len(rows), 10.0),
            "participants_detail": details,
        }
