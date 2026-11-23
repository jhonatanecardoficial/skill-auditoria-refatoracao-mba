"""Controller responsável por diagnósticos de saúde (Health Check) e catálogo raiz."""

from typing import Tuple
from flask import jsonify, Response
from src.database.connection import get_db
from src.config.settings import settings


def health_check() -> Tuple[Response, int]:
    """Verifica a conectividade do banco de dados e retorna métricas sem vazar segredos."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1")
    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    pedidos = cursor.fetchone()[0]

    return (
        jsonify(
            {
                "status": "ok",
                "database": "connected",
                "counts": {
                    "produtos": produtos,
                    "usuarios": usuarios,
                    "pedidos": pedidos,
                },
                "versao": "1.0.0",
                "ambiente": settings.environment,
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
