"""Suíte E2E Black-Box (100% Real, Zero Mocks) para o Projeto 1: code-smells-project.

Sobe instâncias reais de `python app.py` em subprocessos separados sobre TCP/HTTP reais
e bancos SQLite temporários reais, validando contratos funcionais e cenários Red-Team.
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
import urllib.parse
import urllib.request

PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "code-smells-project")
)
sys.path.insert(0, PROJECT_DIR)
from itsdangerous import URLSafeTimedSerializer  # noqa: E402


ENV_KEYS_TO_STRIP = (
    "ENVIRONMENT",
    "NODE_ENV",
    "SECRET_KEY",
    "FLASK_DEBUG",
    "DATABASE_PATH",
    "DB_PATH",
    "PORT",
)


def _get_free_port() -> int:
    """Aloca uma porta TCP livre em localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _clean_env(**overrides: str) -> dict:
    """Constrói ambiente limpo removendo variáveis de configuração para testar padrões reais."""
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
    """Executa uma requisição HTTP real via urllib e retorna (status_code, json_or_text)."""
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


def _start_real_server(tmp_dir: str, db_name: str, extra_env: dict = None) -> tuple:
    """Sobe `python app.py` em subprocesso real e aguarda readiness em /health."""
    port = _get_free_port()
    db_path = os.path.join(tmp_dir, db_name)
    log_path = os.path.join(tmp_dir, f"{db_name}.log")

    env_overrides = {"DATABASE_PATH": db_path, "PORT": str(port)}
    if extra_env:
        env_overrides.update(extra_env)
    env = _clean_env(**env_overrides)

    log_fh = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=PROJECT_DIR,
        env=env,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
    )

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 15.0
    while time.time() < deadline:
        if proc.poll() is not None:
            log_fh.close()
            with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
                raise RuntimeError(
                    f"Servidor encerrou prematuramente (rc={proc.returncode}):\n{fh.read()}"
                )
        try:
            status, _ = _http_json(base_url, "GET", "/health")
            if status == 200:
                return proc, log_fh, base_url, db_path
        except Exception:
            time.sleep(0.1)

    proc.terminate()
    proc.wait(timeout=5)
    log_fh.close()
    raise RuntimeError(f"Timeout aguardando servidor real em {base_url}")


def _stop_real_server(proc, log_fh) -> None:
    """Encerra o subprocesso do servidor e fecha seu arquivo de log."""
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    if log_fh and not log_fh.closed:
        log_fh.close()


