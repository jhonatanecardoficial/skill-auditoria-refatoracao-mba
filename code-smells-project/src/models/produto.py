"""Model para entidade Produto.

Implementa operações de persistência e consultas parametrizadas seguras no SQLite.
"""

from typing import Any, Dict, List, Optional
from src.database.connection import get_db


class ProdutoModel:
    """Repositório e operações de dados para a entidade Produto."""

    @staticmethod
    def get_todos() -> List[Dict[str, Any]]:
        """Retorna todos os produtos cadastrados."""
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM produtos")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_por_id(produto_id: int) -> Optional[Dict[str, Any]]:
        """Busca um produto específico pelo ID com consulta parametrizada.

        Args:
            produto_id: Identificador único do produto.

        Returns:
            Dict com os dados do produto ou None se não encontrado.
        """
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def criar(
        nome: str, descricao: str, preco: float, estoque: int, categoria: str
    ) -> int:
        """Cadastra um novo produto usando query parametrizada.

        Returns:
            int: ID do registro inserido.
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO produtos (nome, descricao, preco, estoque, categoria)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nome, descricao, preco, estoque, categoria),
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def atualizar(
        produto_id: int,
        nome: str,
        descricao: str,
        preco: float,
        estoque: int,
        categoria: str,
    ) -> bool:
        """Atualiza os dados de um produto existente.

        Returns:
            bool: True se atualizado com sucesso.
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            UPDATE produtos
            SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
            WHERE id = ?
            """,
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def deletar(produto_id: int) -> bool:
        """Remove um produto do catálogo pelo ID.

        Returns:
            bool: True se o registro foi removido.
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def buscar(
        termo: str = "",
        categoria: Optional[str] = None,
        preco_min: Optional[float] = None,
        preco_max: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Realiza busca filtrada de produtos de forma segura contra SQL Injection.

        Args:
            termo: Palavra-chave para busca no nome ou descrição.
            categoria: Filtro exato de categoria.
            preco_min: Preço mínimo.
            preco_max: Preço máximo.

        Returns:
            Lista de produtos que atendem aos filtros.
        """
        query = "SELECT * FROM produtos WHERE 1=1"
        params: List[Any] = []

        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            like_term = f"%{termo}%"
            params.extend([like_term, like_term])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            query += " AND preco <= ?"
            params.append(preco_max)

        cursor = get_db().cursor()
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
