"""Middleware centralizado de tratamento e padronização de erros HTTP."""

import logging
from typing import Tuple
from flask import Flask, jsonify, Response
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Registra manipuladores globais de erro na instância do Flask.

    Args:
        app: Instância ativa da aplicação Flask.
    """

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException) -> Tuple[Response, int]:
        """Trata exceções HTTP conhecidas (400, 401, 403, 404, 405, etc.)."""
        response = jsonify({"erro": exc.description, "sucesso": False})
        return response, exc.code or 500

    @app.errorhandler(Exception)
    def handle_generic_exception(exc: Exception) -> Tuple[Response, int]:
        """Trata exceções inesperadas capturando stack traces no log sem expor dados internos ao cliente."""
        logger.error("Exceção não tratada capturada: %s", exc, exc_info=True)
        return (
            jsonify({"erro": "Erro interno do servidor", "sucesso": False}),
            500,
        )
