from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
from jose import jwt
import os
import uuid
import bcrypt
import logging

# --------------------------
# Configuração inicial
# --------------------------
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("consultslt")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
MONGO_URL = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("DB_NAME", "consultslt_db")
JWT_SECRET = os.getenv("JWT_SECRET", "consultslt-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 1440))
ENABLE_DB_SEED = os.getenv("ENABLE_DB_SEED", "true").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="ConsultSLT API", version="1.0.0")

# --------------------------
# CORS
# --------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Router
# --------------------------
api_router = APIRouter(prefix="/api")

# --------------------------
# Models
# --------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: str = "USER"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None

# --------------------------
# Admins padrão
# --------------------------
DEFAULT_ADMINS = [
    {"email": "admin@empresa.com", "password": "admin123", "name": "Administrador", "role": "ADMIN"},
    {"email": "william.lucas@sltconsult.com.br", "password": "Slt@2024", "name": "William Lucas", "role": "ADMIN"},
    {"email": "admin@consultslt.com.br", "password": "Consult@2026", "name": "Admin SLT", "role": "ADMIN"},
]

# --------------------------
# Funções auxiliares
# --------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def generate_token(user: dict) -> str:
    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# --------------------------
# Seed de admins
# --------------------------
async def ensure_default_admins():
    if not ENABLE_DB_SEED:
        return
    for admin in DEFAULT_ADMINS:
        exists = await db.users.find_one({"email": admin["email"]})
        if not exists:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": admin["email"],
                "password_hash": hash_password(admin["password"]),
                "name": admin["name"],
                "role": admin["role"],
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"✓ Admin criado: {admin['email']}")

# --------------------------
# Healthcheck (fora do router)
# --------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# --------------------------
# ROTAS /api/auth
# --------------------------
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = generate_token(user)
    return LoginResponse(
        success=True,
        message="Login realizado com sucesso",
        token=token,
        user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
    )

@api_router.post("/auth/register", response_model=LoginResponse)
async def register(data: UserCreate):
    if await db.users.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    user = {
        "id": str(uuid.uuid4()),
        "email": data.email,
        "password_hash": hash_password(data.password),
        "name": data.name,
        "role": data.role,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user)
    token = generate_token(user)
    return LoginResponse(
        success=True,
        message="Usuário criado com sucesso",
        token=token,
        user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
    )

# --------------------------
# CRUD Usuários /api/users
# --------------------------
@api_router.get("/users")
async def list_users():
    users = []
    cursor = db.users.find({})
    async for u in cursor:
        users.append({"id": u["id"], "email": u["email"], "name": u["name"], "role": u["role"], "active": u.get("active", True)})
    return users

@api_router.put("/users/{user_id}", response_model=LoginResponse)
async def update_user(user_id: str, data: UserUpdate):
    update_data = data.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
    result = await db.users.update_one({"id": user_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user = await db.users.find_one({"id": user_id})
    return LoginResponse(success=True, message="Usuário atualizado com sucesso", user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]})

@api_router.delete("/users/{user_id}", response_model=LoginResponse)
async def delete_user(user_id: str):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return LoginResponse(success=True, message="Usuário deletado com sucesso")

# --------------------------
# Root do router
# --------------------------
@api_router.get("/")
async def root():
    return {"status": "ConsultSLT API Online"}

# --------------------------
# Startup
# --------------------------
@app.on_event("startup")
async def startup():
    logger.info("🚀 Iniciando ConsultSLT API")
    await db.command("ping")
    logger.info("✅ MongoDB conectado")
    await ensure_default_admins()
    logger.info("✅ Sistema pronto")

# --------------------------
# Registrar router
# --------------------------
app.include_router(api_router)
