"""
Script de seed de dados de exemplo
Cria empresas, guias, alertas, certidões, etc para demonstração
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
import logging

# Adicionar backend ao path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from database import get_db_context
from models import Empresa, Guia, Alerta, Certidao, Debito, Obrigacao, Documento
from decimal import Decimal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_data():
    """
    Cria dados de exemplo para demonstração
    """
    try:
        logger.info("🌱 Iniciando seed de dados de exemplo...")
        
        with get_db_context() as db:
            # Verificar se já existem dados
            existing_empresas = db.query(Empresa).count()
            if existing_empresas > 0:
                logger.info(f"✓ Já existem {existing_empresas} empresas no banco. Pulando seed.")
                return
            
            # Criar empresas de exemplo
            empresas = [
                Empresa(
                    id=str(uuid.uuid4()),
                    cnpj="12.345.678/0001-90",
                    razao_social="TRES PINHEIROS LTDA",
                    nome_fantasia="Três Pinheiros",
                    regime_tributario="SIMPLES_NACIONAL",
                    email="contato@trespinheiros.com.br",
                    telefone="(11) 3456-7890",
                    inscricao_estadual="123.456.789.012",
                    cnae="4712-1/00",
                    endereco="Rua das Flores, 123",
                    municipio="São Paulo",
                    estado="SP",
                    cep="01234-567",
                    ativo=True
                ),
                Empresa(
                    id=str(uuid.uuid4()),
                    cnpj="98.765.432/0001-10",
                    razao_social="SUPER GALO RESTAURANTE LTDA",
                    nome_fantasia="Super Galo Rest.",
                    regime_tributario="LUCRO_PRESUMIDO",
                    email="financeiro@supergalo.com.br",
                    telefone="(11) 98765-4321",
                    inscricao_estadual="987.654.321.098",
                    cnae="5611-2/01",
                    endereco="Av. Principal, 456",
                    municipio="São Paulo",
                    estado="SP",
                    cep="04567-890",
                    ativo=True
                ),
                Empresa(
                    id=str(uuid.uuid4()),
                    cnpj="11.222.333/0001-44",
                    razao_social="MAFE RESTAURANTE E EVENTOS LTDA",
                    nome_fantasia="Mafe Restaurante",
                    regime_tributario="SIMPLES_NACIONAL",
                    email="contato@maferest.com.br",
                    telefone="(11) 91234-5678",
                    inscricao_estadual="112.223.334.445",
                    cnae="5611-2/01",
                    endereco="Rua Comercial, 789",
                    municipio="São Paulo",
                    estado="SP",
                    cep="02345-678",
                    ativo=True
                )
            ]
            
            for empresa in empresas:
                db.add(empresa)
            
            db.commit()
            logger.info(f"✓ Criadas {len(empresas)} empresas")
            
            # Criar guias de exemplo
            hoje = datetime.now(timezone.utc)
            guias = []
            
            for i, empresa in enumerate(empresas):
                # DAS
                guia_das = Guia(
                    id=str(uuid.uuid4()),
                    empresa_id=empresa.id,
                    tipo="DAS",
                    competencia=f"{hoje.month:02d}/{hoje.year}",
                    vencimento=hoje + timedelta(days=15+i*5),
                    valor=Decimal("1250.50"),
                    status="pendente",
                    codigo_barras="123456789012345678901234567890123456789012345"
                )
                guias.append(guia_das)
                
                # DARF
                guia_darf = Guia(
                    id=str(uuid.uuid4()),
                    empresa_id=empresa.id,
                    tipo="DARF",
                    competencia=f"{hoje.month:02d}/{hoje.year}",
                    vencimento=hoje + timedelta(days=20+i*3),
                    valor=Decimal("850.00"),
                    status="pendente"
                )
                guias.append(guia_darf)
            
            for guia in guias:
                db.add(guia)
            
            db.commit()
            logger.info(f"✓ Criadas {len(guias)} guias")
            
            # Criar certidões
            certidoes = []
            for empresa in empresas:
                certidao = Certidao(
                    id=str(uuid.uuid4()),
                    empresa_id=empresa.id,
                    tipo="Federal",
                    subtipo="CND",
                    numero=f"CND-{uuid.uuid4().hex[:8].upper()}",
                    orgao="Receita Federal",
                    data_emissao=hoje - timedelta(days=30),
                    data_validade=hoje + timedelta(days=150),
                    status="valida"
                )
                certidoes.append(certidao)
            
            for certidao in certidoes:
                db.add(certidao)
            
            db.commit()
            logger.info(f"✓ Criadas {len(certidoes)} certidões")
            
            # Criar alertas
            alertas = [
                Alerta(
                    id=str(uuid.uuid4()),
                    titulo="DAS vencendo em breve",
                    mensagem=f"DAS da empresa {empresas[0].nome_fantasia} vence em 3 dias",
                    tipo="fiscal",
                    severidade="alto",
                    prioridade="alta",
                    lido=False,
                    empresa_id=empresas[0].id
                ),
                Alerta(
                    id=str(uuid.uuid4()),
                    titulo="Certidão emitida com sucesso",
                    mensagem=f"Certidão Federal emitida para {empresas[1].nome_fantasia}",
                    tipo="certificado",
                    severidade="info",
                    lido=False,
                    empresa_id=empresas[1].id
                ),
                Alerta(
                    id=str(uuid.uuid4()),
                    titulo="Nova empresa cadastrada",
                    mensagem=f"Empresa {empresas[2].nome_fantasia} foi cadastrada no sistema",
                    tipo="sistema",
                    severidade="info",
                    lido=False,
                    empresa_id=empresas[2].id
                )
            ]
            
            for alerta in alertas:
                db.add(alerta)
            
            db.commit()
            logger.info(f"✓ Criados {len(alertas)} alertas")
            
            # Criar obrigações
            obrigacoes = []
            for empresa in empresas:
                obrigacao = Obrigacao(
                    id=str(uuid.uuid4()),
                    empresa_id=empresa.id,
                    tipo="DCTF Web",
                    descricao="Declaração de Débitos e Créditos Tributários Federais",
                    competencia=f"{hoje.month:02d}/{hoje.year}",
                    data_vencimento=hoje + timedelta(days=10),
                    status="pendente",
                    prioridade="alta"
                )
                obrigacoes.append(obrigacao)
            
            for obrigacao in obrigacoes:
                db.add(obrigacao)
            
            db.commit()
            logger.info(f"✓ Criadas {len(obrigacoes)} obrigações")
            
        logger.info("✅ Seed de dados concluído com sucesso!")
        logger.info(f"   - {len(empresas)} empresas")
        logger.info(f"   - {len(guias)} guias")
        logger.info(f"   - {len(certidoes)} certidões")
        logger.info(f"   - {len(alertas)} alertas")
        logger.info(f"   - {len(obrigacoes)} obrigações")
        
    except Exception as e:
        logger.error(f"❌ Erro ao executar seed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    seed_data()
