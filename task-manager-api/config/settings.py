"""Configurações centralizadas para o serviço Task Manager API."""

import os
from typing import NamedTuple


class EmailConfig(NamedTuple):
    """Configuração de servidor SMTP para envio de notificações."""
    host: str
    port: int
    user: str
    password: str


class Config:
    """Configuração base da aplicação com variáveis de ambiente e fallbacks seguros."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secure-secret-key-task-manager-32-chars")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///tasks.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")
    PORT = int(os.getenv("PORT", "5000"))
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # Credenciais SMTP desacopladas
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "taskmanager@gmail.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "dev-smtp-secret-key")


def get_config() -> Config:
    """Retorna instância de configuração ativa."""
    return Config()
