"""Controller responsável por Relatórios Estatísticos e Categorias."""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import (
    calculate_percentage,
    DEFAULT_COLOR,
    is_valid_color,
    sanitize_string,
)

logger = logging.getLogger(__name__)


class ReportController:
    """Implementa a consolidação analítica e operações de categorias."""

    @staticmethod
    def summary_report() -> Tuple[Dict[str, Any], int]:
        """Gera relatório executivo consolidado com prevenção de N+1."""
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
            Task.due_date < now_naive,
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

        seven_days_ago_naive = now_naive - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago_naive).count()
        recent_done = Task.query.filter(
            Task.status == "done", Task.updated_at >= seven_days_ago_naive
        ).count()

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
                    "completion_rate": calculate_percentage(completed, total),
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

        return report, 200

    @staticmethod
    def user_report(user_id: int) -> Tuple[Dict[str, Any], int]:
        """Gera relatório de desempenho de um usuário individual."""
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

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
                "completion_rate": calculate_percentage(done, total),
            },
        }

        return report, 200

    @staticmethod
    def get_categories() -> Tuple[List[Dict[str, Any]], int]:
        """Lista todas as categorias com contagem eager de tarefas."""
        categories = Category.query.options(joinedload(Category.tasks)).all()
        result = []
        for c in categories:
            cat_data = c.to_dict()
            cat_data["task_count"] = len(c.tasks)
            result.append(cat_data)
        return result, 200

    @staticmethod
    def create_category(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Cria uma nova categoria validando nome e cor hexadecimal."""
        if not data or not sanitize_string(data.get("name")):
            return {"error": "Nome é obrigatório"}, 400

        color = sanitize_string(str(data.get("color", DEFAULT_COLOR))) or DEFAULT_COLOR
        if not is_valid_color(color):
            return {"error": "Cor inválida. Use formato hexadecimal #RRGGBB"}, 400

        category = Category()
        category.name = sanitize_string(str(data["name"])) or ""
        category.description = sanitize_string(str(data.get("description", ""))) or ""
        category.color = color

        try:
            db.session.add(category)
            db.session.commit()
            return category.to_dict(), 201
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao criar categoria: %s", exc, exc_info=True)
            return {"error": "Erro ao criar categoria"}, 500

    @staticmethod
    def update_category(cat_id: int, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Atualiza os dados de uma categoria existente."""
        cat = db.session.get(Category, cat_id)
        if not cat:
            return {"error": "Categoria não encontrada"}, 404

        if not data:
            return {"error": "Dados inválidos"}, 400

        if "name" in data:
            cat.name = sanitize_string(str(data["name"])) or ""
        if "description" in data:
            cat.description = sanitize_string(str(data["description"])) or ""
        if "color" in data:
            color = sanitize_string(str(data["color"])) or ""
            if not is_valid_color(color):
                return {"error": "Cor inválida. Use formato hexadecimal #RRGGBB"}, 400
            cat.color = color

        try:
            db.session.commit()
            return cat.to_dict(), 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao atualizar categoria %s: %s", cat_id, exc, exc_info=True)
            return {"error": "Erro ao atualizar"}, 500

    @staticmethod
    def delete_category(cat_id: int) -> Tuple[Dict[str, Any], int]:
        """Exclui uma categoria."""
        cat = db.session.get(Category, cat_id)
        if not cat:
            return {"error": "Categoria não encontrada"}, 404

        try:
            db.session.delete(cat)
            db.session.commit()
            return {"message": "Categoria deletada"}, 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao deletar categoria %s: %s", cat_id, exc, exc_info=True)
            return {"error": "Erro ao deletar"}, 500
