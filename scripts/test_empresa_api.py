import requests
import json

API = "http://localhost:8001/api/empresas"
LOGIN = "http://localhost:8001/api/auth/login"

# Usuário admin
email = "admin@consultslt.com.br"
senha = "Admin@123"

# Login para obter token
resp = requests.post(LOGIN, json={"email": email, "password": senha})
assert resp.status_code == 200, f"Login falhou: {resp.text}"
token = resp.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Listar empresas
r = requests.get(API, headers=headers)
print("Empresas antes:", r.json())

# Criar nova empresa
nova = {
    "razao_social": "EMPRESA TESTE PERSISTENCIA",
    "cnpj": "11.111.111/0001-11",
    "regime": "Simples Nacional",
    "receita_bruta": 100000,
    "fator_r": 10.0,
    "status": "Ativo"
}
cr = requests.post(API, json=nova, headers=headers)
print("Criar empresa:", cr.status_code, cr.text)

# Listar empresas novamente
r2 = requests.get(API, headers=headers)
print("Empresas depois inclusão:", r2.json())

# Excluir empresa criada
empresas = r2.json()
for e in empresas:
    if e.get("razao_social") == "EMPRESA TESTE PERSISTENCIA":
        delr = requests.delete(f"{API}/{e['id']}", headers=headers)
        print("Excluir empresa:", delr.status_code, delr.text)

# Listar empresas final
r3 = requests.get(API, headers=headers)
print("Empresas depois exclusão:", r3.json())
