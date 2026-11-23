"""Rotas e Blueprint para Health Check e Raiz."""

from flask import Blueprint
from src.controllers import health_controller

health_bp = Blueprint("health", __name__)

health_bp.add_url_rule(
    "/health",
    "health_check",
    health_controller.health_check,
    methods=["GET"],
)
health_bp.add_url_rule(
    "/",
    "index",
    health_controller.index,
    methods=["GET"],
)
