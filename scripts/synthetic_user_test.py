import requests
import sys

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api"

HEADERS = {"Content-Type": "application/json"}
TOKEN = None

USERS = [
    {"email": "admin@empresa.com", "password": "admin123"},
    {"email": "william.lucas@sltconsult.com.br", "password": "Slt@2024"},
    {"email": "admin@consultslt.com.br", "password": "Consult@2026"},
]


def log(title):
    print(f"\n{'=' * 12} {title} {'=' * 12}")


def fail(msg):
    print(f"❌ FALHA: {msg}")
    sys.exit(1)


def ok(msg):
    print(f"✅ {msg}")


# =========================
# 1️⃣ LOGIN (REAL)
# =========================
log("LOGIN ADMIN REAL")

for user in USERS:
    r = requests.post(f"{API}/auth/login", json=user, headers=HEADERS)
    if r.status_code == 200:
        TOKEN = r.json().get("access_token")
        if TOKEN:
            ok(f"Login OK -> {user['email']}")
            break

if not TOKEN:
    fail("Nenhum usuário admin conseguiu autenticar")

HEADERS["Authorization"] = f"Bearer {TOKEN}"


# =========================
# 2️⃣ CREATE ALERTA
# =========================
log("CREATE ALERTA")

payload = {
    "titulo": "Alerta Sintético Produção",
    "descricao": "Criado por usuário admin real",
    "criticidade": "ALTA"
}

r = requests.post(f"{API}/alertas", json=payload, headers=HEADERS)

if r.status_code not in (200, 201):
    fail("POST /alertas falhou")

alerta = r.json()
alerta_id = alerta.get("id")

if not alerta_id:
    fail("ID do alerta não retornado")

ok(f"Alerta criado ID={alerta_id}")


# =========================
# 3️⃣ READ ALERTAS
# =========================
log("LIST ALERTAS")

r = requests.get(f"{API}/alertas", headers=HEADERS)

if r.status_code != 200:
    fail("GET /alertas falhou")

alertas = r.json()

if not any(a["id"] == alerta_id for a in alertas):
    fail("Alerta não persistiu no banco")

ok("Listagem e persistência OK")


# =========================
# 4️⃣ UPDATE ALERTA
# =========================
log("UPDATE ALERTA")

update_payload = {
    "titulo": "Alerta Atualizado",
    "descricao": "Editado por teste sintético",
    "criticidade": "MEDIA"
}

r = requests.put(
    f"{API}/alertas/{alerta_id}",
    json=update_payload,
    headers=HEADERS
)

if r.status_code != 200:
    fail("PUT /alertas/{id} falhou")

ok("Update OK")


# =========================
# 5️⃣ DELETE ALERTA
# =========================
log("DELETE ALERTA")

r = requests.delete(f"{API}/alertas/{alerta_id}", headers=HEADERS)

if r.status_code not in (200, 204):
    fail("DELETE /alertas/{id} falhou")

ok("Delete OK")


# =========================
# 6️⃣ CONFIRMA DELETE
# =========================
log("CONFIRM DELETE")

r = requests.get(f"{API}/alertas", headers=HEADERS)

if any(a["id"] == alerta_id for a in r.json()):
    fail("Alerta não foi removido do banco")

ok("Remoção persistente confirmada")


# =========================
# FINAL
# =========================
log("RESULTADO FINAL")
print("🎉 BACKEND, API E BANCO TOTALMENTE FUNCIONAIS EM PRODUÇÃO")
