"""Gerenciamento de conexões e ciclo de vida do banco SQLite.

Garante conexões seguras por contexto de requisição e inicialização controlada de schema e seeds.
"""

import sqlite3
from typing import Optional
from flask import current_app, g
from werkzeug.security import generate_password_hash

from src.config.settings import settings


def get_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Obtém ou instancia a conexão SQLite no contexto da requisição atual.

    Args:
        db_path: Caminho opcional para o arquivo de banco (padrão via settings).

    Returns:
        sqlite3.Connection: Conexão ativa com row_factory configurada.
    """
    if db_path is None:
        try:
            if current_app:
                db_path = current_app.config.get("DATABASE_PATH", settings.db_path)
        except RuntimeError:
            db_path = settings.db_path

    path = db_path or settings.db_path
    if "db" not in g:
        g.db = sqlite3.connect(path, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        # Habilita suporte a chaves estrangeiras no SQLite
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


def close_db(e: Optional[BaseException] = None) -> None:
    """Encerra a conexão com o banco de dados associada ao contexto atual.

    Args:
        e: Exceção opcional capturada pelo Flask no teardown.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path: Optional[str] = None) -> None:
    """Inicializa as tabelas do banco de dados e dados iniciais caso não existam.

    Args:
        db_path: Caminho do arquivo do banco SQLite.
    """
    path = db_path or settings.db_path
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            total REAL NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE RESTRICT
        )
    """)
    conn.commit()

    # Seed de produtos se vazia
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        produtos_iniciais = [
            ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
            ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
            ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
            ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
            ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
            ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
            ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
            ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
            ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
            ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
        ]
        cursor.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            produtos_iniciais,
        )

        usuarios_iniciais = [
            ("Admin", "admin@loja.com", generate_password_hash("admin123"), "admin"),
            ("João Silva", "joao@email.com", generate_password_hash("123456"), "cliente"),
            ("Maria Santos", "maria@email.com", generate_password_hash("senha123"), "cliente"),
        ]
        cursor.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            usuarios_iniciais,
        )
        conn.commit()

    conn.close()
