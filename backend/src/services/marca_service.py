from uuid import UUID

from ..core.exceptions import Conflito, NaoEncontrado
from ..core.utils import limpar_nome
from ..core.persistence.entity_mapper import EntityMapper
from ..dtos.marca_dto import MarcaDTO
from ..entities import MarcaEntity
from ..repositories import MarcaRepository
from .base_service import BaseService


class MarcaService(BaseService):
    def listar(self, busca: str | None = None) -> list[MarcaDTO]:
        with self.session_factory() as session:
            return [
                EntityMapper.marca(item)
                for item in MarcaRepository(session).listar(
                    limpar_nome(busca) if busca else None
                )
            ]

    def obter(self, marca_id: UUID) -> MarcaDTO:
        with self.session_factory() as session:
            entidade = MarcaRepository(session).obter(marca_id)
            if entidade is None:
                raise NaoEncontrado("Marca não encontrada.")
            return EntityMapper.marca(entidade)

    def criar(self, nome: str) -> MarcaDTO:
        nome = self.nome_obrigatorio(nome)
        with self.session_factory.begin() as session:
            repositorio = MarcaRepository(session)
            entidade = repositorio.obter_por_nome(nome)
            if entidade is None:
                entidade = repositorio.adicionar(MarcaEntity(nome=nome))
            return EntityMapper.marca(entidade)

    def atualizar(self, marca_id: UUID, nome: str) -> MarcaDTO:
        nome = self.nome_obrigatorio(nome)
        with self.session_factory.begin() as session:
            repositorio = MarcaRepository(session)
            entidade = repositorio.obter(marca_id)
            if entidade is None:
                raise NaoEncontrado("Marca não encontrada.")
            if repositorio.esta_em_nota_importada(marca_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            duplicada = repositorio.obter_por_nome(nome)
            if duplicada and duplicada.id != marca_id:
                raise Conflito("Já existe uma marca com esse nome.")
            entidade.nome = nome
            session.flush()
            return EntityMapper.marca(entidade)

    def excluir(self, marca_id: UUID) -> None:
        with self.session_factory.begin() as session:
            repositorio = MarcaRepository(session)
            entidade = repositorio.obter(marca_id)
            if entidade is None:
                raise NaoEncontrado("Marca não encontrada.")
            if repositorio.esta_em_nota_importada(marca_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            if repositorio.possui_apresentacoes(marca_id):
                raise Conflito("A marca está vinculada a uma apresentação.")
            repositorio.excluir(entidade)
