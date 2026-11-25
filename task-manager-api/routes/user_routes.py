"""Rotas e Blueprint para o gerenciamento de Usuários e Autenticação."""

from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from controllers.user_controller import UserController

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
def get_users() -> Tuple[Response, int]:
    """Lista todos os usuários com carregamento eficiente de contagem de tarefas."""
    data, status = UserController.get_users()
    return jsonify(data), status


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int) -> Tuple[Response, int]:
    """Retorna os dados cadastrais e tarefas de um usuário específico."""
    data, status = UserController.get_user(user_id)
    return jsonify(data), status


@user_bp.route("/users", methods=["POST"])
def create_user() -> Tuple[Response, int]:
    """Valida e cria um novo usuário no sistema."""
    payload = request.get_json(silent=True) or {}
    data, status = UserController.create_user(payload)
    return jsonify(data), status


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id: int) -> Tuple[Response, int]:
    """Atualiza dados do usuário."""
    payload = request.get_json(silent=True) or {}
    data, status = UserController.update_user(user_id, payload)
    return jsonify(data), status


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int) -> Tuple[Response, int]:
    """Remove um usuário e exclui suas tarefas associadas."""
    data, status = UserController.delete_user(user_id)
    return jsonify(data), status


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id: int) -> Tuple[Response, int]:
    """Lista as tarefas vinculadas a um usuário."""
    data, status = UserController.get_user_tasks(user_id)
    return jsonify(data), status


@user_bp.route("/login", methods=["POST"])
def login() -> Tuple[Response, int]:
    """Autentica o usuário com email e senha."""
    payload = request.get_json(silent=True) or {}
    data, status = UserController.login(payload)
    return jsonify(data), status
