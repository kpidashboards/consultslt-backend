from fastapi import FastAPI
from fastapi.routing import APIRoute


def normalize_routes(app: FastAPI):
    """
    Cria aliases automáticos para evitar 404 causados por
    prefixos duplicados como:
    /api/empresas/empresas
    /api/obrigacoes/obrigacoes
    """

    existing_routes = list(app.router.routes)
    created_aliases = []

    for route in existing_routes:
        if not isinstance(route, APIRoute):
            continue

        path = route.path

        # Ex: /api/empresas/empresas
        parts = path.strip("/").split("/")

        if len(parts) >= 3 and parts[-1] == parts[-2]:
            alias_path = "/" + "/".join(parts[:-1])

            if alias_path not in [r.path for r in app.router.routes]:
                app.add_api_route(
                    alias_path,
                    route.endpoint,
                    methods=route.methods,
                    tags=route.tags,
                    dependencies=route.dependencies,
                    response_model=route.response_model,
                    summary=f"[ALIAS] {route.summary}",
                )
                created_aliases.append(alias_path)

    if created_aliases:
        print("🧭 Rotas alias criadas automaticamente:")
        for a in created_aliases:
            print(f"   → {a}")
