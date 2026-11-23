"""Configurações da aplicação Loja API.

Centraliza variáveis de ambiente, configurações de banco e chaves de segurança.
"""

import os
from typing import NamedTuple


class Settings(NamedTuple):
    """Estrutura imutável de configurações da aplicação."""
    secret_key: str
    debug: bool
    db_path: str
    port: int
    environment: str


def load_settings() -> Settings:
    """Carrega as configurações a partir de variáveis de ambiente com fallbacks seguros.

    Returns:
        Settings: Objeto contendo os parâmetros configurados.
    """
    return Settings(
        secret_key=os.getenv("SECRET_KEY", "dev-secure-secret-key-32-chars-long"),
        debug=os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1"),
        db_path=os.getenv("DATABASE_PATH", "loja.db"),
        port=int(os.getenv("PORT", "5000")),
        environment=os.getenv("ENVIRONMENT", "development")
    )


settings = load_settings()
