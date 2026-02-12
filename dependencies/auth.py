from fastapi import Depends, HTTPException, status
from backend.core.security import decode_token
from backend.core.database import get_db


async def get_current_user(token: str = Depends(decode_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    db = get_db()
    user = await db.users.find_one({"email": token.get("sub")})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )

    user["id"] = str(user["_id"])
    return user