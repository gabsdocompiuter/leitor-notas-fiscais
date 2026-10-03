from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from ..core.exceptions import DadosInvalidos, NaoEncontrado
from ..core.persistence.entity_mapper import EntityMapper
from ..core.utils import limpar_nome, normalizar_nome
from ..dtos.nota_dto import NotaDTO
from ..dtos.tag_dto import TagDTO
from ..entities.tag_entity import TagEntity
from ..entities.nota_entity import NotaEntity
from ..repositories.nota_repository import NotaRepository
from ..repositories.tag_repository import TagRepository


class TagService:
    """Catálogo reutilizável e marcações independentes da classificação automática."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def listar(self, busca: str | None = None) -> list[TagDTO]:
        filtro = normalizar_nome(busca) if busca else ""
        with self.session_factory() as session:
            return [
                EntityMapper.tag(tag)
                for tag in TagRepository(session).listar(filtro if len(filtro) >= 3 else None)
            ]

    def criar(self, nome: str) -> TagDTO:
        nome = limpar_nome(nome)
        if not nome or len(nome) > 100:
            raise DadosInvalidos("A tag deve ter entre 1 e 100 caracteres.")
        with self.session_factory.begin() as session:
            repositorio = TagRepository(session)
            normalizado = normalizar_nome(nome)
            tag = repositorio.obter_por_nome(normalizado)
            if tag is None:
                tag = repositorio.adicionar(TagEntity(nome=nome, nome_normalizado=normalizado))
            return EntityMapper.tag(tag)

    def definir_no_item(self, chave: str, item_id: UUID, tag_ids: list[UUID]) -> NotaDTO:
        with self.session_factory.begin() as session:
            nota = self._obter_nota(session, chave)
            item = next((item for item in nota.itens if item.id == item_id), None)
            if item is None:
                raise NaoEncontrado("Item não encontrado nessa nota.")
            item.tags = self._validar_tags(session, tag_ids)
            session.flush()
            return EntityMapper.nota(nota)

    def adicionar_em_todos(self, chave: str, tag_ids: list[UUID]) -> NotaDTO:
        with self.session_factory.begin() as session:
            nota = self._obter_nota(session, chave)
            tags = self._validar_tags(session, tag_ids)
            for item in nota.itens:
                existentes = {tag.id for tag in item.tags}
                item.tags.extend(tag for tag in tags if tag.id not in existentes)
            session.flush()
            return EntityMapper.nota(nota)

    @staticmethod
    def _validar_tags(session: Session, ids: list[UUID]) -> list[TagEntity]:
        ids_unicos = set(ids)
        tags = TagRepository(session).obter_varias(ids_unicos)
        if len(tags) != len(ids_unicos):
            raise NaoEncontrado("Uma ou mais tags não foram encontradas.")
        return sorted(tags, key=lambda tag: tag.nome_normalizado)

    @staticmethod
    def _obter_nota(session: Session, chave: str) -> NotaEntity:
        nota = NotaRepository(session).obter_por_chave(chave)
        if nota is None:
            raise NaoEncontrado("Nota não encontrada.")
        return nota
