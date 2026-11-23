"""Rotas e controladores para o gerenciamento de Usuários e Autenticação."""

import logging
import re
from datetime import datetime, timezone
from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
def get_users() -> Tuple[Response, int]:
    """Lista todos os usuários com carregamento eficiente de contagem de tarefas."""
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
    return jsonify(result), 200


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int) -> Tuple[Response, int]:
    """Retorna os dados cadastrais e tarefas de um usuário específico."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    data = user.to_dict()
    tasks = Task.query.filter_by(user_id=user_id).all()
    data["tasks"] = [t.to_dict() for t in tasks]

    return jsonify(data), 200


@user_bp.route("/users", methods=["POST"])
def create_user() -> Tuple[Response, int]:
    """Valida e cria um novo usuário no sistema."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not name:
        return jsonify({"error": "Nome é obrigatório"}), 400
    if not email:
        return jsonify({"error": "Email é obrigatório"}), 400
    if not password:
        return jsonify({"error": "Senha é obrigatória"}), 400

    if not re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", email):
        return jsonify({"error": "Email inválido"}), 400

    if len(password) < 4:
        return jsonify({"error": "Senha deve ter no mínimo 4 caracteres"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "Email já cadastrado"}), 409

    if role not in ("user", "admin", "manager"):
        return jsonify({"error": "Role inválido"}), 400

    user = User()
    user.name = name.strip()
    user.email = email.strip()
    user.set_password(password)
    user.role = role

    try:
        db.session.add(user)
        db.session.commit()
        logger.info("Usuário criado com sucesso: ID %s", user.id)
        return jsonify(user.to_dict()), 201
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao criar usuário: %s", exc, exc_info=True)
        return jsonify({"error": "Erro ao criar usuário"}), 500


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id: int) -> Tuple[Response, int]:
    """Atualiza dados do usuário."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    if "name" in data:
        user.name = str(data["name"]).strip()

    if "email" in data:
        eml = str(data["email"]).strip()
        if not re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", eml):
            return jsonify({"error": "Email inválido"}), 400

        existing = User.query.filter_by(email=eml).first()
        if existing and existing.id != user_id:
            return jsonify({"error": "Email já cadastrado"}), 409
        user.email = eml

    if "password" in data:
        pwd = data["password"]
        if len(pwd) < 4:
            return jsonify({"error": "Senha muito curta"}), 400
        user.set_password(pwd)

    if "role" in data:
        r = data["role"]
        if r not in ("user", "admin", "manager"):
            return jsonify({"error": "Role inválido"}), 400
        user.role = r

    if "active" in data:
        user.active = bool(data["active"])

    try:
        db.session.commit()
        return jsonify(user.to_dict()), 200
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao atualizar usuário %s: %s", user_id, exc, exc_info=True)
        return jsonify({"error": "Erro ao atualizar"}), 500


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int) -> Tuple[Response, int]:
    """Remove um usuário e exclui suas tarefas associadas."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    for t in tasks:
        db.session.delete(t)

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Usuário deletado com sucesso"}), 200
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao deletar usuário %s: %s", user_id, exc, exc_info=True)
        return jsonify({"error": "Erro ao deletar"}), 500


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id: int) -> Tuple[Response, int]:
    """Lista as tarefas vinculadas a um usuário."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

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

    return jsonify(result), 200


@user_bp.route("/login", methods=["POST"])
def login() -> Tuple[Response, int]:
    """Autentica o usuário com email e senha."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciais inválidas"}), 401

    if not user.active:
        return jsonify({"error": "Usuário inativo"}), 403

    return (
        jsonify(
            {
                "message": "Login realizado com sucesso",
                "user": user.to_dict(),
                "token": f"jwt-token-{user.id}",
            }
        ),
        200,
    )
