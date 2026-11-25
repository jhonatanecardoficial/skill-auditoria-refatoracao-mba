"""Controller responsável pelo ciclo de vida e processamento de Pedidos."""

import logging
from typing import Tuple
from flask import jsonify, request, Response
from src.models.pedido import PedidoModel
from src.services.pedido_service import PedidoService

logger = logging.getLogger(__name__)

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def criar_pedido() -> Tuple[Response, int]:
    """Valida a carga útil e orquestra a criação atômica de pedido."""
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens or not isinstance(itens, list) or len(itens) == 0:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    resultado = PedidoService.processar_pedido(usuario_id, itens)
    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    logger.info("Pedido %s criado com sucesso para o usuário %s", resultado["pedido_id"], usuario_id)

    return (
        jsonify(
            {
                "dados": resultado,
                "sucesso": True,
                "mensagem": "Pedido criado com sucesso",
            }
        ),
        201,
    )


def listar_pedidos_usuario(usuario_id: int) -> Tuple[Response, int]:
    """Retorna os pedidos pertencentes a um usuário específico."""
    pedidos = PedidoModel.get_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos() -> Tuple[Response, int]:
    """Retorna todos os pedidos da loja."""
    pedidos = PedidoModel.get_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id: int) -> Tuple[Response, int]:
    """Atualiza a situação operacional de um pedido."""
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    novo_status = dados.get("status", "")
    if novo_status not in STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido"}), 400

    PedidoModel.atualizar_status(pedido_id, novo_status)
    logger.info("Status do pedido %s atualizado para %s", pedido_id, novo_status)

    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
