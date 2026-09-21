from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ..core.exceptions import ErroPersistencia, NaoEncontrado
from ..dtos.leitura_nota_dto import LeituraNotaDTO
from ..dtos.nota_dto import NotaDTO
from ..enums.situacao_nota import SituacaoNota
from ..core.persistence.entity_mapper import EntityMapper
from ..repositories import LeituraNotaRepository, NotaRepository


class NotaService:
    """Consultas e persistência transacional do agregado de notas."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def obter_por_chave(self, chave: str) -> NotaDTO | None:
        with self.session_factory() as session:
            entidade = NotaRepository(session).obter_por_chave(chave)
            return EntityMapper.nota(entidade) if entidade else None

    def listar(
        self, situacao: SituacaoNota | None = None,
        limite: int = 100, deslocamento: int = 0,
    ) -> list[NotaDTO]:
        with self.session_factory() as session:
            return [
                EntityMapper.nota(item)
                for item in NotaRepository(session).listar(
                    situacao, limite, deslocamento
                )
            ]

    def obter_leitura_por_chave(self, chave: str) -> LeituraNotaDTO | None:
        with self.session_factory() as session:
            entidade = LeituraNotaRepository(session).obter_por_chave(chave)
            return EntityMapper.leitura(entidade) if entidade else None

    def salvar(self, nota: NotaDTO, leitura_id: UUID | None = None) -> NotaDTO:
        try:
            with self.session_factory.begin() as session:
                notas = NotaRepository(session)
                entidade = notas.obter_por_chave(nota.chave)
                if entidade is None:
                    entidade = notas.adicionar_modelo(nota)
                if leitura_id is not None:
                    leitura = LeituraNotaRepository(session).obter(leitura_id)
                    if leitura is None or leitura.chave != nota.chave:
                        raise ErroPersistencia(
                            "A leitura não corresponde à chave da nota."
                        )
                    leitura.nota = entidade
                    leitura.erro_consulta = None
                    session.flush()
                return EntityMapper.nota(entidade)
        except ErroPersistencia:
            raise
        except SQLAlchemyError as erro:
            raise ErroPersistencia(f"Falha ao salvar a nota: {erro}") from erro

    def registrar_erro(self, leitura_id: UUID, mensagem: str) -> None:
        try:
            with self.session_factory.begin() as session:
                leitura = LeituraNotaRepository(session).obter(leitura_id)
                if leitura is not None and leitura.nota_id is None:
                    leitura.erro_consulta = mensagem
        except SQLAlchemyError as erro:
            raise ErroPersistencia(f"Falha ao registrar a consulta: {erro}") from erro
