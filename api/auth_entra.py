from fastapi import APIRouter, Request

router = APIRouter(prefix="/auth/entra", tags=["Auth EntraID"])

@router.get("/callback")
async def entra_callback(request: Request):
    # Placeholder para integração futura com Entra ID (Azure AD)
    return {"message": "Callback Entra ID recebido. Integração futura."}
