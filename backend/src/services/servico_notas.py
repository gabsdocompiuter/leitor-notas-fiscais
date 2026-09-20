from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ..core.exceptions import ErroPersistencia, NaoEncontrado
from ..models.leitura_nota import LeituraNota
from ..models.nota import Nota
from ..models.situacao_nota import SituacaoNota
from ..persistence.mappers import leitura_modelo, nota_modelo
from ..persistence.repositories import LeituraNotaRepository, NotaRepository


class ServicoNotas:
    """Consultas e persistência transacional do agregado de notas."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def obter_por_chave(self, chave: str) -> Nota | None:
        with self.session_factory() as session:
            entidade = NotaRepository(session).obter_por_chave(chave)
            return nota_modelo(entidade) if entidade else None

    def listar(
        self, situacao: SituacaoNota | None = None,
        limite: int = 100, deslocamento: int = 0,
    ) -> list[Nota]:
        with self.session_factory() as session:
            return [
                nota_modelo(item)
                for item in NotaRepository(session).listar(
                    situacao, limite, deslocamento
                )
            ]

    def obter_leitura_por_chave(self, chave: str) -> LeituraNota | None:
        with self.session_factory() as session:
            entidade = LeituraNotaRepository(session).obter_por_chave(chave)
            return leitura_modelo(entidade) if entidade else None

    def salvar(self, nota: Nota, leitura_id: UUID | None = None) -> Nota:
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
                return nota_modelo(entidade)
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
