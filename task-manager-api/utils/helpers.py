"""Módulo de funções utilitárias e validações do Task Manager API."""

from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)

VALID_STATUSES = ["pending", "in_progress", "done", "cancelled"]
VALID_ROLES = ["user", "admin", "manager"]
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = "#000000"


def format_date(date_obj: Optional[datetime]) -> Optional[str]:
    """Converte um objeto datetime para string ISO."""
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part: float, total: float) -> float:
    """Calcula a porcentagem relativa com proteção contra divisão por zero."""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def validate_email(email: str) -> bool:
    """Verifica se o formato do email informado é válido."""
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", email))


def sanitize_string(s: Optional[str]) -> Optional[str]:
    """Remove espaços em branco no início e final de uma string."""
    if s and isinstance(s, str):
        return s.strip()
    return s


def generate_id() -> str:
    """Gera um identificador universal único (UUID4)."""
    return str(uuid.uuid4())


def log_action(action: str, details: Optional[Any] = None) -> None:
    """Registra uma ação de auditoria usando timezone UTC e logging estruturado."""
    timestamp = datetime.now(timezone.utc)
    logger.info("[%s] ACTION: %s | DETAILS: %s", timestamp, action, details)


def parse_date(date_string: str) -> Optional[datetime]:
    """Faz parsing seguro de strings de data suportando formatos ISO e brasileiro."""
    if not date_string or not isinstance(date_string, str):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def is_valid_color(color: str) -> bool:
    """Valida se uma string é um código hexadecimal de cor válido (#RRGGBB)."""
    if color and isinstance(color, str) and len(color) == 7 and color.startswith("#"):
        return bool(re.match(r"^#[0-9a-fA-F]{6}$", color))
    return False


def process_task_data(data: Dict[str, Any], existing_task: Optional[Any] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Valida e normaliza o payload de entrada de uma tarefa."""
    result: Dict[str, Any] = {}

    if "title" in data:
        title = data["title"]
        if title and isinstance(title, str):
            title = title.strip()
            if MIN_TITLE_LENGTH <= len(title) <= MAX_TITLE_LENGTH:
                result["title"] = title
            else:
                return None, f"Título deve ter entre {MIN_TITLE_LENGTH} e {MAX_TITLE_LENGTH} caracteres"
        else:
            return None, "Título não pode ser vazio"

    if "description" in data:
        result["description"] = data["description"]

    if "status" in data:
        status_val = data["status"]
        if status_val in VALID_STATUSES:
            result["status"] = status_val
        else:
            return None, "Status inválido"

    if "priority" in data:
        try:
            priority_val = int(data["priority"])
            if 1 <= priority_val <= 5:
                result["priority"] = priority_val
            else:
                return None, "Prioridade deve ser entre 1 e 5"
        except (ValueError, TypeError):
            return None, "Prioridade inválida"

    if "due_date" in data:
        due_val = data["due_date"]
        if due_val:
            parsed = parse_date(due_val)
            if parsed:
                result["due_date"] = parsed
            else:
                return None, "Data inválida"
        else:
            result["due_date"] = None

    if "tags" in data:
        tags = data["tags"]
        if isinstance(tags, list):
            result["tags"] = ",".join(str(t) for t in tags)
        elif isinstance(tags, str):
            result["tags"] = tags
        else:
            result["tags"] = str(tags)

    return result, None
