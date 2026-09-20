from fastapi import Request

from ..services.servico_catalogo import ServicoCatalogo
from ..services.servico_leitura_notas import ServicoLeituraNotas
from ..services.servico_notas import ServicoNotas
from ..services.servico_revisao_notas import ServicoRevisaoNotas


def obter_servico_notas(request: Request) -> ServicoNotas:
    return request.app.state.servico_notas


def obter_servico_leitura(request: Request) -> ServicoLeituraNotas:
    return request.app.state.servico_leitura_notas


def obter_servico_catalogo(request: Request) -> ServicoCatalogo:
    return request.app.state.servico_catalogo


def obter_servico_revisao(request: Request) -> ServicoRevisaoNotas:
    return request.app.state.servico_revisao_notas
