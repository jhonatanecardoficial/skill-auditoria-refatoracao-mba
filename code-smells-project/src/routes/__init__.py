"""Módulo de rotas da aplicação."""

from src.routes.produto_routes import produto_bp
from src.routes.usuario_routes import usuario_bp
from src.routes.pedido_routes import pedido_bp
from src.routes.relatorio_routes import relatorio_bp
from src.routes.health_routes import health_bp
from src.routes.admin_routes import admin_bp

__all__ = [
    "produto_bp",
    "usuario_bp",
    "pedido_bp",
    "relatorio_bp",
    "health_bp",
    "admin_bp",
]
