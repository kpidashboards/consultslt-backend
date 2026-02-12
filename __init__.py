"""
Backend - ConsultSLT Web
Inicialização do pacote backend
Expõe apenas o router principal da API
"""

from .api import api_router

__all__ = ["api_router"]