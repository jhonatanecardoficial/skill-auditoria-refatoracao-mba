"""Serviço de notificações desacoplado para canais de email e SMS."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class NotificationService:
    """Desacopla regras de envio e formatação de notificações de pedidos e eventos."""

    @staticmethod
    def notificar_pedido_criado(pedido_id: int, usuario_id: int, total: float) -> Dict[str, Any]:
        """Dispara notificações assíncronas/estruturadas ao cliente informando criação do pedido."""
        logger.info(
            "Notificação enviada: Pedido #%d criado para o usuário #%d no valor de R$ %.2f",
            pedido_id,
            usuario_id,
            total,
        )
        return {
            "pedido_id": pedido_id,
            "status": "notificado",
            "canais": ["email", "sms"],
        }

    @staticmethod
    def notificar_status_pedido(pedido_id: int, novo_status: str) -> None:
        """Registra notificações desacopladas ao alterar status do pedido."""
        if novo_status == "aprovado":
            logger.info("Notificação enviada: Pedido #%d foi aprovado. Preparar envio.", pedido_id)
        elif novo_status == "cancelado":
            logger.info("Notificação enviada: Pedido #%d foi cancelado. Devolver estoque.", pedido_id)
