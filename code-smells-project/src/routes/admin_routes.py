"""Rotas e Blueprint para Administração."""

from flask import Blueprint
from src.controllers import admin_controller
from src.middlewares.auth_middleware import require_admin

admin_bp = Blueprint("admin", __name__)

# NOTA DE SEGURANÇA (Fase 3 - Finding Closure Gate):
# O endpoint vulnerável /admin/query (execução arbitrária de SQL) foi completamente
# removido da tabela de rotas. Requisições recebem automaticamente 404 Not Found.
# O endpoint /admin/reset-db é protegido pelo decorator @require_admin (Bearer token + ambiente).

admin_bp.add_url_rule(
    "/admin/reset-db",
    "reset_database",
    require_admin(admin_controller.reset_database),
    methods=["POST"],
)
