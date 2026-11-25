"""Controller responsável pela gestão e autenticação de Usuários."""

from typing import Tuple
from flask import jsonify, request, Response
from src.models.usuario import UsuarioModel
from src.middlewares.auth_middleware import generate_auth_token


def listar_usuarios() -> Tuple[Response, int]:
    """Retorna lista de todos os usuários."""
    usuarios = UsuarioModel.get_todos()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id: int) -> Tuple[Response, int]:
    """Busca usuário pelo identificador."""
    usuario = UsuarioModel.get_por_id(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario() -> Tuple[Response, int]:
    """Valida e cria um novo usuário."""
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = str(dados.get("nome", "")).strip()
    email = str(dados.get("email", "")).strip()
    senha = str(dados.get("senha", "")).strip()
    tipo = str(dados.get("tipo", "cliente")).strip()

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    try:
        novo_id = UsuarioModel.criar(nome, email, senha, tipo)
        return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            return jsonify({"erro": "Email já cadastrado"}), 400
        raise exc


def login() -> Tuple[Response, int]:
    """Autentica o usuário com email e senha e emite token de acesso assinado."""
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    email = str(dados.get("email", "")).strip()
    senha = str(dados.get("senha", "")).strip()

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = UsuarioModel.autenticar(email, senha)
    if usuario:
        token = generate_auth_token(usuario)
        return (
            jsonify(
                {
                    "dados": usuario,
                    "token": token,
                    "sucesso": True,
                    "mensagem": "Login OK",
                }
            ),
            200,
        )
    return (
        jsonify({"erro": "Email ou senha inválidos", "sucesso": False}),
        401,
    )
