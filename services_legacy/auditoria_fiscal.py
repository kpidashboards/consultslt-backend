"""
Serviço de Auditoria Fiscal com SPED e cruzamentos XML
"""

import logging
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class SPEDParser:
    """Parser de arquivos SPED com validações completas"""
    
    def __init__(self):
        self.registros = []
        self.erros = []
        self.avisos = []
        self.estatisticas = {
            'total_registros': 0,
            'registros_validos': 0,
            'registros_invalidos': 0,
            'blocos': {}
        }
    
    def parsear_arquivo(self, caminho_arquivo: str) -> Dict:
        """Parseia arquivo SPED completo"""
        try:
            logger.info(f"🔍 Iniciando parse do arquivo SPED: {caminho_arquivo}")
            
            with open(caminho_arquivo, 'r', encoding='latin-1') as f:
                linhas = f.readlines()
            
            bloco_atual = None
            
            for num_linha, linha in enumerate(linhas, 1):
                try:
                    linha = linha.rstrip('\n\r')
                    
                    if not linha or linha.startswith('|'):
                        continue
                    
                    # Identificar tipo de registro
                    tipo_registro = self._identificar_tipo_registro(linha)
                    
                    # Parsear registro
                    registro = self._parsear_registro(linha, tipo_registro, num_linha)
                    
                    if registro:
                        self.registros.append(registro)
                        self.estatisticas['registros_validos'] += 1
                        
                        # Atualizar bloco atual
                        if 'bloco' in registro:
                            bloco_atual = registro['bloco']
                            if bloco_atual not in self.estatisticas['blocos']:
                                self.estatisticas['blocos'][bloco_atual] = 0
                            self.estatisticas['blocos'][bloco_atual] += 1
                    else:
                        self.estatisticas['registros_invalidos'] += 1
                    
                    self.estatisticas['total_registros'] += 1
                    
                except Exception as e:
                    logger.warning(f"Erro ao parsear linha {num_linha}: {str(e)}")
                    self.erros.append({
                        'linha': num_linha,
                        'erro': str(e)
                    })
                    continue
            
            logger.info(f"✅ Parse concluído: {self.estatisticas['registros_validos']} registros válidos")
            
            return {
                'sucesso': True,
                'registros': self.registros,
                'estatisticas': self.estatisticas,
                'erros': self.erros,
                'avisos': self.avisos
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao parsear arquivo SPED: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def _identificar_tipo_registro(self, linha: str) -> str:
        """Identifica tipo de registro baseado no conteúdo"""
        partes = linha.split('|')
        
        if len(partes) < 2:
            return 'DESCONHECIDO'
        
        return partes[1]
    
    def _parsear_registro(self, linha: str, tipo_registro: str, num_linha: int) -> Optional[Dict]:
        """Parseia um registro específico"""
        try:
            partes = linha.split('|')
            
            if tipo_registro == '0000':
                return self._parsear_0000(partes, num_linha)
            elif tipo_registro == 'C100':
                return self._parsear_c100(partes, num_linha)
            elif tipo_registro == 'D100':
                return self._parsear_d100(partes, num_linha)
            elif tipo_registro == '9999':
                return self._parsear_9999(partes, num_linha)
            else:
                return None
            
        except Exception as e:
            logger.warning(f"Erro ao parsear registro {tipo_registro}: {str(e)}")
            return None
    
    def _parsear_0000(self, partes: List[str], num_linha: int) -> Dict:
        """Parseia registro 0000 (Abertura do arquivo)"""
        try:
            return {
                'tipo': '0000',
                'bloco': 'BLOCO_0',
                'tipo_arquivo': partes[2] if len(partes) > 2 else None,
                'mes_ano': partes[3] if len(partes) > 3 else None,
                'data_inicio': partes[4] if len(partes) > 4 else None,
                'data_fim': partes[5] if len(partes) > 5 else None,
                'num_linha': num_linha
            }
        except Exception as e:
            logger.warning(f"Erro ao parsear 0000: {str(e)}")
            return None
    
    def _parsear_c100(self, partes: List[str], num_linha: int) -> Dict:
        """Parseia registro C100 (Nota Fiscal de Saída)"""
        try:
            return {
                'tipo': 'C100',
                'bloco': 'BLOCO_C',
                'tipo_documento': partes[2] if len(partes) > 2 else None,
                'serie': partes[3] if len(partes) > 3 else None,
                'numero_nf': partes[4] if len(partes) > 4 else None,
                'data_emissao': partes[5] if len(partes) > 5 else None,
                'valor_total': Decimal(partes[8]) if len(partes) > 8 else Decimal('0'),
                'valor_icms': Decimal(partes[9]) if len(partes) > 9 else Decimal('0'),
                'num_linha': num_linha
            }
        except Exception as e:
            logger.warning(f"Erro ao parsear C100: {str(e)}")
            return None
    
    def _parsear_d100(self, partes: List[str], num_linha: int) -> Dict:
        """Parseia registro D100 (Nota Fiscal de Entrada)"""
        try:
            return {
                'tipo': 'D100',
                'bloco': 'BLOCO_D',
                'tipo_documento': partes[2] if len(partes) > 2 else None,
                'serie': partes[3] if len(partes) > 3 else None,
                'numero_nf': partes[4] if len(partes) > 4 else None,
                'data_emissao': partes[5] if len(partes) > 5 else None,
                'valor_total': Decimal(partes[8]) if len(partes) > 8 else Decimal('0'),
                'valor_icms': Decimal(partes[9]) if len(partes) > 9 else Decimal('0'),
                'num_linha': num_linha
            }
        except Exception as e:
            logger.warning(f"Erro ao parsear D100: {str(e)}")
            return None
    
    def _parsear_9999(self, partes: List[str], num_linha: int) -> Dict:
        """Parseia registro 9999 (Fechamento do arquivo)"""
        try:
            return {
                'tipo': '9999',
                'bloco': 'BLOCO_9',
                'quantidade_blocos': partes[2] if len(partes) > 2 else None,
                'quantidade_registros': partes[3] if len(partes) > 3 else None,
                'num_linha': num_linha
            }
        except Exception as e:
            logger.warning(f"Erro ao parsear 9999: {str(e)}")
            return None


class ValidadorSPED:
    """Validador de registros SPED com regras fiscais"""
    
    def __init__(self):
        self.erros_validacao = []
        self.avisos_validacao = []
    
    def validar_arquivo_sped(self, registros: List[Dict]) -> Dict:
        """Valida arquivo SPED completo"""
        try:
            logger.info("🔍 Iniciando validação de arquivo SPED")
            
            # Validar estrutura
            self._validar_estrutura(registros)
            
            # Validar registros
            for registro in registros:
                self._validar_registro(registro)
            
            resultado = {
                'sucesso': len(self.erros_validacao) == 0,
                'total_erros': len(self.erros_validacao),
                'total_avisos': len(self.avisos_validacao),
                'erros': self.erros_validacao,
                'avisos': self.avisos_validacao
            }
            
            logger.info(f"✅ Validação concluída: {len(self.erros_validacao)} erros, {len(self.avisos_validacao)} avisos")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao validar arquivo SPED: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
    
    def _validar_estrutura(self, registros: List[Dict]):
        """Valida estrutura básica do arquivo"""
        try:
            # Deve começar com 0000
            if not registros or registros[0]['tipo'] != '0000':
                self.erros_validacao.append({
                    'tipo': 'ERRO_ESTRUTURA',
                    'mensagem': 'Arquivo deve começar com registro 0000'
                })
            
            # Deve terminar com 9999
            if not registros or registros[-1]['tipo'] != '9999':
                self.erros_validacao.append({
                    'tipo': 'ERRO_ESTRUTURA',
                    'mensagem': 'Arquivo deve terminar com registro 9999'
                })
            
        except Exception as e:
            logger.error(f"Erro ao validar estrutura: {str(e)}")
    
    def _validar_registro(self, registro: Dict):
        """Valida um registro específico"""
        try:
            tipo = registro.get('tipo')
            
            if tipo in ['C100', 'D100']:
                if not registro.get('numero_nf'):
                    self.erros_validacao.append({
                        'tipo': 'ERRO_REGISTRO',
                        'registro': tipo,
                        'mensagem': 'Número da NF não informado',
                        'linha': registro.get('num_linha')
                    })
            
        except Exception as e:
            logger.error(f"Erro ao validar registro: {str(e)}")


class CruzamentoXmlSped:
    """Cruzamento de dados entre XML e SPED"""
    
    def __init__(self):
        self.divergencias = []
        self.conformidades = []
    
    def cruzar_dados(self, xmls: List[Dict], registros_sped: List[Dict]) -> Dict:
        """Cruza dados de XML com SPED"""
        try:
            logger.info("🔄 Iniciando cruzamento XML × SPED")
            
            # Extrair NFs do XML
            nfs_xml = self._extrair_nfs_xml(xmls)
            
            # Extrair NFs do SPED
            nfs_sped = self._extrair_nfs_sped(registros_sped)
            
            # Comparar
            self._comparar_nfs(nfs_xml, nfs_sped)
            
            resultado = {
                'total_nfs_xml': len(nfs_xml),
                'total_nfs_sped': len(nfs_sped),
                'divergencias': self.divergencias,
                'conformidades': len(self.conformidades),
                'taxa_conformidade': self._calcular_taxa_conformidade()
            }
            
            logger.info(f"✅ Cruzamento concluído: {len(self.divergencias)} divergências encontradas")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao cruzar dados: {str(e)}")
            return {}
    
    def _extrair_nfs_xml(self, xmls: List[Dict]) -> Dict:
        """Extrai NFs do XML"""
        try:
            nfs = {}
            
            for xml in xmls:
                try:
                    numero_nf = xml.get('numero')
                    serie = xml.get('serie')
                    chave = f"{numero_nf}_{serie}"
                    
                    nfs[chave] = {
                        'numero': numero_nf,
                        'serie': serie,
                        'valor_total': Decimal(str(xml.get('valor_total', 0))),
                        'fonte': 'XML'
                    }
                except Exception as e:
                    logger.warning(f"Erro ao extrair NF do XML: {str(e)}")
                    continue
            
            return nfs
            
        except Exception as e:
            logger.error(f"Erro ao extrair NFs do XML: {str(e)}")
            return {}
    
    def _extrair_nfs_sped(self, registros_sped: List[Dict]) -> Dict:
        """Extrai NFs do SPED"""
        try:
            nfs = {}
            
            for registro in registros_sped:
                try:
                    if registro.get('tipo') in ['C100', 'D100']:
                        numero_nf = registro.get('numero_nf')
                        serie = registro.get('serie')
                        chave = f"{numero_nf}_{serie}"
                        
                        nfs[chave] = {
                            'numero': numero_nf,
                            'serie': serie,
                            'valor_total': registro.get('valor_total', Decimal('0')),
                            'fonte': 'SPED'
                        }
                except Exception as e:
                    logger.warning(f"Erro ao extrair NF do SPED: {str(e)}")
                    continue
            
            return nfs
            
        except Exception as e:
            logger.error(f"Erro ao extrair NFs do SPED: {str(e)}")
            return {}
    
    def _comparar_nfs(self, nfs_xml: Dict, nfs_sped: Dict):
        """Compara NFs entre XML e SPED"""
        try:
            # NFs no XML mas não no SPED
            for chave, nf_xml in nfs_xml.items():
                if chave not in nfs_sped:
                    self.divergencias.append({
                        'tipo': 'NF_NAO_ENCONTRADA_SPED',
                        'numero_nf': nf_xml['numero'],
                        'valor': float(nf_xml['valor_total'])
                    })
                else:
                    # Comparar valores
                    nf_sped = nfs_sped[chave]
                    
                    if nf_xml['valor_total'] != nf_sped['valor_total']:
                        self.divergencias.append({
                            'tipo': 'DIVERGENCIA_VALOR',
                            'numero_nf': nf_xml['numero'],
                            'valor_xml': float(nf_xml['valor_total']),
                            'valor_sped': float(nf_sped['valor_total'])
                        })
                    else:
                        self.conformidades.append(chave)
            
            # NFs no SPED mas não no XML
            for chave, nf_sped in nfs_sped.items():
                if chave not in nfs_xml:
                    self.divergencias.append({
                        'tipo': 'NF_NAO_ENCONTRADA_XML',
                        'numero_nf': nf_sped['numero'],
                        'valor': float(nf_sped['valor_total'])
                    })
            
        except Exception as e:
            logger.error(f"Erro ao comparar NFs: {str(e)}")
    
    def _calcular_taxa_conformidade(self) -> float:
        """Calcula taxa de conformidade"""
        try:
            total = len(self.conformidades) + len(self.divergencias)
            
            if total == 0:
                return 100.0
            
            taxa = (len(self.conformidades) / total) * 100
            return round(taxa, 2)
            
        except Exception as e:
            logger.error(f"Erro ao calcular taxa de conformidade: {str(e)}")
            return 0.0
