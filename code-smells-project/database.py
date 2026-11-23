"""Shim de compatibilidade para database legado.

Encaminha chamadas para o módulo estruturado em src.database.connection.
"""

from src.database.connection import get_db, init_db, close_db

__all__ = ["get_db", "init_db", "close_db"]
