"""Rotas e controladores de Relatórios Estatísticos e Categorias."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)

report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
def summary_report() -> Tuple[Response, int]:
    """Gera relatório executivo consolidado com consultas eficientes."""
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status="pending").count()
    in_progress = Task.query.filter_by(status="in_progress").count()
    done = Task.query.filter_by(status="done").count()
    cancelled = Task.query.filter_by(status="cancelled").count()

    p1 = Task.query.filter_by(priority=1).count()
    p2 = Task.query.filter_by(priority=2).count()
    p3 = Task.query.filter_by(priority=3).count()
    p4 = Task.query.filter_by(priority=4).count()
    p5 = Task.query.filter_by(priority=5).count()

    now = datetime.now(timezone.utc)
    now_naive = now.replace(tzinfo=None)

    overdue_tasks = Task.query.filter(
        Task.due_date.isnot(None),
        Task.due_date < now,
        ~Task.status.in_(("done", "cancelled")),
    ).all()

    overdue_list = [
        {
            "id": t.id,
            "title": t.title,
            "due_date": str(t.due_date),
            "days_overdue": (
                now_naive
                - (
                    t.due_date.replace(tzinfo=None)
                    if t.due_date.tzinfo
                    else t.due_date
                )
            ).days,
        }
        for t in overdue_tasks
    ]

    seven_days_ago = now - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == "done", Task.updated_at >= seven_days_ago
    ).count()

    # Prevenção de N+1 com joinedload dos relacionamentos de tarefas por usuário
    users = User.query.options(joinedload(User.tasks)).all()
    user_stats = []
    for u in users:
        u_tasks = u.tasks
        total = len(u_tasks)
        completed = sum(1 for t in u_tasks if t.status == "done")
        user_stats.append(
            {
                "user_id": u.id,
                "user_name": u.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": round((completed / total) * 100, 2)
                if total > 0
                else 0.0,
            }
        )

    report = {
        "generated_at": str(now),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": {
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "cancelled": cancelled,
        },
        "tasks_by_priority": {
            "critical": p1,
            "high": p2,
            "medium": p3,
            "low": p4,
            "minimal": p5,
        },
        "overdue": {
            "count": len(overdue_list),
            "tasks": overdue_list,
        },
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }

    return jsonify(report), 200


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
def user_report(user_id: int) -> Tuple[Response, int]:
    """Gera relatório de desempenho de um usuário individual."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "done")
    pending = sum(1 for t in tasks if t.status == "pending")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    cancelled = sum(1 for t in tasks if t.status == "cancelled")
    high_priority = sum(1 for t in tasks if t.priority <= 2)

    overdue = 0
    for t in tasks:
        if t.due_date and t.status not in ("done", "cancelled"):
            due = (
                t.due_date.replace(tzinfo=None)
                if t.due_date.tzinfo
                else t.due_date
            )
            if due < now_naive:
                overdue += 1

    report = {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": pending,
            "in_progress": in_progress,
            "cancelled": cancelled,
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": round((done / total) * 100, 2)
            if total > 0
            else 0.0,
        },
    }

    return jsonify(report), 200


@report_bp.route("/categories", methods=["GET"])
def get_categories() -> Tuple[Response, int]:
    """Lista todas as categorias com contagem eager de tarefas (sem N+1)."""
    categories = Category.query.options(joinedload(Category.tasks)).all()
    result = []
    for c in categories:
        cat_data = c.to_dict()
        cat_data["task_count"] = len(c.tasks)
        result.append(cat_data)
    return jsonify(result), 200


@report_bp.route("/categories", methods=["POST"])
def create_category() -> Tuple[Response, int]:
    """Cria uma nova categoria."""
    data = request.get_json(silent=True)
    if not data or not data.get("name"):
        return jsonify({"error": "Nome é obrigatório"}), 400

    category = Category()
    category.name = str(data["name"]).strip()
    category.description = str(data.get("description", "")).strip()
    category.color = str(data.get("color", "#000000")).strip()

    try:
        db.session.add(category)
        db.session.commit()
        return jsonify(category.to_dict()), 201
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao criar categoria: %s", exc, exc_info=True)
        return jsonify({"error": "Erro ao criar categoria"}), 500


@report_bp.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id: int) -> Tuple[Response, int]:
    """Atualiza os dados de uma categoria existente."""
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": "Categoria não encontrada"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    if "name" in data:
        cat.name = str(data["name"]).strip()
    if "description" in data:
        cat.description = str(data["description"]).strip()
    if "color" in data:
        cat.color = str(data["color"]).strip()

    try:
        db.session.commit()
        return jsonify(cat.to_dict()), 200
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao atualizar categoria %s: %s", cat_id, exc, exc_info=True)
        return jsonify({"error": "Erro ao atualizar"}), 500


@report_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id: int) -> Tuple[Response, int]:
    """Exclui uma categoria."""
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": "Categoria não encontrada"}), 404

    try:
        db.session.delete(cat)
        db.session.commit()
        return jsonify({"message": "Categoria deletada"}), 200
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao deletar categoria %s: %s", cat_id, exc, exc_info=True)
        return jsonify({"error": "Erro ao deletar"}), 500
