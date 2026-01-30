"""
Serviço de Inteligência Fiscal com motor de regras
"""

import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class MotorRegras:
    """Motor de regras para identificação de riscos fiscais"""
    
    def __init__(self):
        self.regras = self._carregar_regras()
        self.riscos_identificados = []
    
    def _carregar_regras(self) -> Dict:
        """Carrega regras tributárias"""
        return {
            'FATURAMENTO_ZERO': {
                'descricao': 'Empresa com faturamento zero',
                'severidade': 'MEDIA',
                'condicao': lambda dados: dados.get('receita_bruta', 0) == 0,
                'acao': 'REVISAR_ENQUADRAMENTO'
            },
            'FATURAMENTO_ACIMA_LIMITE': {
                'descricao': 'Faturamento acima do limite de Simples Nacional',
                'severidade': 'CRITICA',
                'condicao': lambda dados: dados.get('receita_bruta', 0) > Decimal('4800000'),
                'acao': 'RECLASSIFICAR_REGIME'
            },
            'DEFIS_ATRASADO': {
                'descricao': 'DEFIS em atraso',
                'severidade': 'CRITICA',
                'condicao': lambda dados: dados.get('defis_atrasado', False),
                'acao': 'EMITIR_ALERTA'
            },
            'CERTIDAO_VENCIDA': {
                'descricao': 'Certidão vencida',
                'severidade': 'CRITICA',
                'condicao': lambda dados: dados.get('certidao_vencida', False),
                'acao': 'RENOVAR_CERTIDAO'
            },
            'FATOR_R_BAIXO': {
                'descricao': 'Fator R muito baixo (possível fraude)',
                'severidade': 'ALTA',
                'condicao': lambda dados: dados.get('fator_r', 1) < Decimal('0.28'),
                'acao': 'REVISAR_FOLHA_PAGAMENTO'
            },
            'DIVERGENCIA_FISCAL': {
                'descricao': 'Divergência entre XML e SPED',
                'severidade': 'ALTA',
                'condicao': lambda dados: dados.get('taxa_conformidade', 100) < 95,
                'acao': 'REVISAR_REGISTROS'
            }
        }
    
    def analisar_empresa(self, dados_empresa: Dict) -> Dict:
        """Analisa empresa e identifica riscos"""
        try:
            logger.info(f"Analisando empresa {dados_empresa.get('cnpj')}")
            
            self.riscos_identificados = []
            
            # Aplicar cada regra
            for nome_regra, regra in self.regras.items():
                try:
                    if regra['condicao'](dados_empresa):
                        self.riscos_identificados.append({
                            'regra': nome_regra,
                            'descricao': regra['descricao'],
                            'severidade': regra['severidade'],
                            'acao_recomendada': regra['acao'],
                            'data_identificacao': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Erro ao aplicar regra {nome_regra}: {str(e)}")
                    continue
            
            # Calcular score de risco
            score_risco = self._calcular_score_risco()
            
            resultado = {
                'cnpj': dados_empresa.get('cnpj'),
                'total_riscos': len(self.riscos_identificados),
                'riscos': self.riscos_identificados,
                'score_risco': score_risco,
                'nivel_risco': self._classificar_nivel_risco(score_risco),
                'data_analise': datetime.now().isoformat()
            }
            
            logger.info(f"Análise concluída: {len(self.riscos_identificados)} riscos identificados")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao analisar empresa: {str(e)}")
            return {}
    
    def _calcular_score_risco(self) -> float:
        """Calcula score de risco baseado nos riscos identificados"""
        try:
            score = 0
            pesos = {
                'CRITICA': 10,
                'ALTA': 5,
                'MEDIA': 2,
                'BAIXA': 1
            }
            
            for risco in self.riscos_identificados:
                severidade = risco.get('severidade', 'BAIXA')
                score += pesos.get(severidade, 0)
            
            # Normalizar para 0-100
            score_normalizado = min(100, (score / len(self.regras)) * 100) if self.regras else 0
            
            return round(score_normalizado, 2)
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de risco: {str(e)}")
            return 0.0
    
    def _classificar_nivel_risco(self, score: float) -> str:
        """Classifica nível de risco baseado no score"""
        if score >= 80:
            return 'CRITICO'
        elif score >= 60:
            return 'ALTO'
        elif score >= 40:
            return 'MEDIO'
        else:
            return 'BAIXO'


class MapaFiscal:
    """Mapa fiscal por CNAE com obrigações e regimes"""
    
    def __init__(self):
        self.mapa_cnae = self._carregar_mapa_cnae()
    
    def _carregar_mapa_cnae(self) -> Dict:
        """Carrega mapa fiscal por CNAE"""
        return {
            '4711301': {
                'descricao': 'Comércio varejista de mercadorias em geral',
                'regimes_permitidos': ['SIMPLES_NACIONAL', 'LUCRO_PRESUMIDO', 'LUCRO_REAL'],
                'regime_recomendado': 'SIMPLES_NACIONAL',
                'obrigacoes': ['EMITIR_NF', 'MANTER_SPED', 'PAGAR_ICMS'],
                'impostos_principais': ['ICMS', 'PIS', 'COFINS'],
                'aliquota_simples': '4.00',
                'limite_receita': '4800000'
            },
            '6201501': {
                'descricao': 'Consultoria em gestão empresarial',
                'regimes_permitidos': ['SIMPLES_NACIONAL', 'LUCRO_PRESUMIDO', 'LUCRO_REAL'],
                'regime_recomendado': 'SIMPLES_NACIONAL',
                'obrigacoes': ['EMITIR_RPS', 'MANTER_SPED', 'PAGAR_ISS'],
                'impostos_principais': ['ISS', 'PIS', 'COFINS'],
                'aliquota_simples': '6.00',
                'limite_receita': '4800000'
            }
        }
    
    def obter_mapa_cnae(self, cnae: str) -> Optional[Dict]:
        """Obtém mapa fiscal para um CNAE específico"""
        try:
            return self.mapa_cnae.get(cnae)
        except Exception as e:
            logger.error(f"Erro ao obter mapa CNAE: {str(e)}")
            return None
    
    def recomendar_regime(self, cnae: str, receita_anual: float) -> Dict:
        """Recomenda regime fiscal baseado em CNAE e receita"""
        try:
            mapa = self.obter_mapa_cnae(cnae)
            
            if not mapa:
                return {'erro': 'CNAE não encontrado'}
            
            regime_recomendado = mapa['regime_recomendado']
            
            # Validar limite de receita
            if receita_anual > float(mapa.get('limite_receita', '4800000')):
                regime_recomendado = 'LUCRO_PRESUMIDO'
            
            resultado = {
                'cnae': cnae,
                'descricao_cnae': mapa['descricao'],
                'regime_recomendado': regime_recomendado,
                'regimes_permitidos': mapa['regimes_permitidos'],
                'obrigacoes': mapa['obrigacoes'],
                'impostos_principais': mapa['impostos_principais'],
                'data_recomendacao': datetime.now().isoformat()
            }
            
            logger.info(f"Regime recomendado: {regime_recomendado}")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao recomendar regime: {str(e)}")
            return {}


class SugestoesRegularizacao:
    """Gerador de sugestões de regularização fiscal"""
    
    def __init__(self):
        self.sugestoes = []
    
    def gerar_sugestoes(self, dados_empresa: Dict, riscos: List[Dict]) -> Dict:
        """Gera sugestões de regularização baseado em riscos"""
        try:
            logger.info(f"Gerando sugestões para empresa {dados_empresa.get('cnpj')}")
            
            self.sugestoes = []
            
            # Analisar cada risco
            for risco in riscos:
                sugestao = self._gerar_sugestao_para_risco(risco, dados_empresa)
                if sugestao:
                    self.sugestoes.append(sugestao)
            
            # Ordenar por prioridade
            self.sugestoes.sort(key=lambda x: x['prioridade'], reverse=True)
            
            resultado = {
                'cnpj': dados_empresa.get('cnpj'),
                'total_sugestoes': len(self.sugestoes),
                'sugestoes': self.sugestoes,
                'data_geracao': datetime.now().isoformat()
            }
            
            logger.info(f"{len(self.sugestoes)} sugestão(ões) gerada(s)")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao gerar sugestões: {str(e)}")
            return {}
    
    def _gerar_sugestao_para_risco(self, risco: Dict, dados_empresa: Dict) -> Optional[Dict]:
        """Gera sugestão para um risco específico"""
        try:
            tipo_risco = risco.get('regra')
            
            if tipo_risco == 'FATURAMENTO_ACIMA_LIMITE':
                return {
                    'tipo': 'RECLASSIFICACAO_REGIME',
                    'titulo': 'Reclassificar para Lucro Presumido',
                    'descricao': 'Empresa ultrapassou limite de Simples Nacional',
                    'acao_recomendada': 'Solicitar desenquadramento e reclassificação',
                    'prazo': '30 dias',
                    'prioridade': 10,
                    'impacto': 'Evitar multa de 75% do imposto devido'
                }
            
            elif tipo_risco == 'DEFIS_ATRASADO':
                return {
                    'tipo': 'REGULARIZAR_DEFIS',
                    'titulo': 'Regularizar DEFIS em atraso',
                    'descricao': 'DEFIS não foi entregue no prazo',
                    'acao_recomendada': 'Acessar e-CAC e entregar DEFIS com multa',
                    'prazo': 'Imediato',
                    'prioridade': 10,
                    'impacto': 'Multa de 5% ao mês de atraso'
                }
            
            elif tipo_risco == 'CERTIDAO_VENCIDA':
                return {
                    'tipo': 'RENOVAR_CERTIDAO',
                    'titulo': 'Renovar certidão vencida',
                    'descricao': 'Certidão de regularidade fiscal vencida',
                    'acao_recomendada': 'Acessar e-CAC e renovar certidão',
                    'prazo': '7 dias',
                    'prioridade': 9,
                    'impacto': 'Impossibilidade de participar de licitações'
                }
            
            elif tipo_risco == 'FATOR_R_BAIXO':
                return {
                    'tipo': 'REVISAR_FOLHA_PAGAMENTO',
                    'titulo': 'Revisar folha de pagamento',
                    'descricao': 'Fator R muito baixo pode indicar fraude',
                    'acao_recomendada': 'Revisar registros de folha de pagamento',
                    'prazo': '15 dias',
                    'prioridade': 8,
                    'impacto': 'Risco de auditoria fiscal'
                }
            
            elif tipo_risco == 'DIVERGENCIA_FISCAL':
                return {
                    'tipo': 'REVISAR_REGISTROS',
                    'titulo': 'Revisar divergências fiscais',
                    'descricao': 'Divergência entre XML e SPED',
                    'acao_recomendada': 'Revisar registros e corrigir SPED',
                    'prazo': '30 dias',
                    'prioridade': 7,
                    'impacto': 'Risco de multa por inconsistência'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao gerar sugestão: {str(e)}")
            return None
