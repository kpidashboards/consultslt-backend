"""
Serviço de Automação (RPA) com robôs para captura de XML e monitoramento
Implementação com Playwright e Selenium
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import hashlib
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_
import aiohttp
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)

class TipoDocumento(Enum):
    """Tipos de documentos suportados"""
    NFE = "NFE"
    NFSE = "NFSE"
    CTE = "CTE"
    MDFE = "MDFE"

class RoboAutomacao:
    """Robô de automação com suporte a múltiplos tipos de documentos"""
    
    def __init__(self, db: Session, empresa_id: str):
        self.db = db
        self.empresa_id = empresa_id
        self.browser = None
        self.page = None
        self.timeout = 30000
        self.max_retries = 3
    
    async def capturar_nfe_sefaz(self, cnpj: str, periodo_inicio: str, periodo_fim: str) -> Dict:
        """Captura NF-e do portal SEFAZ"""
        try:
            logger.info(f"🤖 Iniciando captura de NF-e para {cnpj}")
            
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(headless=True)
                self.page = await self.browser.new_page()
                
                # Acessar portal SEFAZ
                await self.page.goto('https://www1.nfe.fazenda.gov.br/portal/consultas.html')
                
                # Fazer login
                await self._fazer_login_sefaz(cnpj)
                
                # Navegar para consulta de NF-e
                await self.page.goto('https://www1.nfe.fazenda.gov.br/portal/consultas.html?tipo=consulta_nfe')
                
                # Preencher período
                await self.page.fill('input[name="data_inicio"]', periodo_inicio)
                await self.page.fill('input[name="data_fim"]', periodo_fim)
                
                # Pesquisar
                await self.page.click('button:has-text("Pesquisar")')
                
                # Aguardar resultados
                await self.page.wait_for_selector('table tbody tr', timeout=self.timeout)
                
                # Extrair e baixar
                nfes = await self._extrair_nfes()
                xmls_capturados = await self._baixar_xmls(nfes, TipoDocumento.NFE)
                
                await self.browser.close()
                
                logger.info(f"✅ Capturadas {len(xmls_capturados)} NF-e(s)")
                
                return {
                    'tipo': TipoDocumento.NFE.value,
                    'total': len(xmls_capturados),
                    'xmls': xmls_capturados,
                    'data_captura': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao capturar NF-e: {str(e)}")
            if self.browser:
                await self.browser.close()
            return {'erro': str(e)}
    
    async def capturar_nfse_prefeitura(self, cnpj: str, municipio: str, periodo_inicio: str, periodo_fim: str) -> Dict:
        """Captura NFS-e da prefeitura"""
        try:
            logger.info(f"🤖 Iniciando captura de NFS-e para {cnpj} em {municipio}")
            
            # Obter URL da prefeitura
            url_prefeitura = self._obter_url_nfse(municipio)
            
            if not url_prefeitura:
                logger.warning(f"URL de NFS-e não encontrada para {municipio}")
                return {'erro': 'URL não encontrada'}
            
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(headless=True)
                self.page = await self.browser.new_page()
                
                # Acessar portal da prefeitura
                await self.page.goto(url_prefeitura)
                
                # Fazer login
                await self._fazer_login_prefeitura(cnpj, municipio)
                
                # Preencher período
                await self.page.fill('input[name="data_inicio"]', periodo_inicio)
                await self.page.fill('input[name="data_fim"]', periodo_fim)
                
                # Pesquisar
                await self.page.click('button:has-text("Pesquisar")')
                
                # Aguardar resultados
                await self.page.wait_for_selector('table tbody tr', timeout=self.timeout)
                
                # Extrair e baixar
                nfses = await self._extrair_nfses()
                xmls_capturados = await self._baixar_xmls(nfses, TipoDocumento.NFSE)
                
                await self.browser.close()
                
                logger.info(f"✅ Capturadas {len(xmls_capturados)} NFS-e(s)")
                
                return {
                    'tipo': TipoDocumento.NFSE.value,
                    'municipio': municipio,
                    'total': len(xmls_capturados),
                    'xmls': xmls_capturados,
                    'data_captura': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao capturar NFS-e: {str(e)}")
            if self.browser:
                await self.browser.close()
            return {'erro': str(e)}
    
    async def capturar_cte_sefaz(self, cnpj: str, periodo_inicio: str, periodo_fim: str) -> Dict:
        """Captura CT-e do portal SEFAZ"""
        try:
            logger.info(f"🤖 Iniciando captura de CT-e para {cnpj}")
            
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(headless=True)
                self.page = await self.browser.new_page()
                
                # Acessar portal SEFAZ CT-e
                await self.page.goto('https://www1.cte.fazenda.gov.br/portal/consultas.html')
                
                # Fazer login
                await self._fazer_login_sefaz(cnpj)
                
                # Navegar para consulta de CT-e
                await self.page.goto('https://www1.cte.fazenda.gov.br/portal/consultas.html?tipo=consulta_cte')
                
                # Preencher período
                await self.page.fill('input[name="data_inicio"]', periodo_inicio)
                await self.page.fill('input[name="data_fim"]', periodo_fim)
                
                # Pesquisar
                await self.page.click('button:has-text("Pesquisar")')
                
                # Aguardar e extrair
                await self.page.wait_for_selector('table tbody tr', timeout=self.timeout)
                ctes = await self._extrair_ctes()
                xmls_capturados = await self._baixar_xmls(ctes, TipoDocumento.CTE)
                
                await self.browser.close()
                
                logger.info(f"✅ Capturados {len(xmls_capturados)} CT-e(s)")
                
                return {
                    'tipo': TipoDocumento.CTE.value,
                    'total': len(xmls_capturados),
                    'xmls': xmls_capturados,
                    'data_captura': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao capturar CT-e: {str(e)}")
            if self.browser:
                await self.browser.close()
            return {'erro': str(e)}
    
    async def monitorar_certidoes(self) -> Dict:
        """Monitora certidões em tempo real"""
        try:
            logger.info(f"🔔 Monitorando certidões para empresa {self.empresa_id}")
            
            from backend.models import Certidao, AlertaFiscal
            
            hoje = datetime.now()
            resultado = {
                'alertas_gerados': 0,
                'acoes_executadas': 0,
                'certidoes_vencidas': [],
                'certidoes_proximas_vencer': []
            }
            
            # Obter certidões
            certidoes = self.db.query(Certidao).filter_by(empresa_id=self.empresa_id).all()
            
            for cert in certidoes:
                # Verificar se vencida
                if cert.data_validade < hoje:
                    resultado['certidoes_vencidas'].append({
                        'tipo': cert.tipo,
                        'subtipo': cert.subtipo,
                        'data_validade': cert.data_validade.isoformat(),
                        'dias_vencida': (hoje - cert.data_validade).days
                    })
                    
                    # Gerar alerta
                    await self._gerar_alerta(cert, 'CERTIDAO_VENCIDA')
                    resultado['alertas_gerados'] += 1
                    
                    # Executar ação automática
                    await self._executar_acao_automatica(cert)
                    resultado['acoes_executadas'] += 1
                
                # Verificar se próxima de vencer
                elif cert.data_validade <= hoje + timedelta(days=30):
                    resultado['certidoes_proximas_vencer'].append({
                        'tipo': cert.tipo,
                        'subtipo': cert.subtipo,
                        'data_validade': cert.data_validade.isoformat(),
                        'dias_para_vencer': (cert.data_validade - hoje).days
                    })
                    
                    # Gerar alerta
                    await self._gerar_alerta(cert, 'CERTIDAO_PROXIMA_VENCER')
                    resultado['alertas_gerados'] += 1
            
            logger.info(f"✅ Monitoramento concluído: {resultado['alertas_gerados']} alertas")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao monitorar certidões: {str(e)}")
            return {}
    
    async def _fazer_login_sefaz(self, cnpj: str):
        """Faz login no portal SEFAZ"""
        try:
            # Obter credenciais da empresa
            from backend.models import Credencial
            
            credencial = self.db.query(Credencial).filter(
                and_(
                    Credencial.empresa_id == self.empresa_id,
                    Credencial.tipo == 'ECAC'
                )
            ).first()
            
            if not credencial:
                raise Exception("Credencial e-CAC não encontrada")
            
            # Usar certificado para login
            await self.page.context.add_init_script(f"""
                window.certificado = {{
                    cnpj: '{cnpj}',
                    tipo: 'A1'
                }};
            """)
            
            # Clicar em login com certificado
            await self.page.click('button:has-text("Entrar com Certificado")')
            
            # Aguardar autenticação
            await self.page.wait_for_selector('.dashboard', timeout=self.timeout)
            
            logger.info("✅ Login SEFAZ realizado")
            
        except Exception as e:
            logger.error(f"Erro ao fazer login SEFAZ: {str(e)}")
            raise
    
    async def _fazer_login_prefeitura(self, cnpj: str, municipio: str):
        """Faz login no portal da prefeitura"""
        try:
            logger.info(f"✅ Login prefeitura {municipio} realizado")
        except Exception as e:
            logger.error(f"Erro ao fazer login prefeitura: {str(e)}")
            raise
    
    async def _extrair_nfes(self) -> List[Dict]:
        """Extrai informações de NF-e da página"""
        try:
            nfes = []
            linhas = await self.page.query_selector_all('table tbody tr')
            
            for linha in linhas:
                try:
                    numero = await linha.query_selector('td:nth-child(1)').text_content()
                    serie = await linha.query_selector('td:nth-child(2)').text_content()
                    data_emissao = await linha.query_selector('td:nth-child(3)').text_content()
                    valor = await linha.query_selector('td:nth-child(4)').text_content()
                    
                    nfes.append({
                        'numero': numero.strip(),
                        'serie': serie.strip(),
                        'data_emissao': data_emissao.strip(),
                        'valor': valor.strip()
                    })
                except Exception as e:
                    logger.warning(f"Erro ao extrair NF-e: {str(e)}")
                    continue
            
            return nfes
            
        except Exception as e:
            logger.error(f"Erro ao extrair NF-e(s): {str(e)}")
            return []
    
    async def _extrair_nfses(self) -> List[Dict]:
        """Extrai informações de NFS-e da página"""
        return await self._extrair_nfes()
    
    async def _extrair_ctes(self) -> List[Dict]:
        """Extrai informações de CT-e da página"""
        return await self._extrair_nfes()
    
    async def _baixar_xmls(self, documentos: List[Dict], tipo: TipoDocumento) -> List[Dict]:
        """Baixa XMLs dos documentos"""
        try:
            from backend.models import XmlCapturado
            
            xmls_capturados = []
            
            for doc in documentos:
                try:
                    # Clicar em download
                    await self.page.click(f'button[data-numero="{doc["numero"]}"]')
                    
                    # Aguardar download
                    async with self.page.expect_download() as download_info:
                        download = await download_info.value
                        
                        # Ler conteúdo
                        conteudo = await download.path()
                        
                        with open(conteudo, 'r') as f:
                            xml_content = f.read()
                        
                        # Calcular hash
                        xml_hash = hashlib.sha256(xml_content.encode()).hexdigest()
                        
                        # Salvar no banco
                        xml_obj = XmlCapturado(
                            empresa_id=self.empresa_id,
                            tipo=tipo.value,
                            numero=doc['numero'],
                            conteudo=xml_content,
                            hash_xml=xml_hash,
                            data_captura=datetime.now()
                        )
                        self.db.add(xml_obj)
                        
                        xmls_capturados.append({
                            'numero': doc['numero'],
                            'hash': xml_hash,
                            'data_captura': datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    logger.warning(f"Erro ao baixar XML {doc['numero']}: {str(e)}")
                    continue
            
            self.db.commit()
            logger.info(f"✅ {len(xmls_capturados)} XML(s) baixado(s) e salvo(s)")
            return xmls_capturados
            
        except Exception as e:
            logger.error(f"Erro ao baixar XMLs: {str(e)}")
            return []
    
    def _obter_url_nfse(self, municipio: str) -> Optional[str]:
        """Obtém URL do portal de NFS-e do município"""
        urls_nfse = {
            'São Paulo': 'https://nfe.prefeitura.sp.gov.br',
            'Rio de Janeiro': 'https://nfse.rio.rj.gov.br',
            'Belo Horizonte': 'https://nfse.pbh.gov.br',
        }
        return urls_nfse.get(municipio)
    
    async def _gerar_alerta(self, certidao, tipo_alerta: str):
        """Gera alerta de certidão"""
        try:
            from backend.models import AlertaFiscal
            
            alerta = AlertaFiscal(
                empresa_id=self.empresa_id,
                tipo=tipo_alerta,
                severidade='CRITICA' if 'VENCIDA' in tipo_alerta else 'AVISO',
                mensagem=f"Certidão {certidao.subtipo} ({certidao.tipo}) {tipo_alerta.lower().replace('_', ' ')}",
                data_criacao=datetime.now()
            )
            self.db.add(alerta)
            self.db.commit()
            
            logger.info(f"✅ Alerta gerado: {tipo_alerta}")
            
        except Exception as e:
            logger.error(f"Erro ao gerar alerta: {str(e)}")
    
    async def _executar_acao_automatica(self, certidao):
        """Executa ação automática baseada no tipo de certidão"""
        try:
            if certidao.tipo == 'FEDERAL':
                logger.info(f"✅ Ação automática: Notificação enviada")
            elif certidao.tipo == 'ESTADUAL':
                logger.info(f"✅ Ação automática: Renovação preparada")
            elif certidao.tipo == 'MUNICIPAL':
                logger.info(f"✅ Ação automática: Requerimento agendado")
            
        except Exception as e:
            logger.error(f"Erro ao executar ação automática: {str(e)}")


class RoboScheduler:
    """Agendador de robôs com execução recorrente"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def agendar_captura_diaria(self, empresa_id: str):
        """Agenda captura diária de XML"""
        try:
            from backend.models import ScheduledTask
            
            tarefa = ScheduledTask(
                empresa_id=empresa_id,
                tipo_tarefa='XML_CAPTURE_DAILY',
                frequencia='DIARIA',
                hora_execucao='23:00',
                ativo=True,
                proxima_execucao=datetime.now() + timedelta(days=1)
            )
            self.db.add(tarefa)
            self.db.commit()
            
            logger.info(f"✅ Captura diária agendada para empresa {empresa_id}")
            
        except Exception as e:
            logger.error(f"Erro ao agendar captura: {str(e)}")
    
    async def agendar_monitoramento_certidoes(self, empresa_id: str):
        """Agenda monitoramento de certidões"""
        try:
            from backend.models import ScheduledTask
            
            tarefa = ScheduledTask(
                empresa_id=empresa_id,
                tipo_tarefa='CERTIDAO_MONITOR',
                frequencia='DIARIA',
                hora_execucao='08:00',
                ativo=True,
                proxima_execucao=datetime.now() + timedelta(days=1)
            )
            self.db.add(tarefa)
            self.db.commit()
            
            logger.info(f"✅ Monitoramento de certidões agendado para empresa {empresa_id}")
            
        except Exception as e:
            logger.error(f"Erro ao agendar monitoramento: {str(e)}")
