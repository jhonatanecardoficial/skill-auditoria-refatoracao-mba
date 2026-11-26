"""Controller administrativo para operações de manutenção controladas."""

import logging
from typing import Tuple
from flask import jsonify, Response
from src.models.admin import AdminModel

logger = logging.getLogger(__name__)


def reset_database() -> Tuple[Response, int]:
    """Reinicializa o estado das tabelas da aplicação delegando ao AdminModel.

    Este método só pode ser invocado através de rotas protegidas por @require_admin
    em ambientes explicitamente autorizados (development / testing).
    """
    try:
        AdminModel.reset_database()
        logger.warning("Banco de dados resetado com autorização administrativa.")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
    except Exception as exc:
        logger.error("Falha ao resetar banco de dados: %s", exc, exc_info=True)
        return jsonify({"erro": "Erro ao resetar banco de dados", "sucesso": False}), 500
