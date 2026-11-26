"""Serviço de domínio para orquestração de regras de negócio de Pedidos."""

import logging
from typing import Any, Dict, List
from src.models.pedido import PedidoModel
from src.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Constantes de regras de negócio
DESCONTO_CLIENTE_VIP = 0.05
LIMITE_ITENS_PEDIDO = 50


class PedidoService:
    """Orquestra regras de validação comercial, criação atômica e disparo de notificações."""

    @staticmethod
    def processar_pedido(usuario_id: int, itens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aplica regras de negócio e cria pedido via Model de forma atômica."""
        if len(itens) > LIMITE_ITENS_PEDIDO:
            return {"erro": f"Limite máximo de {LIMITE_ITENS_PEDIDO} itens por pedido excedido"}

        resultado = PedidoModel.criar(usuario_id, itens)
        if "erro" not in resultado:
            NotificationService.notificar_pedido_criado(
                pedido_id=resultado["pedido_id"],
                usuario_id=usuario_id,
                total=resultado["total"],
            )
        return resultado

    @staticmethod
    def atualizar_status(pedido_id: int, novo_status: str) -> bool:
        """Atualiza status do pedido e dispara notificações de mudança de estado."""
        atualizado = PedidoModel.atualizar_status(pedido_id, novo_status)
        if atualizado:
            NotificationService.notificar_status_pedido(pedido_id, novo_status)
        return atualizado
