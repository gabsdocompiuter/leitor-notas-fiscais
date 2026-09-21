from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ..core.exceptions import ErroConsulta, ErroLeitura, ErroPersistencia
from ..dtos.leitura_nota_dto import LeituraNotaDTO
from ..core.persistence.entity_mapper import EntityMapper
from ..repositories import LeituraNotaRepository, NotaRepository
from .consulta_service import ConsultaService
from .leitura_service import LeituraService
from .qrcode_service import QRCodeService
from .nota_service import NotaService
from .revisao_nota_service import RevisaoNotaService


class LeituraNotaService:
    """Coordena captura, consulta, extração e persistência de uma NFC-e."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        consultar: Callable[[str], bytes] = ConsultaService.consultar_nota,
        revisao_service: RevisaoNotaService | None = None,
    ):
        self.session_factory = session_factory
        self.consultar = consultar
        self._revisao_service = revisao_service
        self._nota_service = NotaService(session_factory)

    def registrar_leitura(self, url: str, chave: str) -> LeituraNotaDTO:
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
                return EntityMapper.leitura(entidade)
        except SQLAlchemyError as erro:
            raise ErroPersistencia(f"Falha ao registrar a leitura: {erro}") from erro

    def ler(self, url: str) -> LeituraNotaDTO:
        chave = QRCodeService.extrair_chave(url)
        leitura = self.registrar_leitura(url, chave)
        if leitura.nota is not None:
            if self._revisao_service is not None:
                self._revisao_service.aplicar_classificacoes_automaticas(chave)
            return self._nota_service.obter_leitura_por_chave(chave) or leitura

        try:
            html = self.consultar(url)
            nota = LeituraService.extrair_nota(html, url)
            self._nota_service.salvar(nota, leitura.id)
            if self._revisao_service is not None:
                self._revisao_service.aplicar_classificacoes_automaticas(chave)
            resultado = self._nota_service.obter_leitura_por_chave(chave)
            if resultado is None:
                raise ErroPersistencia("A leitura salva não pôde ser recuperada.")
            return resultado
        except (ErroConsulta, ErroLeitura, ErroPersistencia) as erro:
            self._nota_service.registrar_erro(leitura.id, str(erro))
            raise
