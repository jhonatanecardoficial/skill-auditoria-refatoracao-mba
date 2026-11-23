"""Suíte de testes automatizados para o Projeto 1: code-smells-project (Flask MVC)."""

import sys
import os
import unittest

# Adiciona o diretório do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code-smells-project")))

from src.app import create_app
from src.database.connection import init_db


class TestCodeSmellsProject(unittest.TestCase):
    """Casos de teste para validar endpoints e integridade do code-smells-project."""

    @classmethod
    def setUpClass(cls):
        """Configura banco temporário isolado para testes."""
        cls.test_db = "test_loja.db"
        cls.app = create_app({"DATABASE_PATH": cls.test_db, "TESTING": True})
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        """Remove o banco de teste temporário."""
        if os.path.exists(cls.test_db):
            try:
                os.remove(cls.test_db)
            except Exception:
                pass

    def test_01_index_and_health(self):
        """Valida se o endpoint raiz e o health check respondem com sucesso."""
        res_index = self.client.get("/")
        self.assertEqual(res_index.status_code, 200)
        self.assertIn("endpoints", res_index.get_json())

        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        json_data = res_health.get_json()
        self.assertEqual(json_data["status"], "ok")
        self.assertEqual(json_data["database"], "connected")
        # Garante que chaves confidenciais não são vazadas no health
        self.assertNotIn("secret_key", json_data)

    def test_02_produtos_crud(self):
        """Testa o ciclo de vida completo de produtos (Listar, Buscar, Criar, Atualizar, Deletar)."""
        # Listar
        res = self.client.get("/produtos")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.get_json()["dados"]), 10)

        # Buscar por termo
        res_busca = self.client.get("/produtos/busca?q=Gamer")
        self.assertEqual(res_busca.status_code, 200)
        self.assertTrue(len(res_busca.get_json()["dados"]) > 0)

        # Criar
        payload = {
            "nome": "Mousepad RGB Extra Grande",
            "descricao": "Mousepad gamer antiderrapante",
            "preco": 129.90,
            "estoque": 45,
            "categoria": "informatica",
        }
        res_create = self.client.post("/produtos", json=payload)
        self.assertEqual(res_create.status_code, 201)
        pid = res_create.get_json()["dados"]["id"]

        # Atualizar
        payload_update = {
            "nome": "Mousepad RGB XXL",
            "descricao": "Mousepad gamer antiderrapante premium",
            "preco": 149.90,
            "estoque": 40,
            "categoria": "informatica",
        }
        res_put = self.client.put(f"/produtos/{pid}", json=payload_update)
        self.assertEqual(res_put.status_code, 200)

        # Buscar por ID
        res_get = self.client.get(f"/produtos/{pid}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.get_json()["dados"]["nome"], "Mousepad RGB XXL")

        # Deletar
        res_del = self.client.delete(f"/produtos/{pid}")
        self.assertEqual(res_del.status_code, 200)

        # Verificar se realmente foi excluído
        res_not_found = self.client.get(f"/produtos/{pid}")
        self.assertEqual(res_not_found.status_code, 404)

    def test_03_usuarios_and_login_security(self):
        """Verifica a gestão de usuários e segurança de credenciais."""
        # Listar usuários e garantir ausência de senhas
        res = self.client.get("/usuarios")
        self.assertEqual(res.status_code, 200)
        for user in res.get_json()["dados"]:
            self.assertNotIn("senha", user)

        # Criar novo usuário
        new_user = {
            "nome": "Carlos Roberto",
            "email": "carlos@empresa.com",
            "senha": "senha-forte-1234",
            "tipo": "cliente",
        }
        res_user = self.client.post("/usuarios", json=new_user)
        self.assertEqual(res_user.status_code, 201)

        # Login com nova senha hasheada
        res_login = self.client.post(
            "/login",
            json={"email": "carlos@empresa.com", "senha": "senha-forte-1234"},
        )
        self.assertEqual(res_login.status_code, 200)
        self.assertEqual(res_login.get_json()["dados"]["nome"], "Carlos Roberto")

        # Login com senha incorreta
        res_bad_login = self.client.post(
            "/login",
            json={"email": "carlos@empresa.com", "senha": "senha-errada"},
        )
        self.assertEqual(res_bad_login.status_code, 401)

        # Login de usuário seed inicial (verificação de retrocompatibilidade)
        res_seed_login = self.client.post(
            "/login",
            json={"email": "admin@loja.com", "senha": "admin123"},
        )
        self.assertEqual(res_seed_login.status_code, 200)

    def test_04_pedidos_and_relatorios(self):
        """Valida criação atômica de pedidos, baixa de estoque e relatórios."""
        # Criar pedido
        pedido_payload = {
            "usuario_id": 1,
            "itens": [{"produto_id": 1, "quantidade": 2}],
        }
        res_ped = self.client.post("/pedidos", json=pedido_payload)
        self.assertEqual(res_ped.status_code, 201)
        ped_id = res_ped.get_json()["dados"]["pedido_id"]

        # Listar pedidos do usuário
        res_user_peds = self.client.get("/pedidos/usuario/1")
        self.assertEqual(res_user_peds.status_code, 200)
        self.assertTrue(len(res_user_peds.get_json()["dados"]) > 0)

        # Atualizar status
        res_status = self.client.put(
            f"/pedidos/{ped_id}/status", json={"status": "aprovado"}
        )
        self.assertEqual(res_status.status_code, 200)

        # Relatório de vendas
        res_rel = self.client.get("/relatorios/vendas")
        self.assertEqual(res_rel.status_code, 200)
        rel_data = res_rel.get_json()["dados"]
        self.assertGreater(rel_data["total_pedidos"], 0)
        self.assertGreater(rel_data["faturamento_bruto"], 0)


if __name__ == "__main__":
    unittest.main()