class TestCodeSmellsProjectRealE2E(unittest.TestCase):
    """Testes E2E reais sem mocks nem test_client para o code-smells-project."""

    @classmethod
    def setUpClass(cls):
        """Inicia Servidor A real sem ENVIRONMENT nem SECRET_KEY definidos."""
        cls.tmp_dir = tempfile.mkdtemp(prefix="e2e_code_smells_")
        cls.proc_a, cls.log_a, cls.base_url_a, cls.db_path_a = _start_real_server(
            cls.tmp_dir, "loja_default_env.db"
        )

    @classmethod
    def tearDownClass(cls):
        """Encerra Servidor A e remove diretório temporário."""
        _stop_real_server(cls.proc_a, cls.log_a)
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_01_real_boot_health_and_fail_closed_default(self):
        """Sem ENVIRONMENT definido, servidor real deve assumir 'production' (fail-closed)."""
        status_idx, data_idx = _http_json(self.base_url_a, "GET", "/")
        self.assertEqual(status_idx, 200)
        self.assertIn("endpoints", data_idx)

        status_h, data_h = _http_json(self.base_url_a, "GET", "/health")
        self.assertEqual(status_h, 200)
        self.assertEqual(data_h["status"], "ok")
        self.assertEqual(data_h["database"], "connected")
        self.assertEqual(data_h["ambiente"], "production")
        self.assertNotIn("secret_key", data_h)
        self.assertNotIn("db_path", data_h)

    def test_02_produtos_crud_and_type_validation(self):
        """Valida CRUD completo de produtos, validações numéricas e rejeição de booleanos."""
        status, data = _http_json(self.base_url_a, "GET", "/produtos")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(data["dados"]), 10)

        status_b, data_b = _http_json(self.base_url_a, "GET", "/produtos/busca?q=Gamer")
        self.assertEqual(status_b, 200)
        self.assertGreater(len(data_b["dados"]), 0)

        # Query param numérico inválido deve retornar 400 (não 500)
        status_bad_q, data_bad_q = _http_json(
            self.base_url_a, "GET", "/produtos/busca?preco_min=invalido"
        )
        self.assertEqual(status_bad_q, 400)
        self.assertFalse(data_bad_q["sucesso"])

        # Booleano disfarçado de número/inteiro deve retornar 400
        status_bool_p, _ = _http_json(
            self.base_url_a,
            "POST",
            "/produtos",
            {"nome": "Prod Bool", "preco": True, "estoque": 5, "categoria": "geral"},
        )
        self.assertEqual(status_bool_p, 400)

        # Criação válida
        status_c, data_c = _http_json(
            self.base_url_a,
            "POST",
            "/produtos",
            {
                "nome": "Mousepad RGB Extra Grande",
                "descricao": "Mousepad gamer antiderrapante",
                "preco": 129.90,
                "estoque": 45,
                "categoria": "informatica",
            },
        )
        self.assertEqual(status_c, 201)
        pid = data_c["dados"]["id"]

        # Categoria inválida no PUT deve retornar 400
        status_put_bad, _ = _http_json(
            self.base_url_a,
            "PUT",
            f"/produtos/{pid}",
            {
                "nome": "Mousepad RGB XXL",
                "preco": 149.90,
                "estoque": 40,
                "categoria": "categoria-inexistente",
            },
        )
        self.assertEqual(status_put_bad, 400)

        # Atualização válida
        status_put, _ = _http_json(
            self.base_url_a,
            "PUT",
            f"/produtos/{pid}",
            {
                "nome": "Mousepad RGB XXL",
                "descricao": "Mousepad gamer antiderrapante premium",
                "preco": 149.90,
                "estoque": 40,
                "categoria": "informatica",
            },
        )
        self.assertEqual(status_put, 200)

        status_get, data_get = _http_json(self.base_url_a, "GET", f"/produtos/{pid}")
        self.assertEqual(status_get, 200)
        self.assertEqual(data_get["dados"]["nome"], "Mousepad RGB XXL")

        # Deleção
        status_del, _ = _http_json(self.base_url_a, "DELETE", f"/produtos/{pid}")
        self.assertEqual(status_del, 200)

        status_404, _ = _http_json(self.base_url_a, "GET", f"/produtos/{pid}")
        self.assertEqual(status_404, 404)

    def test_03_usuarios_mass_assignment_and_unset_env_block(self):
        """Red-Team: cadastro público tentando tipo='admin' + admin real sem ENVIRONMENT."""
        status_u, data_u = _http_json(self.base_url_a, "GET", "/usuarios")
        self.assertEqual(status_u, 200)
        for u in data_u["dados"]:
            self.assertNotIn("senha", u)

        # Tentativa de auto-cadastro como administrador
        status_reg, data_reg = _http_json(
            self.base_url_a,
            "POST",
            "/usuarios",
            {
                "nome": "Atacante Anonimo",
                "email": "atacante@evil.com",
                "senha": "senha-atacante-123",
                "tipo": "admin",
            },
        )
        self.assertEqual(status_reg, 201)
        attacker_id = data_reg["dados"]["id"]

        # Deve estar salvo como 'cliente' e sem expor senha
        status_get, data_get = _http_json(
            self.base_url_a, "GET", f"/usuarios/{attacker_id}"
        )
        self.assertEqual(status_get, 200)
        self.assertEqual(data_get["dados"]["tipo"], "cliente")
        self.assertNotIn("senha", data_get["dados"])

        # Login do atacante -> token de 'cliente', tentativa de reset deve retornar 403
        status_log, data_log = _http_json(
            self.base_url_a,
            "POST",
            "/login",
            {"email": "atacante@evil.com", "senha": "senha-atacante-123"},
        )
        self.assertEqual(status_log, 200)
        self.assertEqual(data_log["dados"]["tipo"], "cliente")
        attacker_token = data_log["token"]

        status_rst_atk, _ = _http_json(
            self.base_url_a,
            "POST",
            "/admin/reset-db",
            headers={"Authorization": f"Bearer {attacker_token}"},
        )
        self.assertEqual(status_rst_atk, 403)

        # Login com senha inválida -> 401
        status_bad_log, _ = _http_json(
            self.base_url_a,
            "POST",
            "/login",
            {"email": "atacante@evil.com", "senha": "errada"},
        )
        self.assertEqual(status_bad_log, 401)

        # Admin legítimo em ambiente sem ENVIRONMENT definido DEVE receber 403 (fail-closed)
        status_adm_log, data_adm_log = _http_json(
            self.base_url_a,
            "POST",
            "/login",
            {"email": "admin@loja.com", "senha": "admin123"},
        )
        self.assertEqual(status_adm_log, 200)
        admin_token = data_adm_log["token"]

        status_rst_unset, _ = _http_json(
            self.base_url_a,
            "POST",
            "/admin/reset-db",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        self.assertEqual(status_rst_unset, 403)

        # Confirma que os dados do banco real não foram apagados
        status_prods, data_prods = _http_json(self.base_url_a, "GET", "/produtos")
        self.assertEqual(status_prods, 200)
        self.assertGreaterEqual(len(data_prods["dados"]), 10)

    def test_04_pedidos_relatorios_sqli_and_negative_qty(self):
        """Valida remoção de /admin/query, bloqueio de SQLi, quantidade negativa e fluxo real."""
        # 1. Backdoor /admin/query removido (404)
        status_q, _ = _http_json(
            self.base_url_a, "POST", "/admin/query", {"sql": "SELECT 1"}
        )
        self.assertEqual(status_q, 404)

        # 2. Tentativas reais de SQL Injection
        sqli_param = urllib.parse.quote("' OR '1'='1")
        status_sqli, data_sqli = _http_json(
            self.base_url_a, "GET", f"/produtos/busca?q={sqli_param}"
        )
        self.assertEqual(status_sqli, 200)
        self.assertEqual(data_sqli["dados"], [])

        status_sqli_log, _ = _http_json(
            self.base_url_a,
            "POST",
            "/login",
            {"email": "admin@loja.com' --", "senha": "' OR '1'='1"},
        )
        self.assertEqual(status_sqli_log, 401)

        # 3. Quantidade negativa, zero, booleana e usuario inexistente devem falhar com 400
        _, prod_before = _http_json(self.base_url_a, "GET", "/produtos/1")
        estoque_inicial = prod_before["dados"]["estoque"]

        for bad_qty in (-5, 0, True):
            st_bad, _ = _http_json(
                self.base_url_a,
                "POST",
                "/pedidos",
                {"usuario_id": 1, "itens": [{"produto_id": 1, "quantidade": bad_qty}]},
            )
            self.assertEqual(st_bad, 400)

        st_bad_uid, _ = _http_json(
            self.base_url_a,
            "POST",
            "/pedidos",
            {"usuario_id": 99999, "itens": [{"produto_id": 1, "quantidade": 1}]},
        )
        self.assertEqual(st_bad_uid, 400)

        _, prod_still = _http_json(self.base_url_a, "GET", "/produtos/1")
        self.assertEqual(prod_still["dados"]["estoque"], estoque_inicial)

        # 4. Criação atômica real de pedido, atualização e relatórios
        status_ped, data_ped = _http_json(
            self.base_url_a,
            "POST",
            "/pedidos",
            {"usuario_id": 1, "itens": [{"produto_id": 1, "quantidade": 2}]},
        )
        self.assertEqual(status_ped, 201)
        ped_id = data_ped["dados"]["pedido_id"]

        _, prod_after = _http_json(self.base_url_a, "GET", "/produtos/1")
        self.assertEqual(prod_after["dados"]["estoque"], estoque_inicial - 2)

        status_upeds, data_upeds = _http_json(
            self.base_url_a, "GET", "/pedidos/usuario/1"
        )
        self.assertEqual(status_upeds, 200)
        self.assertGreater(len(data_upeds["dados"]), 0)

        status_allp, data_allp = _http_json(self.base_url_a, "GET", "/pedidos")
        self.assertEqual(status_allp, 200)
        self.assertGreater(len(data_allp["dados"]), 0)

        status_upd, _ = _http_json(
            self.base_url_a,
            "PUT",
            f"/pedidos/{ped_id}/status",
            {"status": "aprovado"},
        )
        self.assertEqual(status_upd, 200)

        status_rel, data_rel = _http_json(self.base_url_a, "GET", "/relatorios/vendas")
        self.assertEqual(status_rel, 200)
        self.assertGreater(data_rel["dados"]["total_pedidos"], 0)
        self.assertGreater(data_rel["dados"]["faturamento_bruto"], 0)

        # 5. Auditoria direta no banco SQLite real: todas as senhas com hash forte
        with sqlite3.connect(self.db_path_a) as conn:
            rows = conn.execute("SELECT email, senha FROM usuarios").fetchall()
            self.assertGreaterEqual(len(rows), 4)
            for _, pwd_hash in rows:
                self.assertTrue(
                    pwd_hash.startswith(("scrypt:", "pbkdf2:")),
                    f"Senha sem hash forte no banco real: {pwd_hash}",
                )

    def test_05_testing_env_red_team_and_authorized_reset(self):
        """Sobe Servidor B real com ENVIRONMENT=testing e executa ataque completo Red-Team."""
        proc_b, log_b, base_url_b, _ = _start_real_server(
            self.tmp_dir, "loja_testing_env.db", {"ENVIRONMENT": "testing"}
        )
        try:
            st_h, data_h = _http_json(base_url_b, "GET", "/health")
            self.assertEqual(st_h, 200)
            self.assertEqual(data_h["ambiente"], "testing")

            # 1. Sem token -> 401
            st_no_auth, _ = _http_json(base_url_b, "POST", "/admin/reset-db")
            self.assertEqual(st_no_auth, 401)

            # 2. Tentativa de forja offline de token com chave antiga estática -> 401
            forged = URLSafeTimedSerializer(
                "dev-secure-secret-key-32-chars-long", salt="auth-token-salt"
            ).dumps({"id": 1, "email": "admin@loja.com", "tipo": "admin"})
            st_forged, _ = _http_json(
                base_url_b,
                "POST",
                "/admin/reset-db",
                headers={"Authorization": f"Bearer {forged}"},
            )
            self.assertEqual(st_forged, 401)

            # 3. Exploit completo em ENVIRONMENT=testing: auto-cadastro tipo='admin' -> login -> reset
            st_reg, _ = _http_json(
                base_url_b,
                "POST",
                "/usuarios",
                {
                    "nome": "Invasor Testing",
                    "email": "invasor@evil.com",
                    "senha": "invasor123",
                    "tipo": "admin",
                },
            )
            self.assertEqual(st_reg, 201)

            st_log_inv, data_log_inv = _http_json(
                base_url_b,
                "POST",
                "/login",
                {"email": "invasor@evil.com", "senha": "invasor123"},
            )
            self.assertEqual(st_log_inv, 200)
            self.assertEqual(data_log_inv["dados"]["tipo"], "cliente")

            st_rst_inv, _ = _http_json(
                base_url_b,
                "POST",
                "/admin/reset-db",
                headers={"Authorization": f"Bearer {data_log_inv['token']}"},
            )
            self.assertEqual(st_rst_inv, 403)

            # 4. Admin legítimo em ENVIRONMENT=testing -> 200 OK e banco efetivamente zerado
            st_log_adm, data_log_adm = _http_json(
                base_url_b,
                "POST",
                "/login",
                {"email": "admin@loja.com", "senha": "admin123"},
            )
            self.assertEqual(st_log_adm, 200)
            token_admin = data_log_adm["token"]

            st_rst_ok, data_rst_ok = _http_json(
                base_url_b,
                "POST",
                "/admin/reset-db",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
            self.assertEqual(st_rst_ok, 200)
            self.assertTrue(data_rst_ok["sucesso"])

            _, prods_after = _http_json(base_url_b, "GET", "/produtos")
            _, users_after = _http_json(base_url_b, "GET", "/usuarios")
            self.assertEqual(prods_after["dados"], [])
            self.assertEqual(users_after["dados"], [])

            # 5. Mesmo token admin após usuário ser apagado no reset -> 403 (revalidação no DB!)
            st_recheck, _ = _http_json(
                base_url_b,
                "POST",
                "/admin/reset-db",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
            self.assertEqual(st_recheck, 403)
        finally:
            _stop_real_server(proc_b, log_b)


if __name__ == "__main__":
    unittest.main()
