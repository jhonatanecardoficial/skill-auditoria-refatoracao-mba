"""Shim de compatibilidade para chamadas legadas de models.

Delega chamadas para os novos modelos especializados em src.models.
"""

from src.models.produto import ProdutoModel
from src.models.usuario import UsuarioModel
from src.models.pedido import PedidoModel


def get_todos_produtos():
    return ProdutoModel.get_todos()


def get_produto_por_id(id):
    return ProdutoModel.get_por_id(id)


def criar_produto(nome, descricao, preco, estoque, categoria):
    return ProdutoModel.criar(nome, descricao, preco, estoque, categoria)


def atualizar_produto(id, nome, descricao, preco, estoque, categoria):
    return ProdutoModel.atualizar(id, nome, descricao, preco, estoque, categoria)


def deletar_produto(id):
    return ProdutoModel.deletar(id)


def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    return ProdutoModel.buscar(termo, categoria, preco_min, preco_max)


def get_todos_usuarios():
    return UsuarioModel.get_todos()


def get_usuario_por_id(id):
    return UsuarioModel.get_por_id(id)


def login_usuario(email, senha):
    return UsuarioModel.autenticar(email, senha)


def criar_usuario(nome, email, senha, tipo="cliente"):
    return UsuarioModel.criar(nome, email, senha, tipo)


def criar_pedido(usuario_id, itens):
    return PedidoModel.criar(usuario_id, itens)


def get_pedidos_usuario(usuario_id):
    return PedidoModel.get_por_usuario(usuario_id)


def get_todos_pedidos():
    return PedidoModel.get_todos()


def relatorio_vendas():
    return PedidoModel.relatorio_vendas()


def atualizar_status_pedido(pedido_id, novo_status):
    return PedidoModel.atualizar_status(pedido_id, novo_status)
