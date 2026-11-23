"""Rotas e Blueprint para Administração."""

from flask import Blueprint
from src.controllers import admin_controller

admin_bp = Blueprint("admin", __name__)

admin_bp.add_url_rule(
    "/admin/reset-db",
    "reset_database",
    admin_controller.reset_database,
    methods=["POST"],
)
admin_bp.add_url_rule(
    "/admin/query",
    "executar_query",
    admin_controller.executar_query,
    methods=["POST"],
)
