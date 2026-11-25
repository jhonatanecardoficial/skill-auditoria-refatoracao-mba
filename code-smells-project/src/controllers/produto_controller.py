"""Controller responsável pelas regras de requisição e resposta de Produtos."""

from typing import Tuple
from flask import jsonify, request, Response
from src.models.produto import ProdutoModel

CATEGORIAS_VALIDAS = [
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
]

NOME_MIN_LEN = 2
NOME_MAX_LEN = 200


def listar_produtos() -> Tuple[Response, int]:
    """Retorna a listagem de todos os produtos cadastrados."""
    produtos = ProdutoModel.get_todos()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id: int) -> Tuple[Response, int]:
    """Busca um produto específico pelo seu ID."""
    produto = ProdutoModel.get_por_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar_produto() -> Tuple[Response, int]:
    """Valida os dados de entrada e cria um novo produto."""
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            return jsonify({"erro": f"{campo.capitalize()} é obrigatório"}), 400

    nome = str(dados["nome"]).strip()
    descricao = str(dados.get("descricao", "")).strip()
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = str(dados.get("categoria", "geral")).strip()

    if not isinstance(preco, (int, float)) or preco < 0:
        return jsonify({"erro": "Preço não pode ser negativo"}), 400
    if not isinstance(estoque, int) or estoque < 0:
        return jsonify({"erro": "Estoque não pode ser negativo"}), 400
    if len(nome) < 2:
        return jsonify({"erro": "Nome muito curto"}), 400
    if len(nome) > 200:
        return jsonify({"erro": "Nome muito longo"}), 400
    if categoria not in CATEGORIAS_VALIDAS:
        return (
            jsonify({"erro": f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}"}),
            400,
        )

    novo_id = ProdutoModel.criar(nome, descricao, float(preco), estoque, categoria)
    return (
        jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}),
        201,
    )


def atualizar_produto(id: int) -> Tuple[Response, int]:
    """Valida e atualiza os dados de um produto existente."""
    produto_existente = ProdutoModel.get_por_id(id)
    if not produto_existente:
        return jsonify({"erro": "Produto não encontrado"}), 404

    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            return jsonify({"erro": f"{campo.capitalize()} é obrigatório"}), 400

    nome = str(dados["nome"]).strip()
    descricao = str(dados.get("descricao", "")).strip()
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = str(dados.get("categoria", "geral")).strip()

    if len(nome) < NOME_MIN_LEN or len(nome) > NOME_MAX_LEN:
        return (
            jsonify({"erro": f"Nome deve ter entre {NOME_MIN_LEN} e {NOME_MAX_LEN} caracteres"}),
            400,
        )

    if not isinstance(preco, (int, float)) or preco < 0:
        return jsonify({"erro": "Preço não pode ser negativo"}), 400
    if not isinstance(estoque, int) or estoque < 0:
        return jsonify({"erro": "Estoque não pode ser negativo"}), 400

    ProdutoModel.atualizar(id, nome, descricao, float(preco), estoque, categoria)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id: int) -> Tuple[Response, int]:
    """Remove um produto do banco de dados."""
    produto = ProdutoModel.get_por_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404

    ProdutoModel.deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos() -> Tuple[Response, int]:
    """Filtra produtos com parâmetros de query string e validação robusta."""
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min_str = request.args.get("preco_min", None)
    preco_max_str = request.args.get("preco_max", None)

    preco_min = None
    if preco_min_str is not None:
        try:
            preco_min = float(preco_min_str)
        except (ValueError, TypeError):
            return (
                jsonify({"erro": "Parâmetro preco_min deve ser numérico", "sucesso": False}),
                400,
            )

    preco_max = None
    if preco_max_str is not None:
        try:
            preco_max = float(preco_max_str)
        except (ValueError, TypeError):
            return (
                jsonify({"erro": "Parâmetro preco_max deve ser numérico", "sucesso": False}),
                400,
            )

    resultados = ProdutoModel.buscar(
        termo=termo,
        categoria=categoria,
        preco_min=preco_min,
        preco_max=preco_max,
    )
    return (
        jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}),
        200,
    )
