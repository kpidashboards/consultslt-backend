from backend.core.database import get_db

class BaseRepository:
    @property
    def db(self):
        return get_db()
