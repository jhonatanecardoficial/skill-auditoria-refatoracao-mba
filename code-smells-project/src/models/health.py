"""Model para diagnósticos de saúde e estatísticas do banco de dados."""

from typing import Dict
from src.database.connection import get_db


class HealthModel:
    """Encapsula queries de conectividade e volumetria do banco de dados."""

    @staticmethod
    def get_stats() -> Dict[str, int]:
        """Executa checagem de conectividade e contagem de entidades.

        Returns:
            Dict com a quantidade de produtos, usuários e pedidos.
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]

        return {
            "produtos": produtos,
            "usuarios": usuarios,
            "pedidos": pedidos,
        }
