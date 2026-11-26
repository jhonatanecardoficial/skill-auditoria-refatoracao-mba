"""Configurações da aplicação Loja API.

Centraliza variáveis de ambiente, configurações de banco e chaves de segurança
com comportamento fail-closed por padrão.
"""

import os
import secrets
from typing import NamedTuple, Union, List


class Settings(NamedTuple):
    """Estrutura imutável de configurações da aplicação."""
    secret_key: str
    debug: bool
    db_path: str
    port: int
    environment: str
    cors_origins: Union[str, List[str]]


def load_settings() -> Settings:
    """Carrega as configurações a partir de variáveis de ambiente com padrão fail-closed.

    Returns:
        Settings: Objeto contendo os parâmetros configurados.
    """
    raw_cors = (os.getenv("CORS_ORIGINS") or "").strip()
    cors_origins: Union[str, List[str]] = (
        [o.strip() for o in raw_cors.split(",") if o.strip()] if raw_cors else "*"
    )
    return Settings(
        secret_key=(os.getenv("SECRET_KEY") or "").strip() or secrets.token_hex(32),
        debug=(os.getenv("FLASK_DEBUG") or "False").strip().lower() in ("true", "1"),
        db_path=(os.getenv("DATABASE_PATH") or "loja.db").strip(),
        port=int((os.getenv("PORT") or "5000").strip()),
        environment=(os.getenv("ENVIRONMENT") or "production").strip().lower(),
        cors_origins=cors_origins,
    )


settings = load_settings()
