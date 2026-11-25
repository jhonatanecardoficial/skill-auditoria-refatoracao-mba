"""Model para entidade Pedido e Itens de Pedido.

Implementa controle transacional atômico, prevenção de N+1 queries e queries parametrizadas.
"""

from typing import Any, Dict, List, Optional
from src.database.connection import get_db

FAIXA_DESCONTO_ALTO = 10000.0
TAXA_DESCONTO_ALTO = 0.10
FAIXA_DESCONTO_MEDIO = 5000.0
TAXA_DESCONTO_MEDIO = 0.05
FAIXA_DESCONTO_BAIXO = 1000.0
TAXA_DESCONTO_BAIXO = 0.02


class PedidoModel:
    """Repositório e operações de negócio/persistência para Pedidos e Itens."""

    @staticmethod
    def criar(usuario_id: int, itens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Cria um pedido e seus itens de forma atômica dentro de uma transação.

        Verifica estoque, calcula o total, insere o pedido e itens e decrementa o estoque.

        Args:
            usuario_id: ID do cliente que realiza o pedido.
            itens: Lista de dicionários contendo 'produto_id' e 'quantidade'.

        Returns:
            Dict com 'pedido_id' e 'total' ou 'erro' em caso de falha de validação.
        """
        db = get_db()
        cursor = db.cursor()

        try:
            total = 0.0
            itens_processados = []

            for item in itens:
                prod_id = item.get("produto_id")
                qtd = item.get("quantidade", 0)

                cursor.execute(
                    "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?",
                    (prod_id,),
                )
                produto = cursor.fetchone()

                if produto is None:
                    return {"erro": f"Produto {prod_id} não encontrado"}
                if produto["estoque"] < qtd:
                    return {"erro": f"Estoque insuficiente para {produto['nome']}"}

                preco_unitario = float(produto["preco"])
                total += preco_unitario * qtd
                itens_processados.append(
                    {
                        "produto_id": prod_id,
                        "quantidade": qtd,
                        "preco_unitario": preco_unitario,
                    }
                )

            # Inserção do pedido
            cursor.execute(
                """
                INSERT INTO pedidos (usuario_id, status, total)
                VALUES (?, 'pendente', ?)
                """,
                (usuario_id, total),
            )
            pedido_id = cursor.lastrowid

            # Inserção dos itens e atualização de estoque
            for item in itens_processados:
                cursor.execute(
                    """
                    INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        pedido_id,
                        item["produto_id"],
                        item["quantidade"],
                        item["preco_unitario"],
                    ),
                )
                cursor.execute(
                    """
                    UPDATE produtos
                    SET estoque = estoque - ?
                    WHERE id = ?
                    """,
                    (item["quantidade"], item["produto_id"]),
                )

            db.commit()
            return {"pedido_id": pedido_id, "total": round(total, 2)}

        except Exception as exc:
            db.rollback()
            raise exc

    @staticmethod
    def get_por_usuario(usuario_id: int) -> List[Dict[str, Any]]:
        """Busca todos os pedidos de um usuário agregando itens sem N+1 queries.

        Args:
            usuario_id: Identificador do usuário.

        Returns:
            Lista de pedidos com os respectivos itens embutidos.
        """
        cursor = get_db().cursor()
        query = """
            SELECT
                p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
                ip.produto_id, COALESCE(pr.nome, 'Desconhecido') AS produto_nome,
                ip.quantidade, ip.preco_unitario
            FROM pedidos p
            LEFT JOIN itens_pedido ip ON p.id = ip.pedido_id
            LEFT JOIN produtos pr ON ip.produto_id = pr.id
            WHERE p.usuario_id = ?
            ORDER BY p.id ASC
        """
        cursor.execute(query, (usuario_id,))
        rows = cursor.fetchall()

        pedidos_map: Dict[int, Dict[str, Any]] = {}
        for r in rows:
            pid = r["pedido_id"]
            if pid not in pedidos_map:
                pedidos_map[pid] = {
                    "id": pid,
                    "usuario_id": r["usuario_id"],
                    "status": r["status"],
                    "total": r["total"],
                    "criado_em": r["criado_em"],
                    "itens": [],
                }
            if r["produto_id"] is not None:
                pedidos_map[pid]["itens"].append(
                    {
                        "produto_id": r["produto_id"],
                        "produto_nome": r["produto_nome"],
                        "quantidade": r["quantidade"],
                        "preco_unitario": r["preco_unitario"],
                    }
                )

        return list(pedidos_map.values())

    @staticmethod
    def get_todos() -> List[Dict[str, Any]]:
        """Retorna todos os pedidos cadastrados no sistema sem gerar N+1 queries."""
        cursor = get_db().cursor()
        query = """
            SELECT
                p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
                ip.produto_id, COALESCE(pr.nome, 'Desconhecido') AS produto_nome,
                ip.quantidade, ip.preco_unitario
            FROM pedidos p
            LEFT JOIN itens_pedido ip ON p.id = ip.pedido_id
            LEFT JOIN produtos pr ON ip.produto_id = pr.id
            ORDER BY p.id ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        pedidos_map: Dict[int, Dict[str, Any]] = {}
        for r in rows:
            pid = r["pedido_id"]
            if pid not in pedidos_map:
                pedidos_map[pid] = {
                    "id": pid,
                    "usuario_id": r["usuario_id"],
                    "status": r["status"],
                    "total": r["total"],
                    "criado_em": r["criado_em"],
                    "itens": [],
                }
            if r["produto_id"] is not None:
                pedidos_map[pid]["itens"].append(
                    {
                        "produto_id": r["produto_id"],
                        "produto_nome": r["produto_nome"],
                        "quantidade": r["quantidade"],
                        "preco_unitario": r["preco_unitario"],
                    }
                )

        return list(pedidos_map.values())

    @staticmethod
    def atualizar_status(pedido_id: int, novo_status: str) -> bool:
        """Atualiza o status de um pedido usando query parametrizada.

        Args:
            pedido_id: ID do pedido.
            novo_status: Novo estado (pendente, aprovado, enviado, etc.).

        Returns:
            bool: True se o status foi alterado.
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (novo_status, pedido_id),
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def relatorio_vendas() -> Dict[str, Any]:
        """Calcula métricas consolidadas de vendas através de agregações SQL eficientes."""
        cursor = get_db().cursor()

        cursor.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(total) FROM pedidos")
        faturamento_row = cursor.fetchone()[0]
        faturamento = float(faturamento_row) if faturamento_row is not None else 0.0

        cursor.execute(
            """
            SELECT
                SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes,
                SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS aprovados,
                SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
            FROM pedidos
            """
        )
        row = cursor.fetchone()
        pendentes = row["pendentes"] or 0
        aprovados = row["aprovados"] or 0
        cancelados = row["cancelados"] or 0

        desconto = 0.0
        if faturamento > FAIXA_DESCONTO_ALTO:
            desconto = faturamento * TAXA_DESCONTO_ALTO
        elif faturamento > FAIXA_DESCONTO_MEDIO:
            desconto = faturamento * TAXA_DESCONTO_MEDIO
        elif faturamento > FAIXA_DESCONTO_BAIXO:
            desconto = faturamento * TAXA_DESCONTO_BAIXO

        ticket_medio = (
            round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0.0
        )

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": pendentes,
            "pedidos_aprovados": aprovados,
            "pedidos_cancelados": cancelados,
            "ticket_medio": ticket_medio,
        }
