"""
Engine de Cálculos Fiscais (Paridade IRIS)
Implementa cálculos de Simples Nacional, Fator R e Alíquotas
"""

from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Tabelas do Simples Nacional (Anexos I a V) - LC 123/2006 atualizada
TABELA_SIMPLES = {
    "anexo_i": {  # Comércio
        "faixas": [
            {"limite": 180000, "aliquota": 4.0, "deducao": 0},
            {"limite": 360000, "aliquota": 7.3, "deducao": 5940},
            {"limite": 720000, "aliquota": 9.5, "deducao": 13860},
            {"limite": 1800000, "aliquota": 10.7, "deducao": 22500},
            {"limite": 3600000, "aliquota": 14.3, "deducao": 87300},
            {"limite": 4800000, "aliquota": 19.0, "deducao": 378000},
        ]
    },
    "anexo_ii": {  # Indústria
        "faixas": [
            {"limite": 180000, "aliquota": 4.5, "deducao": 0},
            {"limite": 360000, "aliquota": 7.8, "deducao": 5940},
            {"limite": 720000, "aliquota": 10.0, "deducao": 13860},
            {"limite": 1800000, "aliquota": 11.2, "deducao": 22500},
            {"limite": 3600000, "aliquota": 14.7, "deducao": 85500},
            {"limite": 4800000, "aliquota": 30.0, "deducao": 720000},
        ]
    },
    "anexo_iii": {  # Serviços (Fator R >= 28%)
        "faixas": [
            {"limite": 180000, "aliquota": 6.0, "deducao": 0},
            {"limite": 360000, "aliquota": 11.2, "deducao": 9360},
            {"limite": 720000, "aliquota": 13.5, "deducao": 17640},
            {"limite": 1800000, "aliquota": 16.0, "deducao": 35640},
            {"limite": 3600000, "aliquota": 21.0, "deducao": 125640},
            {"limite": 4800000, "aliquota": 33.0, "deducao": 648000},
        ]
    },
    "anexo_iv": {  # Serviços (específicos)
        "faixas": [
            {"limite": 180000, "aliquota": 4.5, "deducao": 0},
            {"limite": 360000, "aliquota": 9.0, "deducao": 8100},
            {"limite": 720000, "aliquota": 10.2, "deducao": 12420},
            {"limite": 1800000, "aliquota": 14.0, "deducao": 39780},
            {"limite": 3600000, "aliquota": 22.0, "deducao": 183780},
            {"limite": 4800000, "aliquota": 33.0, "deducao": 828000},
        ]
    },
    "anexo_v": {  # Serviços (Fator R < 28%)
        "faixas": [
            {"limite": 180000, "aliquota": 15.5, "deducao": 0},
            {"limite": 360000, "aliquota": 18.0, "deducao": 4500},
            {"limite": 720000, "aliquota": 19.5, "deducao": 9900},
            {"limite": 1800000, "aliquota": 20.5, "deducao": 17100},
            {"limite": 3600000, "aliquota": 23.0, "deducao": 62100},
            {"limite": 4800000, "aliquota": 30.5, "deducao": 540000},
        ]
    }
}

# Limite de sublimite estadual
SUBLIMITE_ESTADUAL = 3600000
LIMITE_SIMPLES = 4800000


