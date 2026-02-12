import os
import re
import ast

# --- Configuração dos Caminhos e Nomes de Arquivo ---
# Altere se sua estrutura for diferente
ENV_FILE = ".env"
MAIN_APP_FILE = "main_enterprise.py"
AUTH_ROUTER_FILE = "backend/api/auth.py"
DB_SETUP_FILE = "backend/core/database.py"

# --- Cores para o Terminal ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- Funções de Verificação ---

def check_env_file():
    """Verifica o arquivo .env em busca de chaves inseguras."""
    print(f"{Colors.HEADER}--- Verificando arquivo '{ENV_FILE}' ---{Colors.ENDC}")
    if not os.path.exists(ENV_FILE):
        print(f"{Colors.FAIL}❌ Arquivo '{ENV_FILE}' não encontrado na raiz do projeto.{Colors.ENDC}")
        return False

    found_issues = False
    with open(ENV_FILE, 'r') as f:
        content = f.read()

    secret_key_match = re.search(r"^SECRET_KEY\s*=\s*['\"]?(troque_esta_senha)['\"]?", content, re.MULTILINE)
    if secret_key_match:
        print(f"{Colors.FAIL}❌ Problema de Segurança: A SECRET_KEY em '{ENV_FILE}' é a padrão ('troque_esta_senha'). É crucial trocá-la.{Colors.ENDC}")
        found_issues = True
    else:
        print(f"{Colors.OKGREEN}✅ SECRET_KEY parece ter sido alterada em '{ENV_FILE}'.{Colors.ENDC}")

    if not found_issues:
        print(f"{Colors.OKGREEN}✅ Arquivo '{ENV_FILE}' parece configurado corretamente.{Colors.ENDC}")
    return not found_issues

def check_auth_router():
    """Verifica o router de autenticação em busca de chaves secretas hardcoded."""
    print(f"\n{Colors.HEADER}--- Verificando arquivo '{AUTH_ROUTER_FILE}' ---{Colors.ENDC}")
    if not os.path.exists(AUTH_ROUTER_FILE):
        print(f"{Colors.FAIL}❌ Arquivo '{AUTH_ROUTER_FILE}' não encontrado.{Colors.ENDC}")
        return False

    found_issues = False
    with open(AUTH_ROUTER_FILE, 'r') as f:
        content = f.read()

    # Procura por definições de variáveis como SECRET_KEY = "valor"
    hardcoded_key_match = re.search(r"^\s*SECRET_KEY\s*=\s*['\"].+['\"]", content, re.MULTILINE)
    if hardcoded_key_match:
        print(f"{Colors.FAIL}❌ Problema Crítico: 'SECRET_KEY' está definida diretamente (hardcoded) em '{AUTH_ROUTER_FILE}'.{Colors.ENDC}")
        print(f"{Colors.WARNING}   -> Correção: Remova esta linha e importe a chave de um arquivo de configuração central (ex: backend/core/config.py) que lê do .env.{Colors.ENDC}")
        found_issues = True
    else:
        print(f"{Colors.OKGREEN}✅ 'SECRET_KEY' não parece estar hardcoded em '{AUTH_ROUTER_FILE}'.{Colors.ENDC}")

    if not found_issues:
        print(f"{Colors.OKGREEN}✅ Arquivo '{AUTH_ROUTER_FILE}' passou na verificação de chaves.{Colors.ENDC}")
    return not found_issues

def check_database_setup():
    """Verifica o arquivo de banco de dados em busca de senhas em texto plano."""
    print(f"\n{Colors.HEADER}--- Verificando arquivo '{DB_SETUP_FILE}' ---{Colors.ENDC}")
    if not os.path.exists(DB_SETUP_FILE):
        print(f"{Colors.FAIL}❌ Arquivo '{DB_SETUP_FILE}' não encontrado.{Colors.ENDC}")
        return False

    found_issues = False
    try:
        with open(DB_SETUP_FILE, 'r') as f:
            tree = ast.parse(f.read(), filename=DB_SETUP_FILE)

        for node in ast.walk(tree):
            # Procura pela função init_users
            if isinstance(node, ast.AsyncFunctionDef) and node.name == 'init_users':
                for sub_node in ast.walk(node):
                    # Procura pela chamada db.users.insert_one
                    if (isinstance(sub_node, ast.Call) and
                        hasattr(sub_node.func, 'value') and
                        hasattr(sub_node.func.value, 'value') and
                        hasattr(sub_node.func.value.value, 'id') and
                        sub_node.func.value.value.id == 'db' and
                        hasattr(sub_node.func.value, 'attr') and
                        sub_node.func.value.attr == 'users' and
                        hasattr(sub_node.func, 'attr') and
                        sub_node.func.attr == 'insert_one'):

                        # Verifica se o argumento da inserção contém a chave 'password' vinda diretamente da lista
                        # Esta é uma heurística, mas deve funcionar para o seu caso
                        arg = sub_node.args[0]
                        if isinstance(arg, ast.DictComp) or isinstance(arg, ast.Call): # Ex: {**user}
                             print(f"{Colors.FAIL}❌ Problema de Segurança: A função 'init_users' em '{DB_SETUP_FILE}' parece estar inserindo senhas em texto plano no banco de dados.{Colors.ENDC}")
                             print(f"{Colors.WARNING}   -> Correção: Criptografe a senha com uma função hash (ex: get_password_hash) antes de chamar 'insert_one'.{Colors.ENDC}")
                             found_issues = True
                             break
                if found_issues:
                    break
    except Exception as e:
        print(f"{Colors.WARNING}⚠️ Não foi possível analisar {DB_SETUP_FILE} em detalhes: {e}{Colors.ENDC}")


    if not found_issues:
        print(f"{Colors.OKGREEN}✅ Nenhuma inserção de senha em texto plano detectada em 'init_users'.{Colors.ENDC}")
    return not found_issues


def main():
    """Função principal para rodar todos os diagnósticos."""
    print(f"{Colors.BOLD}{Colors.UNDERLINE}\n🚀 Iniciando Diagnóstico da Aplicação FastAPI 🚀{Colors.ENDC}\n")

    all_ok = True
    if not check_env_file():
        all_ok = False
    if not check_auth_router():
        all_ok = False
    if not check_database_setup():
        all_ok = False

    print(f"\n{Colors.BOLD}--- Resumo do Diagnóstico ---{Colors.ENDC}")
    if all_ok:
        print(f"{Colors.OKGREEN}🎉 Todos os diagnósticos passaram! O código parece estar configurado corretamente em relação aos problemas comuns.{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}🚨 Foram encontrados problemas críticos. Por favor, revise os pontos acima para garantir a segurança e o funcionamento da sua aplicação.{Colors.ENDC}")

if __name__ == "__main__":
    main()
