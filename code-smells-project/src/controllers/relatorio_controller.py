"""Controller responsável por emitir relatórios gerenciais e estatísticas."""

from typing import Tuple
from flask import jsonify, Response
from src.models.pedido import PedidoModel


def relatorio_vendas() -> Tuple[Response, int]:
    """Retorna os indicadores consolidados de faturamento e status de pedidos."""
    relatorio = PedidoModel.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
