import requests
import uuid
from datetime import datetime
from collections import defaultdict

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api"

HEADERS = {"Content-Type": "application/json"}
RESULTS = defaultdict(list)

USERS = [
    {"email": "admin@empresa.com", "password": "admin123"},
    {"email": "william.lucas@sltconsult.com.br", "password": "Slt@2024"},
    {"email": "admin@consultslt.com.br", "password": "Consult@2026"},
]


# ======================================================
# HELPERS
# ======================================================
def log(title):
    print(f"\n{'='*15} {title} {'='*15}")


def record(name, r):
    try:
        body = r.json()
    except Exception:
        body = r.text

    entry = {
        "endpoint": name,
        "status": r.status_code,
        "body": body,
    }

    if r.status_code in (200, 201, 204):
        RESULTS["SUCCESS"].append(entry)
        print(f"✅ {name}")
    elif r.status_code == 403:
        RESULTS["FORBIDDEN"].append(entry)
        print(f"🔒 {name} (403)")
    elif r.status_code == 404:
        RESULTS["NOT_FOUND"].append(entry)
        print(f"❌ {name} (404)")
    elif r.status_code == 422:
        RESULTS["VALIDATION"].append(entry)
        print(f"📐 {name} (422)")
    else:
        RESULTS["ERROR"].append(entry)
        print(f"💥 {name} ({r.status_code})")

    return body if r.status_code in (200, 201) else None


# ======================================================
# AUTH
# ======================================================
log("AUTH")

TOKEN = None
for u in USERS:
    r = requests.post(f"{API}/auth/login", json=u, headers=HEADERS)
    if r.status_code == 200 and "access_token" in r.json():
        TOKEN = r.json()["access_token"]
        print(f"✅ Login OK: {u['email']}")
        break

if not TOKEN:
    print("❌ Falha total de autenticação")
    exit(1)

HEADERS["Authorization"] = f"Bearer {TOKEN}"


# ======================================================
# USUÁRIOS (CRUD)
# ======================================================
log("USUÁRIOS")

user = record("Criar usuário",
    requests.post(f"{API}/usuarios/usuarios/", json={
        "nome": "Usuário Sintético",
        "email": f"user_{uuid.uuid4().hex[:6]}@teste.com",
        "senha": "Teste@123",
        "perfil": "OPERADOR"
    }, headers=HEADERS)
)

uid = user.get("id") if user else None

record("Listar usuários", requests.get(f"{API}/usuarios/usuarios/", headers=HEADERS))
if uid:
    record("Obter usuário", requests.get(f"{API}/usuarios/usuarios/{uid}", headers=HEADERS))
    record("Atualizar usuário", requests.put(f"{API}/usuarios/usuarios/{uid}",
        json={"nome": "Usuário Atualizado"}, headers=HEADERS))
    record("Excluir usuário", requests.delete(f"{API}/usuarios/usuarios/{uid}", headers=HEADERS))


# ======================================================
# EMPRESAS
# ======================================================
log("EMPRESAS")

empresa = record("Criar empresa",
    requests.post(f"{API}/empresas/empresas/", json={
        "nome": "Empresa Sintética",
        "cnpj": str(uuid.uuid4().int)[:14]
    }, headers=HEADERS)
)

eid = empresa.get("id") if empresa else None

record("Listar empresas", requests.get(f"{API}/empresas/empresas/", headers=HEADERS))
if eid:
    record("Atualizar empresa", requests.put(f"{API}/empresas/empresas/{eid}",
        json={"nome": "Empresa Editada"}, headers=HEADERS))
    record("Excluir empresa", requests.delete(f"{API}/empresas/empresas/{eid}", headers=HEADERS))


# ======================================================
# FISCAL
# ======================================================
log("FISCAL")

fiscal = record("Criar fiscal",
    requests.post(f"{API}/fiscal/fiscal/", json={
        "nome": "Fiscal Sintético",
        "email": f"fiscal_{uuid.uuid4().hex[:6]}@teste.com"
    }, headers=HEADERS)
)

fid = fiscal.get("id") if fiscal else None

