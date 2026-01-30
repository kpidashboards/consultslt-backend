"""Robôs de automação"""

from .ingestion_robot import DocumentIngestionRobot, IngestionConfig, IngestionResult
from .sharepoint_ingestion_robot import (
    SharePointIngestionRobot,
    SharePointIngestionConfig,
    get_robot,
    start_ingestion_scheduler,
    stop_ingestion_scheduler
)

__all__ = [
    'DocumentIngestionRobot',
    'IngestionConfig',
    'IngestionResult',
    'SharePointIngestionRobot',
    'SharePointIngestionConfig',
    'get_robot',
    'start_ingestion_scheduler',
    'stop_ingestion_scheduler'
]
