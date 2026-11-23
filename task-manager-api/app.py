"""Aplicação Task Manager API refatorada."""

import os
from datetime import datetime, timezone
from typing import Tuple
from flask import Flask, jsonify, Response
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from database import db
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp


def create_app(test_config: dict = None) -> Flask:
    """Fábrica de aplicação para o serviço Task Manager API."""
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///tasks.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", "dev-secure-secret-key-task-manager-32-chars"
    )

    if test_config:
        app.config.update(test_config)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    @app.route("/health")
    def health() -> Tuple[Response, int]:
        """Endpoint de verificação de integridade."""
        return (
            jsonify(
                {
                    "status": "ok",
                    "timestamp": str(datetime.now(timezone.utc)),
                }
            ),
            200,
        )

    @app.route("/")
    def index() -> Tuple[Response, int]:
        """Endpoint de apresentação da API."""
        return (
            jsonify({"message": "Task Manager API", "version": "1.0"}),
            200,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException) -> Tuple[Response, int]:
        """Trata exceções HTTP conhecidas."""
        return jsonify({"error": exc.description}), exc.code or 500

    @app.errorhandler(Exception)
    def handle_generic_exception(exc: Exception) -> Tuple[Response, int]:
        """Trata exceções inesperadas com resposta JSON padronizada."""
        return jsonify({"error": str(exc)}), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, host="0.0.0.0", port=port)