class FiscalEngine:
    """
    Engine para cálculos fiscais do Simples Nacional
    Implementa as regras da LC 123/2006
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calcular_simples_nacional(
        self,
        receita_bruta_12m: float,
        receita_mensal: float,
        anexo: str = "anexo_iii",
        fator_r: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula o valor do DAS (Simples Nacional)
        
        Args:
            receita_bruta_12m: Receita Bruta Acumulada dos últimos 12 meses
            receita_mensal: Receita bruta do mês corrente
            anexo: Anexo do Simples (anexo_i a anexo_v)
            fator_r: Fator R calculado (se aplicável)
            
        Returns:
            Dict com alíquota efetiva, valor DAS e detalhes
        """
        self.logger.info(
            f"Calculando Simples Nacional: RBT12={receita_bruta_12m}, "
            f"Receita={receita_mensal}, Anexo={anexo}"
        )
        
        # Validar se está no limite do Simples
        if receita_bruta_12m > LIMITE_SIMPLES:
            return {
                "status": "EXCEDIDO",
                "mensagem": f"Receita excede o limite do Simples Nacional (R$ {LIMITE_SIMPLES:,.2f})",
                "aliquota_efetiva": 0,
                "valor_das": 0
            }
        
        # Determinar anexo baseado no Fator R (se serviços)
        if fator_r is not None and anexo in ["anexo_iii", "anexo_v"]:
            if fator_r >= 0.28:
                anexo = "anexo_iii"  # Mais benéfico
            else:
                anexo = "anexo_v"  # Menos benéfico
        
        # Buscar tabela do anexo
        tabela = TABELA_SIMPLES.get(anexo)
        if not tabela:
            raise ValueError(f"Anexo inválido: {anexo}")
        
        # Encontrar faixa
        faixa_encontrada = None
        for faixa in tabela["faixas"]:
            if receita_bruta_12m <= faixa["limite"]:
                faixa_encontrada = faixa
                break
        
        if not faixa_encontrada:
            faixa_encontrada = tabela["faixas"][-1]  # Última faixa
        
        # Calcular alíquota efetiva
        # Fórmula: [(RBT12 × Aliq) - PD] / RBT12
        aliquota_nominal = Decimal(str(faixa_encontrada["aliquota"])) / 100
        parcela_deduzir = Decimal(str(faixa_encontrada["deducao"]))
        rbt12 = Decimal(str(receita_bruta_12m))
        
        if rbt12 > 0:
            aliquota_efetiva = ((rbt12 * aliquota_nominal) - parcela_deduzir) / rbt12
        else:
            aliquota_efetiva = Decimal(0)
        
        # Garantir alíquota mínima
        aliquota_efetiva = max(aliquota_efetiva, Decimal("0.04"))
        
        # Calcular valor do DAS
        receita_decimal = Decimal(str(receita_mensal))
        valor_das = (receita_decimal * aliquota_efetiva).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        # Verificar sublimite estadual
        excede_sublimite = receita_bruta_12m > SUBLIMITE_ESTADUAL
        
        resultado = {
            "status": "SUCESSO",
            "anexo": anexo,
            "faixa": {
                "limite": faixa_encontrada["limite"],
                "aliquota_nominal": float(aliquota_nominal * 100),
                "parcela_deduzir": float(parcela_deduzir)
            },
            "receita_bruta_12m": receita_bruta_12m,
            "receita_mensal": receita_mensal,
            "aliquota_efetiva": float(aliquota_efetiva * 100),
            "valor_das": float(valor_das),
            "excede_sublimite_estadual": excede_sublimite,
            "fator_r": fator_r,
            "calculado_em": datetime.utcnow().isoformat()
        }
        
        self.logger.info(
            f"Cálculo concluído: Alíq. Efetiva={resultado['aliquota_efetiva']:.2f}%, "
            f"DAS=R$ {resultado['valor_das']:,.2f}"
        )
        
        return resultado
    
    def calcular_fator_r(
        self,
        folha_salarios_12m: float,
        receita_bruta_12m: float
    ) -> Dict[str, Any]:
        """
        Calcula o Fator R (relação Folha/Receita)
        
        Args:
            folha_salarios_12m: Folha de salários dos últimos 12 meses
            receita_bruta_12m: Receita Bruta dos últimos 12 meses
            
        Returns:
            Dict com fator R e enquadramento
        """
        self.logger.info(
            f"Calculando Fator R: Folha={folha_salarios_12m}, RBT12={receita_bruta_12m}"
        )
        
        if receita_bruta_12m <= 0:
            return {
                "status": "ERRO",
                "mensagem": "Receita Bruta deve ser maior que zero",
                "fator_r": 0
            }
        
        folha = Decimal(str(folha_salarios_12m))
        receita = Decimal(str(receita_bruta_12m))
        
        fator_r = (folha / receita).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        fator_r_percentual = float(fator_r * 100)
        
        # Determinar enquadramento
        if fator_r >= Decimal("0.28"):
            enquadramento = "ANEXO_III"
            descricao = "Fator R >= 28%: Enquadramento no Anexo III (alíquotas reduzidas)"
        else:
            enquadramento = "ANEXO_V"
            descricao = "Fator R < 28%: Enquadramento no Anexo V (alíquotas majoradas)"
        
        resultado = {
            "status": "SUCESSO",
            "folha_salarios_12m": folha_salarios_12m,
            "receita_bruta_12m": receita_bruta_12m,
            "fator_r": float(fator_r),
            "fator_r_percentual": fator_r_percentual,
            "enquadramento": enquadramento,
            "descricao": descricao,
            "beneficia_anexo_iii": fator_r >= Decimal("0.28"),
            "calculado_em": datetime.utcnow().isoformat()
        }
        
        self.logger.info(
            f"Fator R calculado: {fator_r_percentual:.2f}% - {enquadramento}"
        )
        
        return resultado
    
    def simular_economia_fator_r(
        self,
        receita_bruta_12m: float,
        receita_mensal: float,
        folha_atual_12m: float
    ) -> Dict[str, Any]:
        """
        Simula a economia potencial ao atingir Fator R >= 28%
        
        Returns:
            Dict com comparativo de cenários
        """
        # Calcular com anexo V (Fator R atual < 28%)
        calculo_anexo_v = self.calcular_simples_nacional(
            receita_bruta_12m, receita_mensal, "anexo_v"
        )
        
        # Calcular com anexo III (Fator R >= 28%)
        calculo_anexo_iii = self.calcular_simples_nacional(
            receita_bruta_12m, receita_mensal, "anexo_iii"
        )
        
        # Calcular Fator R atual
        fator_r_atual = self.calcular_fator_r(folha_atual_12m, receita_bruta_12m)
        
        # Calcular folha necessária para 28%
        folha_necessaria = receita_bruta_12m * 0.28
        aumento_folha = max(0, folha_necessaria - folha_atual_12m)
        
        # Economia mensal e anual
        economia_mensal = calculo_anexo_v["valor_das"] - calculo_anexo_iii["valor_das"]
        economia_anual = economia_mensal * 12
        
        return {
            "status": "SUCESSO",
            "cenario_atual": {
                "fator_r": fator_r_atual["fator_r_percentual"],
                "anexo": "V" if fator_r_atual["fator_r"] < 0.28 else "III",
                "das_mensal": calculo_anexo_v["valor_das"] if fator_r_atual["fator_r"] < 0.28 else calculo_anexo_iii["valor_das"],
                "folha_12m": folha_atual_12m
            },
            "cenario_otimizado": {
                "fator_r_minimo": 28.0,
                "anexo": "III",
                "das_mensal": calculo_anexo_iii["valor_das"],
                "folha_necessaria_12m": folha_necessaria,
                "aumento_folha_necessario": aumento_folha
            },
            "economia_potencial": {
                "mensal": economia_mensal,
                "anual": economia_anual
            },
            "recomendacao": "Aumentar folha de salários" if aumento_folha > 0 else "Já enquadrado no Anexo III"
        }
