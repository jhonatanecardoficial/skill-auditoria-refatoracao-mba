"""Middleware centralizado de tratamento e padronização de erros HTTP para o Task Manager API."""

import logging
from typing import Tuple
from flask import Flask, jsonify, Response
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Registra manipuladores globais de erro HTTP na aplicação Flask.

    Args:
        app: Instância do Flask ativa.
    """

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException) -> Tuple[Response, int]:
        """Trata exceções HTTP conhecidas (400, 401, 404, etc.) preservando payload uniforme."""
        return jsonify({"error": exc.description}), exc.code or 500

    @app.errorhandler(Exception)
    def handle_generic_exception(exc: Exception) -> Tuple[Response, int]:
        """Trata exceções genéricas inesperadas sem vazar dados confidenciais ou stack traces."""
        logger.error("Exceção não tratada capturada no servidor: %s", exc, exc_info=True)
        return jsonify({"error": "Erro interno do servidor"}), 500
