"""Aplicação Task Manager API refatorada em padrão MVC completo."""

from datetime import datetime, timezone
import os
from typing import Optional, Tuple
from flask import Flask, jsonify, Response
from flask_cors import CORS

from config.settings import Config
from database import db
from middlewares.error_handler import register_error_handlers
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp


def create_app(test_config: Optional[dict] = None) -> Flask:
    """Fábrica de aplicação (Composition Root) para o serviço Task Manager API."""
    app = Flask(__name__)

    # Carrega configurações base
    app.config.from_object(Config)

    # Aplica configurações de teste quando fornecidas
    if test_config:
        app.config.update(test_config)

    # Inicializa extensões globais (CORS parametrizável via CORS_ORIGINS)
    CORS(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    db.init_app(app)

    # Registra rotas (Blueprints desacoplados)
    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    # Registra middleware centralizado de erro
    register_error_handlers(app)

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

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=app.config.get("DEBUG", False), host="0.0.0.0", port=port)
