"""Model para operações administrativas controladas de banco de dados."""

from src.database.connection import get_db


class AdminModel:
    """Encapsula operações administrativas de manutenção no banco de dados."""

    @staticmethod
    def reset_database() -> None:
        """Remove todos os registros das tabelas de forma atômica e transacional."""
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM itens_pedido")
            cursor.execute("DELETE FROM pedidos")
            cursor.execute("DELETE FROM produtos")
            cursor.execute("DELETE FROM usuarios")
            db.commit()
        except Exception:
            db.rollback()
            raise