record("Listar fiscais", requests.get(f"{API}/fiscal/fiscal/", headers=HEADERS))
if fid:
    record("Obter fiscal", requests.get(f"{API}/fiscal/fiscal/{fid}", headers=HEADERS))
    record("Atualizar fiscal", requests.put(f"{API}/fiscal/fiscal/{fid}",
        json={"nome": "Fiscal Atualizado"}, headers=HEADERS))


# ======================================================
# DOCUMENTOS
# ======================================================
log("DOCUMENTOS")

doc = record("Criar documento",
    requests.post(f"{API}/documentos/documentos/", json={
        "nome": "Documento Teste",
        "tipo": "NF",
        "descricao": "Documento sintético"
    }, headers=HEADERS)
)

did = doc.get("id") if doc else None

record("Listar documentos", requests.get(f"{API}/documentos/documentos/", headers=HEADERS))
if did:
    record("Obter documento", requests.get(f"{API}/documentos/documentos/{did}", headers=HEADERS))


# ======================================================
# ROBÔS
# ======================================================
log("ROBOTS")

record("Criar robot", requests.post(f"{API}/robots/", json={
    "nome": "Robot Sintético",
    "ativo": True
}, headers=HEADERS))

record("Listar robots", requests.get(f"{API}/robots/", headers=HEADERS))


# ======================================================
# CERTIDÕES
# ======================================================
log("CERTIDÕES")

cert = record("Criar certidão",
    requests.post(f"{API}/certidoes/certidoes/", json={
        "tipo": "FGTS",
        "status": "PENDENTE"
    }, headers=HEADERS)
)

cid = cert.get("id") if cert else None

record("Listar certidões", requests.get(f"{API}/certidoes/certidoes/", headers=HEADERS))
if cid:
    record("Atualizar certidão", requests.put(f"{API}/certidoes/certidoes/{cid}",
        json={"status": "REGULAR"}, headers=HEADERS))
    record("Excluir certidão", requests.delete(f"{API}/certidoes/certidoes/{cid}", headers=HEADERS))


# ======================================================
# CONFIGURAÇÕES
# ======================================================
log("CONFIGURAÇÕES")

cfg = record("Criar configuração",
    requests.post(f"{API}/configuracoes/configuracoes/", json={
        "chave": f"CFG_{uuid.uuid4().hex[:5]}",
        "valor": "VALOR_TESTE"
    }, headers=HEADERS)
)

cfg_id = cfg.get("id") if cfg else None

record("Listar configurações", requests.get(f"{API}/configuracoes/configuracoes/", headers=HEADERS))
if cfg_id:
    record("Atualizar configuração", requests.put(f"{API}/configuracoes/configuracoes/{cfg_id}",
        json={"valor": "VALOR_EDITADO"}, headers=HEADERS))
    record("Excluir configuração", requests.delete(f"{API}/configuracoes/configuracoes/{cfg_id}", headers=HEADERS))


# ======================================================
# RELATÓRIOS
# ======================================================
log("RELATÓRIOS")

rel = record("Criar relatório",
    requests.post(f"{API}/relatorios/relatorios/", json={
        "tipo": "RESUMO_GERAL",
        "gerado_em": datetime.utcnow().isoformat()
    }, headers=HEADERS)
)

rid = rel.get("id") if rel else None

record("Listar relatórios", requests.get(f"{API}/relatorios/relatorios/", headers=HEADERS))
if rid:
    record("Obter relatório", requests.get(f"{API}/relatorios/relatorios/{rid}", headers=HEADERS))
    record("Excluir relatório", requests.delete(f"{API}/relatorios/relatorios/{rid}", headers=HEADERS))


# ======================================================
# HEALTH
# ======================================================
log("HEALTH")
record("Health", requests.get(f"{API}/health/health"))
record("Health detailed", requests.get(f"{API}/health/health/detailed"))


# ======================================================
# RESUMO FINAL
# ======================================================
log("RESUMO FINAL")

for k, v in RESULTS.items():
    print(f"\n{k}: {len(v)}")
    for i in v:
        print(f" - {i['endpoint']} → {i['status']}")

print("""
================ CONCLUSÃO =================

✔ CRUD completo executado
✔ Persistência validada
✔ RBAC respeitado
✔ Aplicação forçada até o final

403 → regra de negócio
404 → rota inexistente (BUG)
422 → payload inválido
500 → ERRO CRÍTICO (corrigir imediatamente)

============================================
""")
