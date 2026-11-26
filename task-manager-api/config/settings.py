"""Configurações centralizadas para o serviço Task Manager API (Fail-Closed)."""

import os
import secrets
from typing import NamedTuple


class EmailConfig(NamedTuple):
    """Configuração de servidor SMTP para envio de notificações."""
    host: str
    port: int
    user: str
    password: str


class Config:
    """Configuração base da aplicação com variáveis de ambiente e padrão fail-closed."""

    SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip() or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = (os.getenv("SQLALCHEMY_DATABASE_URI") or "sqlite:///tasks.db").strip()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = (os.getenv("FLASK_DEBUG") or "False").strip().lower() in ("true", "1")
    PORT = int((os.getenv("PORT") or "5000").strip())
    ENVIRONMENT = (os.getenv("ENVIRONMENT") or "production").strip().lower()
    _raw_cors = (os.getenv("CORS_ORIGINS") or "").strip()
    CORS_ORIGINS = [o.strip() for o in _raw_cors.split(",") if o.strip()] if _raw_cors else "*"

    # Credenciais SMTP desacopladas (sem senhas hardcoded)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int((os.getenv("SMTP_PORT") or "587").strip())
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def get_config() -> Config:
    """Retorna instância de configuração ativa."""
    return Config()
