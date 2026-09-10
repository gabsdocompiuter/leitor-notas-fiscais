from fastapi import Request

from ..persistence.repositorio_notas import RepositorioNotas
from ..services.servico_leitura_notas import ServicoLeituraNotas


def obter_repositorio(request: Request) -> RepositorioNotas:
    return request.app.state.repositorio_notas


def obter_servico_leitura(request: Request) -> ServicoLeituraNotas:
    return request.app.state.servico_leitura_notas
