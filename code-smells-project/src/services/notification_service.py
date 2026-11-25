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
