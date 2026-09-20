"""Adaptador temporário para consumidores da interface anterior.

Novos casos de uso devem depender de ``ServicoNotas`` e dos repositories em
``persistence.repositories``. O adaptador não contém SQL nem regras próprias.
"""
from uuid import UUID

from ..models.leitura_nota import LeituraNota
from ..models.nota import Nota
from ..models.situacao_nota import SituacaoNota
from ..services.servico_leitura_notas import ServicoLeituraNotas
from ..services.servico_notas import ServicoNotas
from .banco_sqlite import BancoSQLite


class RepositorioNotas:
    def __init__(self, banco: BancoSQLite):
        self.banco = banco
        self._servico = ServicoNotas(banco.session_factory)
        self._leituras = ServicoLeituraNotas(banco.session_factory)

    def registrar_leitura(self, url: str, chave: str) -> LeituraNota:
        return self._leituras.registrar_leitura(url, chave)

    def registrar_erro(self, leitura_id: UUID, mensagem: str) -> None:
        self._servico.registrar_erro(leitura_id, mensagem)

    def obter_leitura_por_chave(self, chave: str) -> LeituraNota | None:
        return self._servico.obter_leitura_por_chave(chave)

    def obter_por_chave(self, chave: str) -> Nota | None:
        return self._servico.obter_por_chave(chave)

    def listar(
        self, situacao: SituacaoNota | None = None,
        limite: int = 100, deslocamento: int = 0,
    ) -> list[Nota]:
        return self._servico.listar(situacao, limite, deslocamento)

    def salvar(self, nota: Nota, leitura_id: UUID | None = None) -> Nota:
        return self._servico.salvar(nota, leitura_id)
