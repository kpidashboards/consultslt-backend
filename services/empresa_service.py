from backend.repositories.empresa_repository import EmpresaRepository

class EmpresaService:
    def __init__(self):
        self.repo = EmpresaRepository()

    async def criar(self, payload):
        return await self.repo.create(payload)

    async def listar(self):
        return await self.repo.list()
