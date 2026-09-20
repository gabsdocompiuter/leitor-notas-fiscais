from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ..core.exceptions import ErroConsulta, ErroLeitura, ErroPersistencia
from ..models.leitura_nota import LeituraNota
from ..persistence.mappers import leitura_modelo
from ..persistence.repositories import LeituraNotaRepository, NotaRepository
from .consulta import consultar_nota
from .leitura import extrair_nota
from .qrcode import extrair_chave
from .servico_notas import ServicoNotas
from .servico_revisao_notas import ServicoRevisaoNotas


class ServicoLeituraNotas:
    """Coordena captura, consulta, extração e persistência de uma NFC-e."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        consultar: Callable[[str], bytes] = consultar_nota,
        servico_revisao: ServicoRevisaoNotas | None = None,
    ):
        self.session_factory = session_factory
        self.consultar = consultar
        self.servico_revisao = servico_revisao
        self.servico_notas = ServicoNotas(session_factory)

    def registrar_leitura(self, url: str, chave: str) -> LeituraNota:
        try:
            with self.session_factory.begin() as session:
                leituras = LeituraNotaRepository(session)
                entidade = leituras.obter_por_chave(chave)
                if entidade is None:
                    entidade = leituras.adicionar(chave, url, datetime.now(timezone.utc))
                    nota = NotaRepository(session).obter_por_chave(chave)
                    if nota is not None:
                        entidade.nota = nota
                        session.flush()
                return leitura_modelo(entidade)
        except SQLAlchemyError as erro:
            raise ErroPersistencia(f"Falha ao registrar a leitura: {erro}") from erro

    def ler(self, url: str) -> LeituraNota:
        chave = extrair_chave(url)
        leitura = self.registrar_leitura(url, chave)
        if leitura.nota is not None:
            if self.servico_revisao is not None:
                self.servico_revisao.aplicar_classificacoes_automaticas(chave)
            return self.servico_notas.obter_leitura_por_chave(chave) or leitura

        try:
            html = self.consultar(url)
            nota = extrair_nota(html, url)
            self.servico_notas.salvar(nota, leitura.id)
            if self.servico_revisao is not None:
                self.servico_revisao.aplicar_classificacoes_automaticas(chave)
            resultado = self.servico_notas.obter_leitura_por_chave(chave)
            if resultado is None:
                raise ErroPersistencia("A leitura salva não pôde ser recuperada.")
            return resultado
        except (ErroConsulta, ErroLeitura, ErroPersistencia) as erro:
            self.servico_notas.registrar_erro(leitura.id, str(erro))
            raise
