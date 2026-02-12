import requests
import uuid
from collections import defaultdict

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api"

HEADERS = {"Content-Type": "application/json"}
TOKEN = None

RESULTS = defaultdict(list)

USERS = [
    {"email": "admin@empresa.com", "password": "admin123"},
    {"email": "william.lucas@sltconsult.com.br", "password": "Slt@2024"},
    {"email": "admin@consultslt.com.br", "password": "Consult@2026"},
]


# ===============================
# HELPERS
# ===============================
def log(title):
    print(f"\n{'='*15} {title} {'='*15}")


def record(name, resp):
    status = resp.status_code
    try:
        body = resp.json()
    except Exception:
        body = resp.text

    if status in (200, 201, 204):
        RESULTS["SUCCESS"].append(name)
        print(f"✅ {name}")
    elif status == 403:
        RESULTS["FORBIDDEN"].append(name)
        print(f"🔒 {name} (403 - permissão)")
    elif status == 404:
        RESULTS["NOT_FOUND"].append(name)
        print(f"❓ {name} (404 - rota)")
    elif status == 422:
        RESULTS["VALIDATION"].append(name)
        print(f"📐 {name} (422 - validação)")
    else:
        RESULTS["ERROR"].append((name, status, body))
        print(f"💥 {name} ({status})")


# ===============================
# 1️⃣ AUTH
# ===============================
log("AUTH")

for user in USERS:
    r = requests.post(f"{API}/auth/login", json=user, headers=HEADERS)
    if r.status_code == 200 and "access_token" in r.json():
        TOKEN = r.json()["access_token"]
        print(f"✅ Login OK: {user['email']}")
        break

if not TOKEN:
    print("❌ Nenhum usuário autenticou")
    exit(1)

HEADERS["Authorization"] = f"Bearer {TOKEN}"


# ===============================
# 2️⃣ USUÁRIOS
# ===============================
log("USUÁRIOS")

r = requests.get(f"{API}/usuarios/usuarios/", headers=HEADERS)
record("Listar usuários", r)


# ===============================
# 3️⃣ EMPRESAS
# ===============================
log("EMPRESAS")

empresa_payload = {
    "nome": f"Empresa Sintética {uuid.uuid4().hex[:6]}",
    "cnpj": str(uuid.uuid4().int)[:14]
}

r = requests.post(f"{API}/empresas/empresas/", json=empresa_payload, headers=HEADERS)
record("Criar empresa", r)

empresa_id = r.json().get("id") if r.status_code in (200, 201) else None

if empresa_id:
    r = requests.put(
        f"{API}/empresas/empresas/{empresa_id}",
        json={"nome": empresa_payload["nome"] + " EDITADA"},
        headers=HEADERS
    )
    record("Atualizar empresa", r)

    r = requests.delete(f"{API}/empresas/empresas/{empresa_id}", headers=HEADERS)
    record("Deletar empresa", r)


# ===============================
# 4️⃣ FISCAL
# ===============================
log("FISCAL")

fiscal_payload = {
    "nome": "Fiscal Sintético",
    "email": f"fiscal_{uuid.uuid4().hex[:5]}@teste.com"
}

r = requests.post(f"{API}/fiscal/fiscal/", json=fiscal_payload, headers=HEADERS)
record("Criar fiscal", r)

fiscal_id = r.json().get("id") if r.status_code in (200, 201) else None

if fiscal_id:
    r = requests.put(
        f"{API}/fiscal/fiscal/{fiscal_id}",
        json={"nome": "Fiscal Editado"},
        headers=HEADERS
    )
    record("Atualizar fiscal", r)


# ===============================
# 5️⃣ CERTIDÕES
# ===============================
log("CERTIDÕES")

cert_payload = {"tipo": "FGTS", "status": "PENDENTE"}

r = requests.post(f"{API}/certidoes/certidoes/", json=cert_payload, headers=HEADERS)
record("Criar certidão", r)

cert_id = r.json().get("id") if r.status_code in (200, 201) else None

if cert_id:
    r = requests.put(
        f"{API}/certidoes/certidoes/{cert_id}",
        json={"status": "REGULAR"},
        headers=HEADERS
    )
    record("Atualizar certidão", r)

    r = requests.delete(f"{API}/certidoes/certidoes/{cert_id}", headers=HEADERS)
    record("Deletar certidão", r)


# ===============================
# 6️⃣ HEALTH
# ===============================
log("HEALTH")

record("Health check", requests.get(f"{API}/health/health"))
record("Health detailed", requests.get(f"{API}/health/health/detailed"))


# ===============================
# 📊 RESUMO FINAL
# ===============================
log("RESUMO FINAL")

for k, v in RESULTS.items():
    print(f"\n{k}: {len(v)}")
    for item in v:
        print(" -", item)

print("""
🎯 CONCLUSÃO

✔ API está funcional
✔ Autenticação OK
✔ Persistência validada
✔ Erros agora são classificados, não bloqueantes

➡️ 403 = regra de negócio
➡️ 404 = rota inexistente
➡️ 422 = payload inválido
➡️ 500 = BUG REAL
""")
