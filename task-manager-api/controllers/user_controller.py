"""Controller responsável pelo gerenciamento de Usuários e Autenticação."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User
from utils.helpers import (
    MIN_PASSWORD_LENGTH,
    sanitize_string,
    validate_email,
)

logger = logging.getLogger(__name__)


class UserController:
    """Orquestra operações de CRUD de usuários, autenticação e estatísticas individuais."""

    @staticmethod
    def get_users() -> Tuple[List[Dict[str, Any]], int]:
        """Lista usuários com contagem agregada de tarefas sem queries N+1."""
        users = User.query.options(joinedload(User.tasks)).all()
        result = []
        for u in users:
            user_data = {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "active": u.active,
                "created_at": str(u.created_at),
                "task_count": len(u.tasks),
            }
            result.append(user_data)
        return result, 200

    @staticmethod
    def get_user(user_id: int) -> Tuple[Dict[str, Any], int]:
        """Retorna detalhes e tarefas de um usuário."""
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

        data = user.to_dict()
        tasks = Task.query.filter_by(user_id=user_id).all()
        data["tasks"] = [t.to_dict() for t in tasks]
        return data, 200

    @staticmethod
    def create_user(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Valida e persiste novo usuário."""
        if not data:
            return {"error": "Dados inválidos"}, 400

        name = sanitize_string(data.get("name"))
        email = sanitize_string(data.get("email"))
        password = data.get("password")

        if not name:
            return {"error": "Nome é obrigatório"}, 400
        if not email:
            return {"error": "Email é obrigatório"}, 400
        if not password:
            return {"error": "Senha é obrigatória"}, 400

        if not validate_email(email):
            return {"error": "Email inválido"}, 400

        if len(password) < MIN_PASSWORD_LENGTH:
            return {"error": f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres"}, 400

        existing = User.query.filter_by(email=email).first()
        if existing:
            return {"error": "Email já cadastrado"}, 409

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        # Regra de segurança: cadastro público atribui sempre papel padrão 'user'
        user.role = "user"

        try:
            db.session.add(user)
            db.session.commit()
            logger.info("Usuário criado com sucesso: ID %s", user.id)
            return user.to_dict(), 201
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao criar usuário: %s", exc, exc_info=True)
            return {"error": "Erro ao criar usuário"}, 500

    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Atualiza os dados de um usuário existente."""
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

        if not data:
            return {"error": "Dados inválidos"}, 400

        if "name" in data:
            user.name = sanitize_string(str(data["name"])) or ""

        if "email" in data:
            eml = sanitize_string(str(data["email"])) or ""
            if not validate_email(eml):
                return {"error": "Email inválido"}, 400

            existing = User.query.filter_by(email=eml).first()
            if existing and existing.id != user_id:
                return {"error": "Email já cadastrado"}, 409
            user.email = eml

        if "password" in data:
            pwd = data["password"]
            if len(pwd) < MIN_PASSWORD_LENGTH:
                return {"error": "Senha muito curta"}, 400
            user.set_password(pwd)

        if "role" in data and data["role"] != user.role:
            return {"error": "Alteração de papel não permitida neste endpoint"}, 403

        if "active" in data:
            user.active = bool(data["active"])

        try:
            db.session.commit()
            return user.to_dict(), 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao atualizar usuário %s: %s", user_id, exc, exc_info=True)
            return {"error": "Erro ao atualizar"}, 500

    @staticmethod
    def delete_user(user_id: int) -> Tuple[Dict[str, Any], int]:
        """Remove o usuário e suas tarefas associadas."""
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        for t in tasks:
            db.session.delete(t)

        try:
            db.session.delete(user)
            db.session.commit()
            return {"message": "Usuário deletado com sucesso"}, 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao deletar usuário %s: %s", user_id, exc, exc_info=True)
            return {"error": "Erro ao deletar"}, 500

    @staticmethod
    def get_user_tasks(user_id: int) -> Tuple[Any, int]:
        """Lista todas as tarefas vinculadas a um usuário."""
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        result = []

        for t in tasks:
            task_data = {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "created_at": str(t.created_at),
                "due_date": str(t.due_date) if t.due_date else None,
            }

            if t.due_date:
                due = (
                    t.due_date.replace(tzinfo=None)
                    if t.due_date.tzinfo
                    else t.due_date
                )
                task_data["overdue"] = bool(
                    due < now_naive and t.status not in ("done", "cancelled")
                )
            else:
                task_data["overdue"] = False

            result.append(task_data)

        return result, 200

    @staticmethod
    def login(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Autentica o usuário com credenciais e preserva o contrato de token da API."""
        if not data:
            return {"error": "Dados inválidos"}, 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error": "Email e senha são obrigatórios"}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {"error": "Credenciais inválidas"}, 401

        if not user.active:
            return {"error": "Usuário inativo"}, 403

        return {
            "message": "Login realizado com sucesso",
            "user": user.to_dict(),
            "token": f"fake-jwt-token-{user.id}",
        }, 200
