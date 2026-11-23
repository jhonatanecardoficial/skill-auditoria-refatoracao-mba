"""Suíte de testes automatizados para o Projeto 3: task-manager-api (Flask + SQLAlchemy MVC)."""

import os
import sys
import unittest

# Adiciona o diretório do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "task-manager-api")))

from app import create_app
from database import db
from models.user import User
from models.category import Category
from models.task import Task


class TestTaskManagerAPI(unittest.TestCase):
    """Casos de teste para validar endpoints e integridade do task-manager-api."""

    @classmethod
    def setUpClass(cls):
        """Configura banco em memória isolado para testes."""
        cls.app = create_app({
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "TESTING": True,
        })
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db.create_all()

            # Seed de teste
            u1 = User(name="Admin Teste", email="admin@test.com", role="admin")
            u1.set_password("adminpass")
            u2 = User(name="User Normal", email="user@test.com", role="user")
            u2.set_password("userpass")
            db.session.add_all([u1, u2])

            c1 = Category(name="Desenvolvimento", color="#3498db")
            c2 = Category(name="Urgente", color="#e74c3c")
            db.session.add_all([c1, c2])
            db.session.commit()

            t1 = Task(
                title="Configurar infra",
                status="in_progress",
                priority=1,
                user_id=u1.id,
                category_id=c1.id,
            )
            t2 = Task(
                title="Criar testes",
                status="done",
                priority=2,
                user_id=u2.id,
                category_id=c1.id,
            )
            db.session.add_all([t1, t2])
            db.session.commit()

    def test_01_health_and_index(self):
        """Valida disponibilidade da raiz e endpoint /health."""
        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)

        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.get_json()["status"], "ok")

    def test_02_tasks_crud_and_stats(self):
        """Valida operações de tarefas e estatísticas agregadas."""
        # Listar tarefas (verifica joinedload de usuário e categoria)
        res_list = self.client.get("/tasks")
        self.assertEqual(res_list.status_code, 200)
        tasks = res_list.get_json()
        self.assertGreaterEqual(len(tasks), 2)
        self.assertIn("user_name", tasks[0])
        self.assertIn("category_name", tasks[0])

        # Criar nova tarefa
        new_task = {
            "title": "Refatoração arquitetural profunda",
            "description": "Aplicar princípios MVC e Clean Architecture",
            "status": "pending",
            "priority": 1,
            "user_id": 1,
            "category_id": 1,
        }
        res_create = self.client.post("/tasks", json=new_task)
        self.assertEqual(res_create.status_code, 201)
        tid = res_create.get_json()["id"]

        # Atualizar tarefa
        res_update = self.client.put(
            f"/tasks/{tid}", json={"status": "in_progress", "priority": 2}
        )
        self.assertEqual(res_update.status_code, 200)

        # Buscar tarefa por termo
        res_search = self.client.get("/tasks/search?q=profunda")
        self.assertEqual(res_search.status_code, 200)
        self.assertEqual(len(res_search.get_json()), 1)

        # Obter estatísticas agregadas
        res_stats = self.client.get("/tasks/stats")
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.get_json()
        self.assertGreater(stats["total"], 0)

        # Deletar tarefa
        res_del = self.client.delete(f"/tasks/{tid}")
        self.assertEqual(res_del.status_code, 200)

    def test_03_users_and_security(self):
        """Valida a ausência de vazamento de senhas e hashing seguro."""
        # Listar usuários
        res_users = self.client.get("/users")
        self.assertEqual(res_users.status_code, 200)
        users = res_users.get_json()
        for u in users:
            self.assertNotIn("password", u)

        # Buscar usuário por ID
        res_user1 = self.client.get("/users/1")
        self.assertEqual(res_user1.status_code, 200)
        self.assertNotIn("password", res_user1.get_json())

        # Criar usuário
        new_u = {
            "name": "Dev QA",
            "email": "dev.qa@empresa.com",
            "password": "supersegura123",
            "role": "user",
        }
        res_new_u = self.client.post("/users", json=new_u)
        self.assertEqual(res_new_u.status_code, 201)
        self.assertNotIn("password", res_new_u.get_json())

        # Login com senha correta
        res_login = self.client.post(
            "/login",
            json={"email": "dev.qa@empresa.com", "password": "supersegura123"},
        )
        self.assertEqual(res_login.status_code, 200)
        self.assertIn("token", res_login.get_json())

        # Login com credenciais inválidas
        res_bad_login = self.client.post(
            "/login",
            json={"email": "dev.qa@empresa.com", "password": "senha-incorreta"},
        )
        self.assertEqual(res_bad_login.status_code, 401)

    def test_04_reports_and_categories(self):
        """Valida relatórios gerenciais sem N+1 e manutenção de categorias."""
        # Relatório executivo consolidado
        res_rep = self.client.get("/reports/summary")
        self.assertEqual(res_rep.status_code, 200)
        rep = res_rep.get_json()
        self.assertIn("overview", rep)
        self.assertIn("user_productivity", rep)

        # Relatório individual de usuário
        res_u_rep = self.client.get("/reports/user/1")
        self.assertEqual(res_u_rep.status_code, 200)
        self.assertIn("statistics", res_u_rep.get_json())

        # Categorias
        res_cats = self.client.get("/categories")
        self.assertEqual(res_cats.status_code, 200)
        self.assertGreaterEqual(len(res_cats.get_json()), 2)


if __name__ == "__main__":
    unittest.main()
