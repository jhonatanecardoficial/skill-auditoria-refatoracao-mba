"""Suíte E2E Black-Box (100% Real, Zero Mocks) para o Projeto 3: task-manager-api.

Executa `python seed.py` e sobe `python app.py` em subprocessos reais com ambiente limpo
e banco SQLite em disco temporário, testando todos os endpoints via HTTP TCP real.
"""

import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "task-manager-api")
)

ENV_KEYS_TO_STRIP = (
    "ENVIRONMENT",
    "SECRET_KEY",
    "FLASK_DEBUG",
    "SQLALCHEMY_DATABASE_URI",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "PORT",
)


def _get_free_port() -> int:
    """Aloca uma porta TCP livre em localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _clean_env(**overrides: str) -> dict:
    """Constrói ambiente limpo sem variáveis de configuração maquiadas."""
    env = os.environ.copy()
    for key in ENV_KEYS_TO_STRIP:
        env.pop(key, None)
    env.update(overrides)
    return env


def _http_json(
    base_url: str,
    method: str,
    path: str,
    payload: object = None,
    headers: dict = None,
) -> tuple:
    """Executa uma requisição HTTP real e retorna (status_code, json_or_text)."""
    url = f"{base_url}{path}"
    req_headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except ValueError:
                return resp.status, raw
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        try:
            return err.code, json.loads(raw)
        except ValueError:
            return err.code, raw


class TestTaskManagerAPIRealE2E(unittest.TestCase):
    """Testes E2E reais sem mocks nem SQLite em memória para o task-manager-api."""

    @classmethod
    def setUpClass(cls):
        """Popula banco real via `seed.py` e inicia `python app.py` em subprocesso real."""
        cls.tmp_dir = tempfile.mkdtemp(prefix="e2e_task_manager_")
        cls.db_path = os.path.join(cls.tmp_dir, "e2e_tasks.db")
        db_uri = "sqlite:///" + cls.db_path.replace("\\", "/")
        cls.port = _get_free_port()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        env = _clean_env(SQLALCHEMY_DATABASE_URI=db_uri, PORT=str(cls.port))

        # 1. Execução real do seed.py
        seed_res = subprocess.run(
            [sys.executable, "seed.py"],
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        if "Seed concluído com sucesso!" not in seed_res.stdout:
            raise RuntimeError(f"Saída inesperada de seed.py:\n{seed_res.stdout}")

        # 2. Inicialização real do app.py
        cls.log_path = os.path.join(cls.tmp_dir, "server.log")
        cls.log_fh = open(cls.log_path, "w", encoding="utf-8")
        cls.proc = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=PROJECT_DIR,
            env=env,
            stdout=cls.log_fh,
            stderr=subprocess.STDOUT,
        )

        deadline = time.time() + 15.0
        while time.time() < deadline:
            if cls.proc.poll() is not None:
                cls.log_fh.close()
                with open(cls.log_path, "r", encoding="utf-8", errors="replace") as fh:
                    raise RuntimeError(f"Servidor encerrou cedo:\n{fh.read()}")
            try:
                status, _ = _http_json(cls.base_url, "GET", "/health")
                if status == 200:
                    return
            except Exception:
                time.sleep(0.1)

        raise RuntimeError("Timeout aguardando Task Manager API real")

    @classmethod
    def tearDownClass(cls):
        """Encerra subprocesso e remove banco temporário."""
        if cls.proc and cls.proc.poll() is None:
            cls.proc.terminate()
            try:
                cls.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.proc.kill()
                cls.proc.wait(timeout=5)
        if cls.log_fh and not cls.log_fh.closed:
            cls.log_fh.close()
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_01_health_and_index(self):
        """Valida endpoints / e /health no servidor real."""
        st_root, data_root = _http_json(self.base_url, "GET", "/")
        self.assertEqual(st_root, 200)
        self.assertEqual(data_root["message"], "Task Manager API")

        st_health, data_health = _http_json(self.base_url, "GET", "/health")
        self.assertEqual(st_health, 200)
        self.assertEqual(data_health["status"], "ok")

    def test_02_tasks_crud_search_and_stats(self):
        """Valida CRUD de tarefas carregadas pelo seed real, busca e validações."""
        st_list, tasks = _http_json(self.base_url, "GET", "/tasks")
        self.assertEqual(st_list, 200)
        self.assertGreaterEqual(len(tasks), 10)
        self.assertIn("user_name", tasks[0])
        self.assertIn("category_name", tasks[0])

        # Booleano disfarçado de prioridade -> 400
        st_bool, _ = _http_json(
            self.base_url,
            "POST",
            "/tasks",
            {"title": "Teste Booleano", "priority": True, "user_id": 1, "category_id": 1},
        )
        self.assertEqual(st_bool, 400)

        # Criação real
        st_create, created = _http_json(
            self.base_url,
            "POST",
            "/tasks",
            {
                "title": "Refatoração arquitetural profunda",
                "description": "Aplicar princípios MVC e Clean Architecture",
                "status": "pending",
                "priority": 1,
                "user_id": 1,
                "category_id": 1,
            },
        )
        self.assertEqual(st_create, 201)
        tid = created["id"]

        st_get, fetched = _http_json(self.base_url, "GET", f"/tasks/{tid}")
        self.assertEqual(st_get, 200)
        self.assertEqual(fetched["id"], tid)

        st_upd, _ = _http_json(
            self.base_url,
            "PUT",
            f"/tasks/{tid}",
            {"status": "in_progress", "priority": 2},
        )
        self.assertEqual(st_upd, 200)

        st_search, found = _http_json(
            self.base_url, "GET", "/tasks/search?q=profunda"
        )
        self.assertEqual(st_search, 200)
        self.assertEqual(len(found), 1)

        st_bad_prio, d_prio = _http_json(
            self.base_url, "GET", "/tasks/search?priority=invalido"
        )
        self.assertEqual(st_bad_prio, 400)
        self.assertIn("error", d_prio)

        st_bad_uid, d_uid = _http_json(
            self.base_url, "GET", "/tasks/search?user_id=invalido"
        )
        self.assertEqual(st_bad_uid, 400)
        self.assertIn("error", d_uid)

        st_stats, stats = _http_json(self.base_url, "GET", "/tasks/stats")
        self.assertEqual(st_stats, 200)
        self.assertGreater(stats["total"], 10)

        st_del, _ = _http_json(self.base_url, "DELETE", f"/tasks/{tid}")
        self.assertEqual(st_del, 200)

    def test_03_users_login_and_mass_assignment_defense(self):
        """Red-Team: impede auto-cadastro como admin/manager e remoção de role em PUT."""
        st_users, users = _http_json(self.base_url, "GET", "/users")
        self.assertEqual(st_users, 200)
        self.assertGreaterEqual(len(users), 3)
        for u in users:
            self.assertNotIn("password", u)

        st_u1, u1 = _http_json(self.base_url, "GET", "/users/1")
        self.assertEqual(st_u1, 200)
        self.assertNotIn("password", u1)

        st_utasks, _ = _http_json(self.base_url, "GET", "/users/1/tasks")
        self.assertEqual(st_utasks, 200)

        # Login com usuário real populado pelo seed.py (deve emitir token assinado, nunca fake)
        st_seed_log, d_seed_log = _http_json(
            self.base_url,
            "POST",
            "/login",
            {"email": "joao@email.com", "password": "1234"},
        )
        self.assertEqual(st_seed_log, 200)
        seed_token = d_seed_log["token"]
        self.assertFalse(seed_token.startswith("fake-jwt-token-"))
        self.assertIn(".", seed_token)
        self.assertGreater(len(seed_token), 40)

        # Tentativa de Mass Assignment no cadastro público
        st_create, created_u = _http_json(
            self.base_url,
            "POST",
            "/users",
            {
                "name": "Atacante Task",
                "email": "atacante.task@empresa.com",
                "password": "supersegura123",
                "role": "admin",
            },
        )
        self.assertEqual(st_create, 201)
        self.assertEqual(created_u["role"], "user")
        self.assertNotIn("password", created_u)
        uid = created_u["id"]

        # Tentativa de escalar privilégio via PUT -> 403 Forbidden
        st_esc, _ = _http_json(
            self.base_url, "PUT", f"/users/{uid}", {"role": "admin"}
        )
        self.assertEqual(st_esc, 403)

        st_verify, verified_u = _http_json(self.base_url, "GET", f"/users/{uid}")
        self.assertEqual(st_verify, 200)
        self.assertEqual(verified_u["role"], "user")

        st_log, d_log = _http_json(
            self.base_url,
            "POST",
            "/login",
            {"email": "atacante.task@empresa.com", "password": "supersegura123"},
        )
        self.assertEqual(st_log, 200)
        self.assertIn("token", d_log)
        self.assertFalse(d_log["token"].startswith("fake-jwt-token-"))
        self.assertIn(".", d_log["token"])

        st_bad_log, _ = _http_json(
            self.base_url,
            "POST",
            "/login",
            {"email": "atacante.task@empresa.com", "password": "errada"},
        )
        self.assertEqual(st_bad_log, 401)

        st_del, _ = _http_json(self.base_url, "DELETE", f"/users/{uid}")
        self.assertEqual(st_del, 200)

    def test_04_reports_and_categories_crud(self):
        """Valida relatórios agregados e ciclo completo de categorias no banco real."""
        st_rep, rep = _http_json(self.base_url, "GET", "/reports/summary")
        self.assertEqual(st_rep, 200)
        self.assertIn("overview", rep)
        self.assertIn("user_productivity", rep)

        st_urep, urep = _http_json(self.base_url, "GET", "/reports/user/1")
        self.assertEqual(st_urep, 200)
        self.assertIn("statistics", urep)

        st_cats, cats = _http_json(self.base_url, "GET", "/categories")
        self.assertEqual(st_cats, 200)
        self.assertGreaterEqual(len(cats), 4)

        st_bad_col, _ = _http_json(
            self.base_url,
            "POST",
            "/categories",
            {"name": "Cor Ruim", "color": "vermelho"},
        )
        self.assertEqual(st_bad_col, 400)

        st_new_cat, cat = _http_json(
            self.base_url,
            "POST",
            "/categories",
            {"name": "Segurança", "description": "AppSec", "color": "#112233"},
        )
        self.assertEqual(st_new_cat, 201)
        cid = cat["id"]

        st_upd_cat, _ = _http_json(
            self.base_url, "PUT", f"/categories/{cid}", {"color": "#445566"}
        )
        self.assertEqual(st_upd_cat, 200)

        st_del_cat, _ = _http_json(self.base_url, "DELETE", f"/categories/{cid}")
        self.assertEqual(st_del_cat, 200)

    def test_05_real_db_passwords_and_config_fail_closed(self):
        """Audita hashes reais em disco (zero MD5) e comportamento fail-closed/efêmero de Config."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT email, password FROM users").fetchall()
            self.assertGreaterEqual(len(rows), 3)
            for email, pwd_hash in rows:
                self.assertTrue(
                    pwd_hash.startswith(("scrypt:", "pbkdf2:")),
                    f"Senha sem hash PBKDF2/scrypt para {email}: {pwd_hash}",
                )
                self.assertNotEqual(len(pwd_hash), 32, "Hash MD5 não pode existir no banco")

        script = (
            "import json; "
            "from config.settings import Config; "
            "print(json.dumps({"
            "'env': Config.ENVIRONMENT, "
            "'smtp_pwd': Config.SMTP_PASSWORD, "
            "'secret': Config.SECRET_KEY"
            "}))"
        )
        clean_env = _clean_env()
        out1 = json.loads(
            subprocess.check_output(
                [sys.executable, "-c", script], cwd=PROJECT_DIR, env=clean_env, text=True
            )
        )
        out2 = json.loads(
            subprocess.check_output(
                [sys.executable, "-c", script], cwd=PROJECT_DIR, env=clean_env, text=True
            )
        )
        self.assertEqual(out1["env"], "production")
        self.assertEqual(out1["smtp_pwd"], "")
        self.assertEqual(len(out1["secret"]), 64)
        self.assertNotEqual(
            out1["secret"],
            out2["secret"],
            "SECRET_KEY ausente deve gerar chave efêmera única por processo",
        )


if __name__ == "__main__":
    unittest.main()
