"""Clients para integração com serviços externos"""

from .azure_auth_client import AzureAuthClient, AuthenticationError
from .sharepoint_client import SharePointClient, SharePointFile, SharePointError

__all__ = [
    'AzureAuthClient',
    'AuthenticationError',
    'SharePointClient',
    'SharePointFile',
    'SharePointError'
]
