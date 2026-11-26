"""Middleware de geração e verificação de tokens autenticados para o Task Manager API."""

import logging
from typing import Any, Dict, Optional
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

logger = logging.getLogger(__name__)


def _get_serializer() -> URLSafeTimedSerializer:
    """Retorna serializador assinado com SECRET_KEY da aplicação ativa."""
    secret = current_app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret, salt="task-manager-auth-salt")


def generate_auth_token(user_dict: Dict[str, Any]) -> str:
    """Gera token assinado criptograficamente para o usuário autenticado."""
    serializer = _get_serializer()
    payload = {
        "id": user_dict.get("id"),
        "email": user_dict.get("email"),
        "role": user_dict.get("role", "user"),
    }
    return serializer.dumps(payload)


def verify_auth_token(token: str, max_age: int = 86400) -> Optional[Dict[str, Any]]:
    """Valida a assinatura e validade temporal de um token recebido."""
    serializer = _get_serializer()
    try:
        return serializer.loads(token, max_age=max_age)
    except (SignatureExpired, BadSignature) as exc:
        logger.debug("Token inválido ou expirado: %s", exc)
        return None
