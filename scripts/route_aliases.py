from fastapi import FastAPI
from fastapi.routing import APIRoute
import logging

logger = logging.getLogger("sltweb")

# ===============================
# REMOVE PREFIXOS DUPLICADOS
# ===============================
def normalize_routes(app: FastAPI):
    new_routes = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            new_routes.append(route)
            continue

        original_path = route.path

        # Corrige padrões /empresas/empresas → /empresas
        normalized_path = original_path
        parts = original_path.strip("/").split("/")

        if len(parts) >= 2 and parts[-1] == parts[-2]:
            normalized_path = "/" + "/".join(parts[:-1])

        # Se mudou, cria alias
        if normalized_path != original_path:
            logger.warning(
                f"🔁 Alias criado: {original_path} → {normalized_path}"
            )

            alias_route = APIRoute(
                path=normalized_path,
                endpoint=route.endpoint,
                methods=route.methods,
                name=f"{route.name}_alias",
                response_model=route.response_model,
                dependencies=route.dependencies,
                summary=route.summary,
                description=route.description,
                response_description=route.response_description,
                tags=route.tags,
            )

            new_routes.append(alias_route)

        new_routes.append(route)

    app.router.routes = new_routes
