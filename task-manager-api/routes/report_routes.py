"""Rotas e Blueprint de Relatórios Estatísticos e Categorias."""

from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from controllers.report_controller import ReportController

report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
def summary_report() -> Tuple[Response, int]:
    """Gera relatório executivo consolidado com consultas eficientes sem N+1."""
    data, status = ReportController.summary_report()
    return jsonify(data), status


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
def user_report(user_id: int) -> Tuple[Response, int]:
    """Gera relatório de desempenho de um usuário individual."""
    data, status = ReportController.user_report(user_id)
    return jsonify(data), status


@report_bp.route("/categories", methods=["GET"])
def get_categories() -> Tuple[Response, int]:
    """Lista todas as categorias com contagem eager de tarefas."""
    data, status = ReportController.get_categories()
    return jsonify(data), status


@report_bp.route("/categories", methods=["POST"])
def create_category() -> Tuple[Response, int]:
    """Cria uma nova categoria."""
    payload = request.get_json(silent=True) or {}
    data, status = ReportController.create_category(payload)
    return jsonify(data), status


@report_bp.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id: int) -> Tuple[Response, int]:
    """Atualiza os dados de uma categoria existente."""
    payload = request.get_json(silent=True) or {}
    data, status = ReportController.update_category(cat_id, payload)
    return jsonify(data), status


@report_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id: int) -> Tuple[Response, int]:
    """Exclui uma categoria."""
    data, status = ReportController.delete_category(cat_id)
    return jsonify(data), status
