from database.repositories.participants import ParticipantRepository


class ParticipantService:
    def __init__(self, conn):
        self.conn = conn
        self.repo = ParticipantRepository(conn)

    def list_all(self):
        return self.repo.list_all()

    def create(self, name: str) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Имя участника не может быть пустым.")
        with self.conn:
            return self.repo.get_or_create(name)
