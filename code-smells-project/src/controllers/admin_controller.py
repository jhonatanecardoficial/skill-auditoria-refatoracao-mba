"""Controller administrativo para operações de manutenção e consultas controladas."""

import logging
from typing import Tuple
from flask import jsonify, request, Response
from src.database.connection import get_db

logger = logging.getLogger(__name__)


def reset_database() -> Tuple[Response, int]:
    """Reinicializa o estado das tabelas da aplicação."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM itens_pedido")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM produtos")
        cursor.execute("DELETE FROM usuarios")
        db.commit()
        logger.warning("Banco de dados resetado via endpoint administrativo.")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
    except Exception as exc:
        db.rollback()
        return jsonify({"erro": str(exc), "sucesso": False}), 500


def executar_query() -> Tuple[Response, int]:
    """Executa consultas parametrizadas ou administrativas com tratamento adequado de erros."""
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Query não informada"}), 400

    query = dados.get("sql", "").strip()
    if not query:
        return jsonify({"erro": "Query não informada"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query)
        if query.upper().startswith("SELECT"):
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            return jsonify({"dados": result, "sucesso": True}), 200

        db.commit()
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
    except Exception as exc:
        db.rollback()
        return jsonify({"erro": str(exc)}), 500
