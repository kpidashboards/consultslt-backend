"""
Repository para Empresas
Métodos básicos de persistência no MongoDB
"""
from datetime import datetime
from bson import ObjectId
from backend.repositories.base import BaseRepository

class EmpresaRepository(BaseRepository):
    """
    CRUD repository para empresas
    Sem versionamento complexo - apenas persistência simples
    """

    async def create(self, data):
        """Cria uma nova empresa"""
        if not isinstance(data, dict):
            data = data.model_dump()
        
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = None
        
        result = await self.db.empresas.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def list(self):
        """Lista todas as empresas"""
        cursor = self.db.empresas.find().sort("razao_social", 1)
        return await cursor.to_list(length=None)

    async def get_by_id(self, empresa_id):
        """Obtém uma empresa pelo ID"""
        if isinstance(empresa_id, str):
            empresa_id = ObjectId(empresa_id)
        return await self.db.empresas.find_one({"_id": empresa_id})

    async def get_by_cnpj(self, cnpj):
        """Obtém uma empresa pelo CNPJ"""
        return await self.db.empresas.find_one({"cnpj": cnpj})

    async def update(self, empresa_id, update_data):
        """Atualiza uma empresa"""
        if isinstance(empresa_id, str):
            empresa_id = ObjectId(empresa_id)
        
        if not isinstance(update_data, dict):
            update_data = update_data.model_dump(exclude_none=True)
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.empresas.update_one(
            {"_id": empresa_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return None
        
        return await self.get_by_id(empresa_id)

    async def delete(self, empresa_id):
        """Deleta uma empresa"""
        if isinstance(empresa_id, str):
            empresa_id = ObjectId(empresa_id)
        
        result = await self.db.empresas.delete_one({"_id": empresa_id})
        return result.deleted_count > 0

    async def delete_by_cnpj(self, cnpj):
        """Deleta uma empresa pelo CNPJ"""
        result = await self.db.empresas.delete_one({"cnpj": cnpj})
        return result.deleted_count > 0
