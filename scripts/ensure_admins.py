from backend.core.database import SessionLocal
from backend.models.usuario import Usuario
from backend.core.security import get_password_hash

ADMINS = [
    ("admin@empresa.com", "admin123"),
    ("william.lucas@sltconsult.com.br", "Slt@2024"),
    ("admin@consultslt.com.br", "Consult@2026"),
]

db = SessionLocal()

for email, senha in ADMINS:
    user = db.query(Usuario).filter_by(email=email).first()
    if not user:
        user = Usuario(
            email=email,
            senha_hash=get_password_hash(senha),
            is_admin=True,
            ativo=True
        )
        db.add(user)

db.commit()
db.close()
print("Admins garantidos com sucesso")
