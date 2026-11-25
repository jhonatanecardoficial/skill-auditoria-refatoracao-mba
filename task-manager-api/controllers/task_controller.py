"""Controller responsável pela orquestração do ciclo de vida de Tarefas."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)


class TaskController:
    """Implementa a lógica de negócio e manipulação de dados para Tarefas."""

    @staticmethod
    def get_tasks() -> Tuple[List[Dict[str, Any]], int]:
        """Recupera lista de tarefas com eager loading evitando queries N+1."""
        tasks = Task.query.options(
            joinedload(Task.user), joinedload(Task.category)
        ).all()
        result = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        for t in tasks:
            task_data = t.to_dict()
            due = (
                t.due_date.replace(tzinfo=None)
                if t.due_date and t.due_date.tzinfo
                else t.due_date
            )
            task_data["overdue"] = bool(
                due and due < now and t.status not in ("done", "cancelled")
            )
            task_data["user_name"] = t.user.name if t.user else None
            task_data["category_name"] = t.category.name if t.category else None
            result.append(task_data)

        return result, 200

    @staticmethod
    def get_task(task_id: int) -> Tuple[Dict[str, Any], int]:
        """Busca detalhes de uma tarefa por ID."""
        task = db.session.get(Task, task_id)
        if not task:
            return {"error": "Task não encontrada"}, 404

        data = task.to_dict()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        due = (
            task.due_date.replace(tzinfo=None)
            if task.due_date and task.due_date.tzinfo
            else task.due_date
        )
        data["overdue"] = bool(
            due and due < now and task.status not in ("done", "cancelled")
        )
        return data, 200

    @staticmethod
    def create_task(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Valida e cria uma nova tarefa com integridade referencial."""
        if not data:
            return {"error": "Dados inválidos"}, 400

        title = data.get("title")
        if not title:
            return {"error": "Título é obrigatório"}, 400
        if len(title) < 3:
            return {"error": "Título muito curto"}, 400
        if len(title) > 200:
            return {"error": "Título muito longo"}, 400

        description = data.get("description", "")
        status = data.get("status", "pending")
        priority = data.get("priority", 3)
        user_id = data.get("user_id")
        category_id = data.get("category_id")
        due_date = data.get("due_date")
        tags = data.get("tags")

        if status not in ("pending", "in_progress", "done", "cancelled"):
            return {"error": "Status inválido"}, 400
        if not isinstance(priority, int) or priority < 1 or priority > 5:
            return {"error": "Prioridade deve ser entre 1 e 5"}, 400

        if user_id and not db.session.get(User, user_id):
            return {"error": "Usuário não encontrado"}, 404
        if category_id and not db.session.get(Category, category_id):
            return {"error": "Categoria não encontrada"}, 404

        task = Task()
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        if due_date:
            try:
                task.due_date = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                return {"error": "Formato de data inválido. Use YYYY-MM-DD"}, 400

        if tags:
            task.tags = ",".join(tags) if isinstance(tags, list) else tags

        try:
            db.session.add(task)
            db.session.commit()
            logger.info("Task criada com sucesso: ID %s", task.id)
            return task.to_dict(), 201
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao persistir task: %s", exc, exc_info=True)
            return {"error": "Erro ao criar task"}, 500

    @staticmethod
    def update_task(task_id: int, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Atualiza uma tarefa existente."""
        task = db.session.get(Task, task_id)
        if not task:
            return {"error": "Task não encontrada"}, 404

        if not data:
            return {"error": "Dados inválidos"}, 400

        if "title" in data:
            t = data["title"]
            if len(t) < 3:
                return {"error": "Título muito curto"}, 400
            if len(t) > 200:
                return {"error": "Título muito longo"}, 400
            task.title = t

        if "description" in data:
            task.description = data["description"]

        if "status" in data:
            if data["status"] not in ("pending", "in_progress", "done", "cancelled"):
                return {"error": "Status inválido"}, 400
            task.status = data["status"]

        if "priority" in data:
            p = data["priority"]
            if not isinstance(p, int) or p < 1 or p > 5:
                return {"error": "Prioridade deve ser entre 1 e 5"}, 400
            task.priority = p

        if "user_id" in data:
            uid = data["user_id"]
            if uid and not db.session.get(User, uid):
                return {"error": "Usuário não encontrado"}, 404
            task.user_id = uid

        if "category_id" in data:
            cid = data["category_id"]
            if cid and not db.session.get(Category, cid):
                return {"error": "Categoria não encontrada"}, 404
            task.category_id = cid

        if "due_date" in data:
            d = data["due_date"]
            if d:
                try:
                    task.due_date = datetime.strptime(d, "%Y-%m-%d")
                except ValueError:
                    return {"error": "Formato de data inválido"}, 400
            else:
                task.due_date = None

        if "tags" in data:
            tags = data["tags"]
            task.tags = ",".join(tags) if isinstance(tags, list) else tags

        task.updated_at = datetime.now(timezone.utc)

        try:
            db.session.commit()
            return task.to_dict(), 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao atualizar task %s: %s", task_id, exc, exc_info=True)
            return {"error": "Erro ao atualizar"}, 500

    @staticmethod
    def delete_task(task_id: int) -> Tuple[Dict[str, Any], int]:
        """Remove uma tarefa do banco de dados."""
        task = db.session.get(Task, task_id)
        if not task:
            return {"error": "Task não encontrada"}, 404

        try:
            db.session.delete(task)
            db.session.commit()
            return {"message": "Task deletada com sucesso"}, 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao deletar task %s: %s", task_id, exc, exc_info=True)
            return {"error": "Erro ao deletar"}, 500

    @staticmethod
    def search_tasks(query: str = "", status: str = "", priority_str: str = "", user_id_str: str = "") -> Tuple[List[Dict[str, Any]], int]:
        """Filtra tarefas com validação robusta de tipos nos parâmetros."""
        tasks_query = Task.query

        if query:
            tasks_query = tasks_query.filter(
                db.or_(
                    Task.title.like(f"%{query}%"),
                    Task.description.like(f"%{query}%"),
                )
            )

        if status:
            tasks_query = tasks_query.filter(Task.status == status)

        if priority_str:
            try:
                priority = int(priority_str)
                tasks_query = tasks_query.filter(Task.priority == priority)
            except (ValueError, TypeError):
                return {"error": "Priority must be an integer"}, 400

        if user_id_str:
            try:
                user_id = int(user_id_str)
                tasks_query = tasks_query.filter(Task.user_id == user_id)
            except (ValueError, TypeError):
                return {"error": "User_id must be an integer"}, 400

        results = tasks_query.all()
        return [t.to_dict() for t in results], 200

    @staticmethod
    def task_stats() -> Tuple[Dict[str, Any], int]:
        """Calcula estatísticas agregadas de tarefas no banco."""
        total = Task.query.count()
        pending = Task.query.filter_by(status="pending").count()
        in_progress = Task.query.filter_by(status="in_progress").count()
        done = Task.query.filter_by(status="done").count()
        cancelled = Task.query.filter_by(status="cancelled").count()

        now = datetime.now(timezone.utc)
        overdue_count = Task.query.filter(
            Task.due_date.isnot(None),
            Task.due_date < now,
            ~Task.status.in_(("done", "cancelled")),
        ).count()

        completion_rate = round((done / total) * 100, 2) if total > 0 else 0.0

        stats = {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "cancelled": cancelled,
            "overdue": overdue_count,
            "completion_rate": completion_rate,
        }

        return stats, 200
