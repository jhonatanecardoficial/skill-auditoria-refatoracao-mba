"""Serviço de envio e registro de notificações de tarefas."""

from datetime import datetime, timezone
import logging
import smtplib
from typing import Any, Dict, List, Optional
from flask import current_app
from config.settings import Config

logger = logging.getLogger(__name__)


class NotificationService:
    """Gerencia despacho de notificações por email e histórico operacional."""

    def __init__(self, email_host: Optional[str] = None, email_port: Optional[int] = None,
                 email_user: Optional[str] = None, email_password: Optional[str] = None):
        self.notifications: List[Dict[str, Any]] = []

        # Carrega credenciais a partir de configurações seguras de ambiente
        self.email_host = email_host or (
            current_app.config.get("SMTP_HOST") if current_app else Config.SMTP_HOST
        )
        self.email_port = email_port or (
            current_app.config.get("SMTP_PORT") if current_app else Config.SMTP_PORT
        )
        self.email_user = email_user or (
            current_app.config.get("SMTP_USER") if current_app else Config.SMTP_USER
        )
        self.email_password = email_password or (
            current_app.config.get("SMTP_PASSWORD") if current_app else Config.SMTP_PASSWORD
        )

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Envia mensagem de email via protocolo SMTP com criptografia TLS."""
        if not self.email_user or not self.email_password:
            logger.warning("Credenciais SMTP não configuradas; envio ignorado para %s", to)
            return False
        try:
            server = smtplib.SMTP(self.email_host, self.email_port, timeout=10)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info("Email enviado com sucesso para %s", to)
            return True
        except Exception as exc:
            logger.warning("Simulação/Falha de envio SMTP para %s: %s", to, exc)
            return False

    def notify_task_assigned(self, user: Any, task: Any) -> None:
        """Notifica o responsável sobre uma nova tarefa atribuída."""
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\n"
            f"Status: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            "type": "task_assigned",
            "user_id": user.id,
            "task_id": task.id,
            "timestamp": datetime.now(timezone.utc),
        })

    def notify_task_overdue(self, user: Any, task: Any) -> None:
        """Notifica o responsável sobre uma tarefa cujo prazo expirou."""
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Recupera a lista de notificações registradas para um usuário."""
        return [n for n in self.notifications if n["user_id"] == user_id]
