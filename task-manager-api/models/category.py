"""Modelo da entidade Category (Categoria)."""

from datetime import datetime, timezone
from typing import Any, Dict
from database import db


class Category(db.Model):
    """Representa uma categoria temática para organização de tarefas."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default="#000000")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a categoria para formato de dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": str(self.created_at),
        }
