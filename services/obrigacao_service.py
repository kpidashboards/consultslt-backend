"""
Serviço de Obrigações Fiscais
Gerencia obrigações, vencimentos e alertas
"""

import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

# ✅ IMPORT RELATIVO CORRETO (padrão backend)
from ..repositories.obrigacoes_repository import ObrigacoesRepository

# ✅ IMPORT RELATIVO DOS SCHEMAS
from ..schemas.obrigacao import (
    TipoObrigacao,
    StatusObrigacao,
    PrioridadeObrigacao,
    ObrigacaoCreate,
    ObrigacaoUpdate,
    ObrigacaoResponse
)

logger = logging.getLogger(__name__)


class ObrigacaoService:
    """
    Serviço para gerenciamento de obrigações fiscais
    """

    def __init__(self):
        self.repo = ObrigacoesRepository()

    async def criar_obrigacao(self, dados: ObrigacaoCreate) -> ObrigacaoResponse:
        """
        Cria uma nova obrigação fiscal
        """
        obrigacao_id = str(uuid.uuid4())

        prioridade = self._calcular_prioridade(dados.data_vencimento)

        obrigacao = {
            "id": obrigacao_id,
            "tipo": dados.tipo.value,
            "empresa_id": dados.empresa_id,
            "cnpj": dados.cnpj,
            "competencia": dados.competencia,
            "ano": dados.ano,
            "mes": dados.mes,
            "valor": dados.valor,
            "valor_pago": 0.0,
            "data_vencimento": dados.data_vencimento.isoformat() if dados.data_vencimento else None,
            "data_pagamento": None,
            "status": StatusObrigacao.PENDENTE.value,
            "prioridade": prioridade.value,
            "documento_ids": [],
            "observacoes": dados.observacoes,
            "created_at": datetime.utcnow(),
            "updated_at": None
        }

        obrigacao_criada = await self.repo.create_obrigacao(obrigacao)
        return ObrigacaoResponse(**obrigacao_criada)

    async def atualizar_obrigacao(
        self,
        obrigacao_id: str,
        dados: ObrigacaoUpdate
    ) -> Optional[ObrigacaoResponse]:
        """
        Atualiza uma obrigação existente
        """
        obrigacao = await self.repo.get_obrigacao_by_id(obrigacao_id)
        if not obrigacao:
            return None

        update_data: Dict[str, Any] = {
            "updated_at": datetime.utcnow()
        }

        if dados.status is not None:
            update_data["status"] = dados.status.value

        if dados.valor is not None:
            update_data["valor"] = dados.valor

        if dados.data_vencimento is not None:
            update_data["data_vencimento"] = dados.data_vencimento.isoformat()
            update_data["prioridade"] = self._calcular_prioridade(
                dados.data_vencimento
            ).value

        if dados.data_pagamento is not None:
            update_data["data_pagamento"] = dados.data_pagamento.isoformat()
            update_data["status"] = StatusObrigacao.CONCLUIDA.value

        if dados.prioridade is not None:
            update_data["prioridade"] = dados.prioridade.value

        if dados.observacoes is not None:
            update_data["observacoes"] = dados.observacoes

        obrigacao_atualizada = await self.repo.update_obrigacao(
            obrigacao_id,
            update_data
        )

        return ObrigacaoResponse(**obrigacao_atualizada)

    async def obter_obrigacao(self, obrigacao_id: str) -> Optional[ObrigacaoResponse]:
        """
        Obtém uma obrigação pelo ID
        """
        obrigacao = await self.repo.get_obrigacao_by_id(obrigacao_id)
        if not obrigacao:
            return None
        return ObrigacaoResponse(**obrigacao)

    async def listar_obrigacoes(
        self,
        empresa_id: Optional[str] = None,
        tipo: Optional[TipoObrigacao] = None,
        status: Optional[StatusObrigacao] = None,
        cnpj: Optional[str] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        pagina: int = 1,
        por_pagina: int = 20
    ) -> Dict[str, Any]:
        """
        Lista obrigações com filtros e paginação
        """
        filtro: Dict[str, Any] = {}

        if empresa_id:
            filtro["empresa_id"] = empresa_id
        if tipo:
            filtro["tipo"] = tipo.value
        if status:
            filtro["status"] = status.value
        if cnpj:
            filtro["cnpj"] = cnpj

        if data_inicio or data_fim:
            filtro["data_vencimento"] = {}
            if data_inicio:
                filtro["data_vencimento"]["$gte"] = data_inicio.isoformat()
            if data_fim:
                filtro["data_vencimento"]["$lte"] = data_fim.isoformat()

        skip = (pagina - 1) * por_pagina

        obrigacoes, total = await self.repo.list_obrigacoes(
            filtro,
            skip,
            por_pagina
        )

        return {
            "obrigacoes": obrigacoes,
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina
        }

    async def obter_proximos_vencimentos(
        self,
        dias: int = 30,
        empresa_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém obrigações com vencimento próximo
        """
        hoje = date.today()
        data_limite = hoje + timedelta(days=dias)

        filtro = {
            "status": {
                "$in": [
                    StatusObrigacao.PENDENTE.value,
                    StatusObrigacao.EM_ANDAMENTO.value
                ]
            },
            "data_vencimento": {
                "$gte": hoje.isoformat(),
                "$lte": data_limite.isoformat()
            }
        }

        if empresa_id:
            filtro["empresa_id"] = empresa_id

        return await self.repo.list_proximos_vencimentos(filtro, 100)

    async def atualizar_status_atrasados(self) -> int:
        """
        Atualiza status de obrigações atrasadas
        """
        return await self.repo.update_status_atrasados()

    async def deletar_obrigacao(self, obrigacao_id: str) -> bool:
        """
        Deleta uma obrigação
        """
        return await self.repo.delete_obrigacao(obrigacao_id)

    def _calcular_prioridade(
        self,
        data_vencimento: Optional[date]
    ) -> PrioridadeObrigacao:
        """
        Calcula prioridade baseada nos dias até o vencimento
        """
        if not data_vencimento:
            return PrioridadeObrigacao.NORMAL

        hoje = date.today()
        dias_ate_vencimento = (data_vencimento - hoje).days

        if dias_ate_vencimento < 0:
            return PrioridadeObrigacao.CRITICA
        if dias_ate_vencimento <= 3:
            return PrioridadeObrigacao.CRITICA
        if dias_ate_vencimento <= 7:
            return PrioridadeObrigacao.ALTA
        if dias_ate_vencimento <= 15:
            return PrioridadeObrigacao.NORMAL

        return PrioridadeObrigacao.BAIXA
