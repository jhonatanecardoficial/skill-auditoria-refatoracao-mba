"""Fábrica de aplicação (Application Factory) para o serviço da Loja."""

import os
from flask import Flask
from flask_cors import CORS

from src.config.settings import settings
from src.database.connection import close_db, init_db
from src.middlewares.error_handler import register_error_handlers
from src.routes import (
    produto_bp,
    usuario_bp,
    pedido_bp,
    relatorio_bp,
    health_bp,
    admin_bp,
)


def create_app(test_config: dict = None) -> Flask:
    """Cria e configura uma instância da aplicação Flask no padrão MVC.

    Args:
        test_config: Dicionário opcional de configurações para testes.

    Returns:
        Flask: Instância da aplicação pronta para execução.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    app.config["ENVIRONMENT"] = os.getenv("ENVIRONMENT", settings.environment)

    if test_config:
        app.config.update(test_config)

    # Configuração de CORS
    CORS(app)

    # Teardown de contexto para fechar conexões de banco
    app.teardown_appcontext(close_db)

    # Registro de tratador centralizado de erros
    register_error_handlers(app)

    # Registro dos Blueprints MVC
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)

    # Inicializa banco e seeds no primeiro boot
    init_db(app.config.get("DATABASE_PATH", settings.db_path))

    return app
