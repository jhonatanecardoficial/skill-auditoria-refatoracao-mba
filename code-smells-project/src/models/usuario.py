"""Model para entidade Usuário.

Implementa hashing seguro de senhas com Werkzeug e proteção contra SQL Injection.
"""

import hmac
from typing import Any, Dict, List, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from src.database.connection import get_db

TIPOS_VALIDOS = ("cliente", "admin")


class UsuarioModel:
    """Repositório e operações de persistência e autenticação de usuários."""

    @staticmethod
    def get_todos() -> List[Dict[str, Any]]:
        """Retorna todos os usuários cadastrados sem expor senhas."""
        cursor = get_db().cursor()
        cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_por_id(usuario_id: int) -> Optional[Dict[str, Any]]:
        """Busca usuário por ID sem expor o hash da senha.

        Args:
            usuario_id: Identificador único do usuário.

        Returns:
            Dict com os dados públicos do usuário ou None.
        """
        cursor = get_db().cursor()
        cursor.execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
            (usuario_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def criar(nome: str, email: str, senha: str, tipo: str = "cliente") -> int:
        """Cria um novo usuário com senha criptografada de forma segura.

        Args:
            nome: Nome do usuário.
            email: Endereço de email único.
            senha: Senha em texto plano a ser hasheada com salt.
            tipo: Papel do usuário (padrão 'cliente').

        Returns:
            int: ID do novo usuário inserido.
        """
        if tipo not in TIPOS_VALIDOS:
            raise ValueError("Tipo de usuário inválido")
        senha_hash = generate_password_hash(senha)
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO usuarios (nome, email, senha, tipo)
            VALUES (?, ?, ?, ?)
            """,
            (nome, email, senha_hash, tipo),
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def autenticar(email: str, senha: str) -> Optional[Dict[str, Any]]:
        """Autentica o usuário comparando a senha com o hash seguro armazenado.

        Suporta retrocompatibilidade com hashes ou senhas legadas, promovendo migração automática.

        Args:
            email: Email cadastrado.
            senha: Senha informada.

        Returns:
            Dict com dados essenciais do usuário autenticado ou None se inválido.
        """
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            return None

        user_dict = dict(row)
        stored_password = user_dict["senha"]

        is_valid = False
        try:
            is_valid = check_password_hash(stored_password, senha)
        except Exception:
            is_valid = False

        # Fallback exclusivo para senhas de seed pré-existentes em texto plano (migração segura)
        if (
            not is_valid
            and stored_password
            and not stored_password.startswith(("scrypt:", "pbkdf2:"))
            and hmac.compare_digest(stored_password, senha)
        ):
            is_valid = True
            # Atualiza para hash seguro automaticamente
            novo_hash = generate_password_hash(senha)
            cursor.execute(
                "UPDATE usuarios SET senha = ? WHERE id = ?",
                (novo_hash, user_dict["id"]),
            )
            db.commit()

        if is_valid:
            return {
                "id": user_dict["id"],
                "nome": user_dict["nome"],
                "email": user_dict["email"],
                "tipo": user_dict["tipo"],
            }
        return None
