"""Controller responsável por diagnósticos de saúde (Health Check) e catálogo raiz."""

from typing import Tuple
from flask import current_app, jsonify, Response
from src.models.health import HealthModel
from src.config.settings import settings


def health_check() -> Tuple[Response, int]:
    """Verifica a conectividade do banco de dados e retorna métricas sem vazar segredos ou executar SQL direto no controller."""
    stats = HealthModel.get_stats()
    env = current_app.config.get("ENVIRONMENT", settings.environment)

    return (
        jsonify(
            {
                "status": "ok",
                "database": "connected",
                "counts": stats,
                "versao": "1.0.0",
                "ambiente": env,
            }
        ),
        200,
    )


def index() -> Tuple[Response, int]:
    """Retorna o catálogo de rotas e boas-vindas da API."""
    return (
        jsonify(
            {
                "mensagem": "Bem-vindo à API da Loja",
                "versao": "1.0.0",
                "endpoints": {
                    "produtos": "/produtos",
                    "usuarios": "/usuarios",
                    "pedidos": "/pedidos",
                    "login": "/login",
                    "relatorios": "/relatorios/vendas",
                    "health": "/health",
                },
            }
        ),
        200,
    )
