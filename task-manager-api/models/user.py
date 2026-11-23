"""Modelo da entidade User (Usuário).

Garante armazenamento seguro de senhas através de PBKDF2/scrypt e previne vazamento de credenciais.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from werkzeug.security import generate_password_hash, check_password_hash
from database import db


class User(db.Model):
    """Representa a entidade de usuário no banco de dados."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serializa o usuário para dicionário, omitindo senhas e hashes confidenciais.

        Returns:
            Dict com informações públicas do usuário.
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def set_password(self, pwd: str) -> None:
        """Criptografa e armazena a senha do usuário com salt seguro.

        Args:
            pwd: Senha em texto plano.
        """
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd: str) -> bool:
        """Verifica se a senha informada corresponde ao hash seguro ou legado armazenado.

        Args:
            pwd: Senha a ser testada.

        Returns:
            bool: True se a senha for autêntica.
        """
        if not self.password:
            return False
        try:
            if check_password_hash(self.password, pwd):
                return True
        except Exception:
            pass

        # Suporte a senhas antigas em texto plano ou MD5 legado com migração transparente
        import hashlib
        legacy_md5 = hashlib.md5(pwd.encode()).hexdigest()
        if self.password == pwd or self.password == legacy_md5:
            # Atualiza para hash seguro
            self.set_password(pwd)
            db.session.commit()
            return True
        return False

    def is_admin(self) -> bool:
        """Verifica se o usuário possui privilégios de administrador.

        Returns:
            bool: True se o papel for 'admin'.
        """
        return self.role == "admin"
