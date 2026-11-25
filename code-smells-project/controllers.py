"""Shim de compatibilidade para controladores legados.

Encaminha chamadas para os controllers modulares em src.controllers.
"""

from src.controllers.produto_controller import (
    listar_produtos,
    buscar_produto,
    criar_produto,
    atualizar_produto,
    deletar_produto,
    buscar_produtos,
)
from src.controllers.usuario_controller import (
    listar_usuarios,
    buscar_usuario,
    criar_usuario,
    login,
)
from src.controllers.pedido_controller import (
    criar_pedido,
    listar_todos_pedidos,
    listar_pedidos_usuario,
    atualizar_status_pedido,
)
from src.controllers.relatorio_controller import relatorio_vendas
from src.controllers.health_controller import health_check, index
from src.controllers.admin_controller import reset_database

__all__ = [
    "listar_produtos",
    "buscar_produto",
    "criar_produto",
    "atualizar_produto",
    "deletar_produto",
    "buscar_produtos",
    "listar_usuarios",
    "buscar_usuario",
    "criar_usuario",
    "login",
    "criar_pedido",
    "listar_todos_pedidos",
    "listar_pedidos_usuario",
    "atualizar_status_pedido",
    "relatorio_vendas",
    "health_check",
    "index",
    "reset_database",
]
