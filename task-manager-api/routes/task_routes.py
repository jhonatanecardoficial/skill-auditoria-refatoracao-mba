"""Rotas e Blueprint para o gerenciamento de Tarefas."""

from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from controllers.task_controller import TaskController

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
def get_tasks() -> Tuple[Response, int]:
    """Retorna todas as tarefas com eager loading de relacionamentos para evitar N+1."""
    data, status = TaskController.get_tasks()
    return jsonify(data), status


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id: int) -> Tuple[Response, int]:
    """Busca os detalhes de uma tarefa específica pelo ID."""
    data, status = TaskController.get_task(task_id)
    return jsonify(data), status


@task_bp.route("/tasks", methods=["POST"])
def create_task() -> Tuple[Response, int]:
    """Valida e cadastra uma nova tarefa."""
    payload = request.get_json(silent=True) or {}
    data, status = TaskController.create_task(payload)
    return jsonify(data), status


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id: int) -> Tuple[Response, int]:
    """Atualiza as informações de uma tarefa existente."""
    payload = request.get_json(silent=True) or {}
    data, status = TaskController.update_task(task_id, payload)
    return jsonify(data), status


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id: int) -> Tuple[Response, int]:
    """Exclui uma tarefa do banco de dados."""
    data, status = TaskController.delete_task(task_id)
    return jsonify(data), status


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks() -> Tuple[Response, int]:
    """Filtra tarefas por termo de busca, status, prioridade ou responsável com validação de tipo."""
    query = request.args.get("q", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")
    user_id = request.args.get("user_id", "")
    data, status_code = TaskController.search_tasks(
        query=query, status=status, priority_str=priority, user_id_str=user_id
    )
    return jsonify(data), status_code


@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats() -> Tuple[Response, int]:
    """Calcula estatísticas agregadas de tarefas."""
    data, status = TaskController.task_stats()
    return jsonify(data), status
