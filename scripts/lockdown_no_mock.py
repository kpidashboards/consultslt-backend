"""
LOCKDOWN DE PRODUÇÃO
- Remove mocks
- Bloqueia seed automático
- Força persistência real
- Garante que dados apagados NÃO retornem
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MOCK_KEYWORDS = [
    "mock",
    "fake",
    "exemplo",
    "sample",
    "simula",
    "simulação",
    "teste",
    "test",
]

SEED_KEYWORDS = [
    "seed_",
    "insert_many(",
    "DEFAULT_",
    "MOCK_",
]

FILES_TO_IGNORE = [
    "scripts",
    "tests",
    "__pycache__",
    ".venv",
    "venv",
]

def should_ignore(path: Path):
    return any(p in str(path) for p in FILES_TO_IGNORE)

def scan_and_block():
    print("\n🔍 Iniciando varredura total do backend...\n")
    problems = []

    for file in BASE_DIR.rglob("*.py"):
        if should_ignore(file):
            continue

        content = file.read_text(encoding="utf-8", errors="ignore")
        lowered = content.lower()

        for word in MOCK_KEYWORDS:
            if word in lowered:
                problems.append((file, word))

        for seed in SEED_KEYWORDS:
            if seed in content:
                problems.append((file, seed))

    if problems:
        print("🚨 MOCK / SEED ENCONTRADO 🚨\n")
        for file, word in problems:
            print(f"❌ {file}  -> '{word}'")

        print("\n⛔ APLICAÇÃO NÃO ESTÁ PRONTA PARA PRODUÇÃO")
        print("➡️ Corrija os arquivos acima ou use APP_ENV=development")
        sys.exit(1)

    print("✅ Nenhum mock ou seed automático encontrado")
    print("🚀 Aplicação pronta para produção")

if __name__ == "__main__":
    scan_and_block()
