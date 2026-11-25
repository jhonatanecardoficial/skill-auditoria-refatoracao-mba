"""Middleware de autenticação e controle de acesso baseado em tokens seguros."""

from functools import wraps
import logging
from typing import Any, Dict, Optional
from flask import current_app, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from src.config.settings import settings

logger = logging.getLogger(__name__)


def _get_serializer() -> URLSafeTimedSerializer:
    """Obtém o serializador criptográfico configurado com a secret key."""
    secret = (
        current_app.config.get("SECRET_KEY")
        if current_app
        else settings.secret_key
    )
    return URLSafeTimedSerializer(secret, salt="auth-token-salt")


def generate_auth_token(usuario: Dict[str, Any]) -> str:
    """Gera um token assinado contendo os dados essenciais do usuário.

    Args:
        usuario: Dicionário contendo dados do usuário autenticado.

    Returns:
        str: Token assinado e seguro.
    """
    serializer = _get_serializer()
    payload = {
        "id": usuario.get("id"),
        "email": usuario.get("email"),
        "tipo": usuario.get("tipo", "cliente"),
    }
    return serializer.dumps(payload)


def verify_auth_token(token: str, max_age: int = 86400) -> Optional[Dict[str, Any]]:
    """Verifica e decodifica o token assinado.

    Args:
        token: String contendo o token a ser validado.
        max_age: Validade máxima em segundos (padrão: 24 horas).

    Returns:
        Optional[Dict[str, Any]]: Dados decodificados ou None se inválido/expirado.
    """
    serializer = _get_serializer()
    try:
        dados = serializer.loads(token, max_age=max_age)
        return dados
    except (SignatureExpired, BadSignature) as exc:
        logger.debug("Token inválido ou expirado: %s", exc)
        return None
    except Exception as exc:
        logger.error("Falha ao validar token: %s", exc)
        return None


def require_admin(f):
    """Decorator para proteger endpoints administrativos destrutivos.

    Exige:
    1. Que o ambiente NÃO seja 'production' (bloqueia em produção);
    2. Header 'Authorization: Bearer <token>' válido;
    3. Usuário com papel (tipo) == 'admin'.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Verificação de restrição de ambiente (whitelist estrita)
        env = (
            current_app.config.get("ENVIRONMENT") or settings.environment
            if current_app
            else settings.environment
        )
        if env not in ("development", "testing"):
            return (
                jsonify(
                    {
                        "erro": "Operação não permitida neste ambiente",
                        "sucesso": False,
                    }
                ),
                403,
            )

        # 2. Extração do token Bearer
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return (
                jsonify(
                    {
                        "erro": "Token de autenticação não fornecido",
                        "sucesso": False,
                    }
                ),
                401,
            )

        token = auth_header.split(" ", 1)[1].strip()
        user_data = verify_auth_token(token)
        if not user_data:
            return (
                jsonify(
                    {
                        "erro": "Token inválido ou expirado",
                        "sucesso": False,
                    }
                ),
                401,
            )

        # 3. Verificação de papel administrativo
        if user_data.get("tipo") != "admin":
            return (
                jsonify(
                    {
                        "erro": "Acesso restrito a administradores",
                        "sucesso": False,
                    }
                ),
                403,
            )

        return f(*args, **kwargs)

    return decorated_function
