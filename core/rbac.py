from fastapi import Depends, HTTPException, status
from backend.core.security import get_current_user

def admin_required(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return user
