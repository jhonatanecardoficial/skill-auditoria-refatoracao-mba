"""Controller administrativo para operações de manutenção controladas."""

import logging
from typing import Tuple
from flask import jsonify, Response
from src.database.connection import get_db

logger = logging.getLogger(__name__)


def reset_database() -> Tuple[Response, int]:
    """Reinicializa o estado das tabelas da aplicação de forma segura e transacional.

    Este método só pode ser invocado através de rotas protegidas por @require_admin
    em ambientes autorizados (development / testing).
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM itens_pedido")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM produtos")
        cursor.execute("DELETE FROM usuarios")
        db.commit()
        logger.warning("Banco de dados resetado com autorização administrativa.")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
    except Exception as exc:
        db.rollback()
        logger.error("Falha ao resetar banco de dados: %s", exc, exc_info=True)
        return jsonify({"erro": "Erro ao resetar banco de dados", "sucesso": False}), 500
