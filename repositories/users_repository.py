from backend.core.database import get_db
from passlib.context import CryptContext
from typing import Optional
import datetime
import uuid


class UsersRepository:
    def __init__(self):
        self.collection = get_db().users
        self.history_collection = get_db().users_history
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def get_by_email(self, email: str) -> Optional[dict]:
        return await self.collection.find_one({"email": email, "valid_to": None})

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    async def create_user(
        self,
        nome: str,
        email: str,
        senha: str,
        role: str = "viewer",
        ativo: bool = True,
        created_by: Optional[str] = None
    ) -> dict:
        now = datetime.datetime.utcnow()
        hashed_password = self.pwd_context.hash(senha)
        entity_id = str(uuid.uuid4())

        user_doc = {
            "nome": nome,
            "email": email,
            "password": hashed_password,
            "role": role,
            "ativo": ativo,
            "entity_id": entity_id,
            "version": 1,
            "created_at": now,
            "created_by": created_by,
            "valid_from": now,
            "valid_to": None,
            "previous_version_id": None
        }

        result = await self.collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return user_doc

    async def update_user(
        self,
        user_id,
        update_data: dict,
        updated_by: Optional[str] = None
    ) -> Optional[dict]:
        now = datetime.datetime.utcnow()

        current = await self.collection.find_one({"_id": user_id, "valid_to": None})
        if not current:
            return None

        current["valid_to"] = now
        await self.history_collection.insert_one(current)

        new_version = current.copy()
        new_version.update(update_data)
        new_version["version"] = current.get("version", 1) + 1
        new_version["created_at"] = current["created_at"]
        new_version["created_by"] = current.get("created_by")
        new_version["valid_from"] = now
        new_version["valid_to"] = None
        new_version["previous_version_id"] = current["_id"]

        new_version.pop("_id", None)

        result = await self.collection.insert_one(new_version)
        new_version["_id"] = result.inserted_id
        return new_version

    async def deactivate_user(
        self,
        user_id,
        deactivated_by: Optional[str] = None
    ) -> Optional[dict]:
        now = datetime.datetime.utcnow()

        current = await self.collection.find_one({"_id": user_id, "valid_to": None})
        if not current:
            return None

        current["valid_to"] = now
        await self.history_collection.insert_one(current)

        new_version = current.copy()
        new_version["ativo"] = False
        new_version["version"] = current.get("version", 1) + 1
        new_version["created_at"] = current["created_at"]
        new_version["created_by"] = current.get("created_by")
        new_version["valid_from"] = now
        new_version["valid_to"] = None
        new_version["previous_version_id"] = current["_id"]

        new_version.pop("_id", None)

        result = await self.collection.insert_one(new_version)
        new_version["_id"] = result.inserted_id
        return new_version
