"""
Serviço de e-CAC automático para acesso a certidões e DEFIS
Implementação com Selenium + Anti-Captcha
"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
import time

logger = logging.getLogger(__name__)

class EcacService:
    """Serviço de e-CAC para acesso automático"""
    
        self.db = db
        self.driver = None
        self.base_url = "https://www8.receita.fazenda.gov.br/SimplesNacional/"
        self.timeout = 30
        self.anti_captcha_key = "YOUR_ANTI_CAPTCHA_KEY"
    
    def _inicializar_navegador(self) -> webdriver.Chrome:
        """Inicializa navegador Chrome com opções otimizadas"""
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            driver = webdriver.Chrome(options=options)
            logger.info("✅ Navegador Chrome inicializado")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar navegador: {str(e)}")
            raise
    
    async def obter_defis(self, cnpj: str, cpf: str, senha: str) -> Dict:
        """Obtém DEFIS do e-CAC"""
        try:
            logger.info(f"🔍 Obtendo DEFIS para CNPJ {cnpj}")
            
            self.driver = self._inicializar_navegador()
            
            # Acessar portal
            self.driver.get(f"{self.base_url}Consultas/ConsultarDEFIS.aspx")
            
            # Aguardar carregamento
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "txtCNPJ"))
            )
            
            # Preencher CNPJ
            campo_cnpj = self.driver.find_element(By.ID, "txtCNPJ")
            campo_cnpj.clear()
            campo_cnpj.send_keys(cnpj)
            
            # Preencher CPF
            campo_cpf = self.driver.find_element(By.ID, "txtCPF")
            campo_cpf.clear()
            campo_cpf.send_keys(cpf)
            
            # Preencher Senha
            campo_senha = self.driver.find_element(By.ID, "txtSenha")
            campo_senha.clear()
            campo_senha.send_keys(senha)
            
            # Resolver captcha
            await self._resolver_captcha()
            
            # Clicar em consultar
            botao_consultar = self.driver.find_element(By.ID, "btnConsultar")
            botao_consultar.click()
            
            # Aguardar resultados
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "resultado"))
            )
            
            # Extrair dados
            defis = await self._extrair_defis()
            
            self.driver.quit()
            
            logger.info(f"✅ {len(defis)} DEFIS obtidos com sucesso")
            
            return {
                'sucesso': True,
                'cnpj': cnpj,
                'defis': defis,
                'data_consulta': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter DEFIS: {str(e)}")
            if self.driver:
                self.driver.quit()
            return {'sucesso': False, 'erro': str(e)}
    
    async def obter_certidoes(self, cnpj: str, cpf: str, senha: str) -> Dict:
        """Obtém certidões do e-CAC"""
        try:
            logger.info(f"🔍 Obtendo certidões para CNPJ {cnpj}")
            
            self.driver = self._inicializar_navegador()
            
            # Acessar portal
            self.driver.get(f"{self.base_url}Consultas/ConsultarCertidao.aspx")
            
            # Aguardar carregamento
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "txtCNPJ"))
            )
            
            # Preencher CNPJ
            campo_cnpj = self.driver.find_element(By.ID, "txtCNPJ")
            campo_cnpj.clear()
            campo_cnpj.send_keys(cnpj)
            
            # Preencher CPF
            campo_cpf = self.driver.find_element(By.ID, "txtCPF")
            campo_cpf.clear()
            campo_cpf.send_keys(cpf)
            
            # Preencher Senha
            campo_senha = self.driver.find_element(By.ID, "txtSenha")
            campo_senha.clear()
            campo_senha.send_keys(senha)
            
            # Resolver captcha
            await self._resolver_captcha()
            
            # Clicar em consultar
            botao_consultar = self.driver.find_element(By.ID, "btnConsultar")
            botao_consultar.click()
            
            # Aguardar resultados
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "resultado"))
            )
            
            # Extrair dados
            certidoes = await self._extrair_certidoes()
            
            self.driver.quit()
            
            logger.info(f"✅ {len(certidoes)} certidão(ões) obtida(s) com sucesso")
            
            return {
                'sucesso': True,
                'cnpj': cnpj,
                'certidoes': certidoes,
                'data_consulta': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter certidões: {str(e)}")
            if self.driver:
                self.driver.quit()
            return {'sucesso': False, 'erro': str(e)}
    
    async def _resolver_captcha(self):
        """Resolve captcha usando Anti-Captcha"""
        try:
            logger.info("🤖 Resolvendo captcha...")
            
            # Encontrar iframe do captcha
            iframe = self.driver.find_element(By.TAG_NAME, "iframe")
            
            # Extrair site key
            site_key = iframe.get_attribute("data-sitekey")
            
            # Enviar para Anti-Captcha
            response = requests.post(
                "https://api.anti-captcha.com/createTask",
                json={
                    "clientKey": self.anti_captcha_key,
                    "task": {
                        "type": "NoCaptchaTaskProxyless",
                        "websiteURL": self.driver.current_url,
                        "websiteKey": site_key
                    }
                }
            )
            
            task_id = response.json()['taskId']
            
            # Aguardar solução
            while True:
                response = requests.post(
                    "https://api.anti-captcha.com/getTaskResult",
                    json={
                        "clientKey": self.anti_captcha_key,
                        "taskId": task_id
                    }
                )
                
                if response.json()['isReady']:
                    captcha_token = response.json()['solution']['gRecaptchaResponse']
                    
                    # Injetar token
                    self.driver.execute_script(
                        f"document.getElementById('g-recaptcha-response').innerHTML = '{captcha_token}';"
                    )
                    
                    logger.info("✅ Captcha resolvido")
                    break
                
                await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Erro ao resolver captcha: {str(e)}")
            raise
    
    async def _extrair_defis(self) -> List[Dict]:
        """Extrai dados de DEFIS da página"""
        try:
            defis = []
            
            # Encontrar tabela de resultados
            tabela = self.driver.find_element(By.CLASS_NAME, "resultado")
            linhas = tabela.find_elements(By.TAG_NAME, "tr")[1:]  # Pular header
            
            for linha in linhas:
                try:
                    colunas = linha.find_elements(By.TAG_NAME, "td")
                    
                    if len(colunas) >= 5:
                        defis.append({
                            'mes': colunas[0].text,
                            'ano': colunas[1].text,
                            'valor': Decimal(colunas[2].text.replace('R$', '').replace('.', '').replace(',', '.')),
                            'data_vencimento': colunas[3].text,
                            'status': colunas[4].text
                        })
                except Exception as e:
                    logger.warning(f"Erro ao extrair linha: {str(e)}")
                    continue
            
            return defis
            
        except Exception as e:
            logger.error(f"Erro ao extrair DEFIS: {str(e)}")
            return []
    
    async def _extrair_certidoes(self) -> List[Dict]:
        """Extrai dados de certidões da página"""
        try:
            certidoes = []
            
            # Encontrar tabela de resultados
            tabela = self.driver.find_element(By.CLASS_NAME, "resultado")
            linhas = tabela.find_elements(By.TAG_NAME, "tr")[1:]  # Pular header
            
            for linha in linhas:
                try:
                    colunas = linha.find_elements(By.TAG_NAME, "td")
                    
                    if len(colunas) >= 4:
                        certidoes.append({
                            'tipo': colunas[0].text,
                            'status': colunas[1].text,
                            'data_emissao': colunas[2].text,
                            'data_validade': colunas[3].text
                        })
                except Exception as e:
                    logger.warning(f"Erro ao extrair linha: {str(e)}")
                    continue
            
            return certidoes
            
        except Exception as e:
            logger.error(f"Erro ao extrair certidões: {str(e)}")
            return []


class SimplesNacionalService:
    """Serviço de cálculo de Simples Nacional"""
    
        self.db = db
        self.aliquotas = self._carregar_aliquotas()
    
    def _carregar_aliquotas(self) -> Dict:
        """Carrega alíquotas de Simples Nacional por anexo"""
        return {
            'ANEXO_I': {
                'descricao': 'Comércio em geral',
                'aliquotas': [
                    {'rbt': 180000, 'aliquota': 4.00},
                    {'rbt': 360000, 'aliquota': 5.47},
                    {'rbt': 540000, 'aliquota': 6.84},
                    {'rbt': 720000, 'aliquota': 7.54},
                    {'rbt': 900000, 'aliquota': 7.60},
                    {'rbt': 1080000, 'aliquota': 8.21},
                    {'rbt': 1260000, 'aliquota': 8.35},
                    {'rbt': 1440000, 'aliquota': 8.45},
                    {'rbt': 1620000, 'aliquota': 8.53},
                    {'rbt': 1800000, 'aliquota': 8.60},
                    {'rbt': 4800000, 'aliquota': 8.95},
                ]
            },
            'ANEXO_II': {
                'descricao': 'Atividades de prestação de serviços',
                'aliquotas': [
                    {'rbt': 180000, 'aliquota': 4.50},
                    {'rbt': 360000, 'aliquota': 7.30},
                    {'rbt': 540000, 'aliquota': 8.20},
                    {'rbt': 720000, 'aliquota': 8.70},
                    {'rbt': 900000, 'aliquota': 9.00},
                    {'rbt': 1080000, 'aliquota': 9.20},
                    {'rbt': 1260000, 'aliquota': 9.35},
                    {'rbt': 1440000, 'aliquota': 9.45},
                    {'rbt': 1620000, 'aliquota': 9.52},
                    {'rbt': 1800000, 'aliquota': 9.60},
                    {'rbt': 4800000, 'aliquota': 16.93},
                ]
            }
        }
    
    def calcular_das(self, rbt_trimestral: Decimal, anexo: str) -> Dict:
        """Calcula DAS baseado em RBT trimestral"""
        try:
            logger.info(f"💰 Calculando DAS para RBT {rbt_trimestral} - {anexo}")
            
            aliquotas = self.aliquotas.get(anexo, {}).get('aliquotas', [])
            
            # Encontrar alíquota correta
            aliquota = 0
            for faixa in aliquotas:
                if rbt_trimestral <= Decimal(str(faixa['rbt'])):
                    aliquota = Decimal(str(faixa['aliquota']))
                    break
            
            # Calcular imposto
            imposto = (rbt_trimestral * aliquota) / Decimal('100')
            
            resultado = {
                'rbt_trimestral': float(rbt_trimestral),
                'anexo': anexo,
                'aliquota': float(aliquota),
                'imposto': float(imposto),
                'data_calculo': datetime.now().isoformat()
            }
            
            logger.info(f"✅ DAS calculado: R$ {imposto:.2f}")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular DAS: {str(e)}")
            return {}
    
    def calcular_fator_r(self, receita_servicos: Decimal, receita_total: Decimal, folha_pagamento: Decimal) -> Dict:
        """Calcula Fator R"""
        try:
            logger.info("📊 Calculando Fator R")
            
            # Fator R = Folha de Pagamento / Receita de Serviços
            if receita_servicos == 0:
                fator_r = Decimal('0')
            else:
                fator_r = folha_pagamento / receita_servicos
            
            # Percentual de serviços
            if receita_total == 0:
                percentual_servicos = Decimal('0')
            else:
                percentual_servicos = (receita_servicos / receita_total) * Decimal('100')
            
            resultado = {
                'fator_r': float(fator_r),
                'percentual_servicos': float(percentual_servicos),
                'folha_pagamento': float(folha_pagamento),
                'receita_servicos': float(receita_servicos),
                'receita_total': float(receita_total),
                'data_calculo': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Fator R calculado: {fator_r:.4f}")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular Fator R: {str(e)}")
            return {}
