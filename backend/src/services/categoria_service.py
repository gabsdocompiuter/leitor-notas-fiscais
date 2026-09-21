from uuid import UUID

from ..core.exceptions import Conflito, NaoEncontrado
from ..core.utils import limpar_nome
from ..core.persistence.entity_mapper import EntityMapper
from ..dtos.categoria_dto import CategoriaDTO
from ..entities import CategoriaEntity
from ..repositories import CategoriaRepository
from .base_service import BaseService


class CategoriaService(BaseService):
    def listar(self, busca: str | None = None) -> list[CategoriaDTO]:
        with self.session_factory() as session:
            entidades = CategoriaRepository(session).listar(
                limpar_nome(busca) if busca else None
            )
            return [EntityMapper.categoria(item) for item in entidades]

    def obter(self, categoria_id: UUID) -> CategoriaDTO:
        with self.session_factory() as session:
            entidade = CategoriaRepository(session).obter(categoria_id)
            if entidade is None:
                raise NaoEncontrado("Categoria não encontrada.")
            return EntityMapper.categoria(entidade)

    def criar(self, nome: str) -> CategoriaDTO:
        nome = self.nome_obrigatorio(nome)
        with self.session_factory.begin() as session:
            repositorio = CategoriaRepository(session)
            entidade = repositorio.obter_por_nome(nome)
            if entidade is None:
                entidade = repositorio.adicionar(CategoriaEntity(nome=nome))
            return EntityMapper.categoria(entidade)

    def atualizar(self, categoria_id: UUID, nome: str) -> CategoriaDTO:
        nome = self.nome_obrigatorio(nome)
        with self.session_factory.begin() as session:
            repositorio = CategoriaRepository(session)
            entidade = repositorio.obter(categoria_id)
            if entidade is None:
                raise NaoEncontrado("Categoria não encontrada.")
            if repositorio.esta_em_nota_importada(categoria_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            duplicada = repositorio.obter_por_nome(nome)
            if duplicada and duplicada.id != categoria_id:
                raise Conflito("Já existe uma categoria com esse nome.")
            entidade.nome = nome
            session.flush()
            return EntityMapper.categoria(entidade)

    def excluir(self, categoria_id: UUID) -> None:
        with self.session_factory.begin() as session:
            repositorio = CategoriaRepository(session)
            entidade = repositorio.obter(categoria_id)
            if entidade is None:
                raise NaoEncontrado("Categoria não encontrada.")
            if repositorio.esta_em_nota_importada(categoria_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            if repositorio.possui_produtos(categoria_id):
                raise Conflito("A categoria está vinculada a um produto.")
            repositorio.excluir(entidade)
