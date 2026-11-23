"""Ponto de entrada da aplicação Loja API refatorada em padrão MVC."""

from src.app import create_app
from src.config.settings import settings

app = create_app()

if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO (Arquitetura MVC Refatorada)")
    print(f"Rodando em http://localhost:{settings.port}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=settings.port, debug=settings.debug)
