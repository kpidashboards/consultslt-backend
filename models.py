"""
Modelos de banco de dados do SLTWEB ConsultSLT Enterprise
SQLAlchemy ORM com suporte a multi-tenancy
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, Decimal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()

# ============================================================================
# MODELOS DE TENANT E USUÁRIOS
# ============================================================================

class Tenant(Base):
    """Modelo de Tenant (Empresa)"""
    __tablename__ = 'tenants'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    razao_social = Column(String(255), nullable=False)
    nome_fantasia = Column(String(255))
    inscricao_estadual = Column(String(20))
    inscricao_municipal = Column(String(20))
    cnae = Column(String(10))
    regime_fiscal = Column(String(50))  # SIMPLES_NACIONAL, LUCRO_PRESUMIDO, LUCRO_REAL
    endereco = Column(String(255))
    numero = Column(String(20))
    complemento = Column(String(255))
    bairro = Column(String(100))
    municipio = Column(String(100))
    estado = Column(String(2))
    cep = Column(String(10))
    telefone = Column(String(20))
    email = Column(String(255))
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    usuarios = relationship("Usuario", back_populates="tenant")
    empresas = relationship("Empresa", back_populates="tenant")
    alertas = relationship("AlertaFiscal", back_populates="tenant")


class Usuario(Base):
    """Modelo de Usuário"""
    __tablename__ = 'usuarios'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey('tenants.id'), nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    telefone = Column(String(20))
    cargo = Column(String(100))
    perfil = Column(String(50))  # ADMIN, FISCAL, ANALISTA, CLIENTE
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    ultimo_acesso = Column(DateTime)
    
    # Relacionamentos
    tenant = relationship("Tenant", back_populates="usuarios")


# ============================================================================
# MODELOS FISCAIS
# ============================================================================

class Empresa(Base):
    """Modelo de Empresa (Filial/Unidade)"""
    __tablename__ = 'empresas'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey('tenants.id'), nullable=False)
    cnpj = Column(String(18), nullable=False)
    nome_fantasia = Column(String(255))
    inscricao_estadual = Column(String(20))
    inscricao_municipal = Column(String(20))
    regime_fiscal = Column(String(50))
    receita_bruta_12m = Column(Decimal(15, 2), default=0)
    receita_bruta_trimestral = Column(Decimal(15, 2), default=0)
    data_constituicao = Column(DateTime)
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    tenant = relationship("Tenant", back_populates="empresas")
    certidoes = relationship("Certidao", back_populates="empresa")
    xmls = relationship("XmlCapturado", back_populates="empresa")
    das = relationship("DAS", back_populates="empresa")


class Certidao(Base):
    """Modelo de Certidão (Federal, Estadual, Municipal)"""
    __tablename__ = 'certidoes'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    tipo = Column(String(50), nullable=False)  # FEDERAL, ESTADUAL, MUNICIPAL
    subtipo = Column(String(100), nullable=False)  # CND, CNDT, CNPJ, etc
    orgao = Column(String(255))
    numero = Column(String(50))
    data_emissao = Column(DateTime)
    data_validade = Column(DateTime)
    status = Column(String(50))  # ATIVA, VENCIDA, CANCELADA
    conteudo = Column(Text)
    data_captura = Column(DateTime, default=datetime.now)
    data_criacao = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="certidoes")


class DAS(Base):
    """Modelo de DAS (Documento de Arrecadação do Simples Nacional)"""
    __tablename__ = 'das'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    mes = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    anexo = Column(String(20))  # ANEXO_I, ANEXO_II, etc
    rbt_trimestral = Column(Decimal(15, 2))
    aliquota = Column(Decimal(5, 2))
    imposto = Column(Decimal(15, 2))
    multa = Column(Decimal(15, 2), default=0)
    juros = Column(Decimal(15, 2), default=0)
    total = Column(Decimal(15, 2))
    data_vencimento = Column(DateTime)
    status = Column(String(50))  # ABERTO, PAGO, ATRASADO, CANCELADO
    numero_documento = Column(String(50))
    data_pagamento = Column(DateTime)
    data_criacao = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="das")


class FatorR(Base):
    """Modelo de Fator R"""
    __tablename__ = 'fator_r'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    periodo = Column(String(10), nullable=False)  # YYYY-MM
    receita_servicos = Column(Decimal(15, 2))
    receita_total = Column(Decimal(15, 2))
    folha_pagamento = Column(Decimal(15, 2))
    fator_r_calculado = Column(Decimal(5, 4))
    fator_r_ajustado = Column(Decimal(5, 4))
    percentual_servicos = Column(Decimal(5, 2))
    data_calculo = Column(DateTime, default=datetime.now)


# ============================================================================
# MODELOS DE AUTOMAÇÃO (RPA)
# ============================================================================

class XmlCapturado(Base):
    """Modelo de XML Capturado"""
    __tablename__ = 'xmls_capturados'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    tipo = Column(String(20), nullable=False)  # NFE, NFSE, CTE, MDFE
    numero = Column(String(50))
    serie = Column(String(10))
    chave_acesso = Column(String(50), unique=True)
    data_emissao = Column(DateTime)
    valor_total = Column(Decimal(15, 2))
    valor_icms = Column(Decimal(15, 2), default=0)
    valor_ipi = Column(Decimal(15, 2), default=0)
    cnpj_destinatario = Column(String(18))
    conteudo = Column(Text)
    hash_xml = Column(String(64))
    status = Column(String(50))  # CAPTURADO, VALIDADO, AUDITADO
    data_captura = Column(DateTime, default=datetime.now)
    data_criacao = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="xmls")


class RoboLog(Base):
    """Modelo de Log de Execução de Robôs"""
    __tablename__ = 'robo_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    tipo_robo = Column(String(100), nullable=False)  # ECAC, XML_CAPTURE, CERTIDAO_MONITOR
    tipo_xml = Column(String(20))  # NFE, NFSE, CTE
    status = Column(String(50))  # SUCESSO, ERRO, AGUARDANDO
    mensagem = Column(Text)
    dados_entrada = Column(Text)
    dados_saida = Column(Text)
    tempo_execucao = Column(Integer)  # em segundos
    data_execucao = Column(DateTime, default=datetime.now)
    data_criacao = Column(DateTime, default=datetime.now)


class ScheduledTask(Base):
    """Modelo de Tarefas Agendadas"""
    __tablename__ = 'scheduled_tasks'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    tipo_tarefa = Column(String(100), nullable=False)  # ECAC_DAILY, XML_CAPTURE, CERTIDAO_MONITOR
    frequencia = Column(String(50))  # DIARIA, SEMANAL, MENSAL
    hora_execucao = Column(String(5))  # HH:MM
    dia_semana = Column(String(20))  # Segunda, Terça, etc (para semanal)
    dia_mes = Column(Integer)  # 1-31 (para mensal)
    ativo = Column(Boolean, default=True)
    proxima_execucao = Column(DateTime)
    ultima_execucao = Column(DateTime)
    data_criacao = Column(DateTime, default=datetime.now)


# ============================================================================
# MODELOS DE AUDITORIA
# ============================================================================

class RegistroSPED(Base):
    """Modelo de Registro SPED"""
    __tablename__ = 'registros_sped'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    tipo_registro = Column(String(10), nullable=False)  # 0000, C100, D100, K100, etc
    bloco = Column(String(20))  # BLOCO_0, BLOCO_C, BLOCO_D, BLOCO_K, etc
    dados = Column(Text)  # JSON com dados do registro
    numero_linha = Column(Integer)
    data_processamento = Column(DateTime, default=datetime.now)


class Divergencia(Base):
    """Modelo de Divergência Fiscal"""
    __tablename__ = 'divergencias'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    tipo = Column(String(100), nullable=False)  # NF_NAO_ENCONTRADA, DIVERGENCIA_VALOR, etc
    descricao = Column(Text)
    numero_nf = Column(String(50))
    serie = Column(String(10))
    valor_xml = Column(Decimal(15, 2))
    valor_sped = Column(Decimal(15, 2))
    diferenca = Column(Decimal(15, 2))
    status = Column(String(50))  # ABERTA, ANALISADA, RESOLVIDA
    data_identificacao = Column(DateTime, default=datetime.now)
    data_resolucao = Column(DateTime)


# ============================================================================
# MODELOS DE INTELIGÊNCIA FISCAL
# ============================================================================

class RiscoFiscal(Base):
    """Modelo de Risco Fiscal Identificado"""
    __tablename__ = 'riscos_fiscais'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    regra = Column(String(100), nullable=False)  # FATURAMENTO_ACIMA_LIMITE, DEFIS_ATRASADO, etc
    descricao = Column(Text)
    severidade = Column(String(50))  # CRITICA, ALTA, MEDIA, BAIXA
    acao_recomendada = Column(String(100))
    score_risco = Column(Float)
    status = Column(String(50))  # ABERTO, ANALISADO, RESOLVIDO
    data_identificacao = Column(DateTime, default=datetime.now)
    data_resolucao = Column(DateTime)


class SugestaoRegularizacao(Base):
    """Modelo de Sugestão de Regularização"""
    __tablename__ = 'sugestoes_regularizacao'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    tipo = Column(String(100), nullable=False)
    titulo = Column(String(255))
    descricao = Column(Text)
    acao_recomendada = Column(Text)
    prazo = Column(String(50))
    prioridade = Column(Integer)
    impacto = Column(Text)
    status = Column(String(50))  # ABERTA, IMPLEMENTADA, DESCARTADA
    data_criacao = Column(DateTime, default=datetime.now)
    data_implementacao = Column(DateTime)


# ============================================================================
# MODELOS DE ALERTAS
# ============================================================================

class AlertaFiscal(Base):
    """Modelo de Alerta Fiscal"""
    __tablename__ = 'alertas_fiscais'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey('tenants.id'), nullable=False)
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    tipo = Column(String(100), nullable=False)  # CERTIDAO_VENCIDA, DEFIS_ATRASADO, etc
    severidade = Column(String(50))  # CRITICA, AVISO, INFO
    mensagem = Column(Text)
    lido = Column(Boolean, default=False)
    data_criacao = Column(DateTime, default=datetime.now)
    data_leitura = Column(DateTime)
    
    # Relacionamentos
    tenant = relationship("Tenant", back_populates="alertas")


# ============================================================================
# MODELOS DE CREDENCIAIS E SEGURANÇA
# ============================================================================

class Credencial(Base):
    """Modelo de Credenciais (e-CAC, Certificados, etc)"""
    __tablename__ = 'credenciais'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    tipo = Column(String(50), nullable=False)  # ECAC, CERTIFICADO_A1, CERTIFICADO_A3
    cpf_cnpj = Column(String(18))
    usuario = Column(String(255))
    senha_encriptada = Column(String(255))
    certificado_path = Column(String(255))
    certificado_senha = Column(String(255))
    data_validade = Column(DateTime)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============================================================================
# MODELOS DE AUDITORIA DE SISTEMA
# ============================================================================

class AuditoriaLog(Base):
    """Modelo de Log de Auditoria do Sistema"""
    __tablename__ = 'auditoria_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id = Column(String(36), ForeignKey('usuarios.id'))
    acao = Column(String(255), nullable=False)
    tabela = Column(String(100))
    registro_id = Column(String(36))
    dados_antes = Column(Text)
    dados_depois = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    data_criacao = Column(DateTime, default=datetime.now)

# ============================================================================
# SCHEMAS Pydantic – AUTENTICAÇÃO E SEGURANÇA (FASTAPI)
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class UserResponse(BaseModel):
    id: str
    nome: str
    email: EmailStr
    perfil: Optional[str] = None
    tenant_id: Optional[str] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

