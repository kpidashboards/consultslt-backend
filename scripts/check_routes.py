import sys
import os

# ===============================
# AJUSTA O PYTHONPATH
# ===============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# ===============================
# IMPORTA A APP CORRETA
# ===============================
from main_enterprise import app

# ===============================
# LISTA ROTAS
# ===============================
print("\n🚦 ROTAS REGISTRADAS NA APLICAÇÃO:\n")

for route in app.routes:
    methods = ",".join(route.methods) if hasattr(route, "methods") else "N/A"
    print(f"{methods:10s} {route.path}")
