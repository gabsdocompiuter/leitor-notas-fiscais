from uuid import UUID

from ..core.exceptions import Conflito, DadosInvalidos, NaoEncontrado
from ..core.utils import limpar_nome
from ..core.persistence.entity_mapper import EntityMapper
from ..dtos.produto_dto import ProdutoDTO
from ..entities import ProdutoEntity
from ..enums.unidade_medida import UnidadeMedida
from ..repositories import CategoriaRepository, ProdutoRepository
from .base_service import BaseService


class ProdutoService(BaseService):
    def listar(
        self, busca: str | None = None, categoria_id: UUID | None = None
    ) -> list[ProdutoDTO]:
        with self.session_factory() as session:
            entidades = ProdutoRepository(session).listar(
                limpar_nome(busca) if busca else None, categoria_id
            )
            return [EntityMapper.produto(item) for item in entidades]

    def obter(self, produto_id: UUID) -> ProdutoDTO:
        with self.session_factory() as session:
            entidade = ProdutoRepository(session).obter(produto_id)
            if entidade is None:
                raise NaoEncontrado("Produto não encontrado.")
            return EntityMapper.produto(entidade)

    def criar(
        self,
        nome: str,
        categoria_id: UUID,
        nao_solicitar_marca: bool,
        tratar_apenas_como_unidades: bool,
        contem_variacoes: bool,
        unidade_medida: UnidadeMedida | None,
    ) -> ProdutoDTO:
        self._validar_tipo(
            tratar_apenas_como_unidades, contem_variacoes, unidade_medida
        )
        nome = self.nome_obrigatorio(nome)
        with self.session_factory.begin() as session:
            categoria = CategoriaRepository(session).obter(categoria_id)
            if categoria is None:
                raise NaoEncontrado("Categoria não encontrada.")
            repositorio = ProdutoRepository(session)
            entidade = repositorio.obter_por_identidade(nome, categoria_id)
            if entidade is None:
                entidade = repositorio.adicionar(
                    ProdutoEntity(
                        nome=nome,
                        categoria=categoria,
                        nao_solicitar_marca=nao_solicitar_marca,
                        tratar_apenas_como_unidades=tratar_apenas_como_unidades,
                        contem_variacoes=contem_variacoes,
                        unidade_medida=unidade_medida,
                    )
                )
            return EntityMapper.produto(entidade)

    def atualizar(
        self,
        produto_id: UUID,
        nome: str,
        categoria_id: UUID,
        nao_solicitar_marca: bool,
        tratar_apenas_como_unidades: bool,
        contem_variacoes: bool,
        unidade_medida: UnidadeMedida | None,
    ) -> ProdutoDTO:
        self._validar_tipo(
            tratar_apenas_como_unidades, contem_variacoes, unidade_medida
        )
        nome = self.nome_obrigatorio(nome)
        with self.session_factory.begin() as session:
            repositorio = ProdutoRepository(session)
            entidade = repositorio.obter(produto_id)
            if entidade is None:
                raise NaoEncontrado("Produto não encontrado.")
            if repositorio.esta_em_nota_importada(produto_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            categoria = CategoriaRepository(session).obter(categoria_id)
            if categoria is None:
                raise NaoEncontrado("Categoria não encontrada.")
            duplicado = repositorio.obter_por_identidade(nome, categoria_id)
            if duplicado and duplicado.id != produto_id:
                raise Conflito("Já existe esse produto na categoria e unidade informadas.")
            entidade.nome = nome
            entidade.categoria = categoria
            entidade.nao_solicitar_marca = nao_solicitar_marca
            entidade.tratar_apenas_como_unidades = tratar_apenas_como_unidades
            entidade.contem_variacoes = contem_variacoes
            entidade.unidade_medida = unidade_medida
            session.flush()
            return EntityMapper.produto(entidade)

    def excluir(self, produto_id: UUID) -> None:
        with self.session_factory.begin() as session:
            repositorio = ProdutoRepository(session)
            entidade = repositorio.obter(produto_id)
            if entidade is None:
                raise NaoEncontrado("Produto não encontrado.")
            if repositorio.esta_em_nota_importada(produto_id):
                raise Conflito("O cadastro pertence a uma nota importada e não pode ser alterado.")
            if repositorio.possui_apresentacoes(produto_id):
                raise Conflito("O produto está vinculado a uma apresentação.")
            repositorio.excluir(entidade)

    @staticmethod
    def _validar_tipo(
        tratar_apenas_como_unidades: bool,
        contem_variacoes: bool,
        unidade_medida: UnidadeMedida | None,
    ) -> None:
        if tratar_apenas_como_unidades:
            if contem_variacoes or unidade_medida is not None:
                raise DadosInvalidos(
                    "Produtos tratados como unidades não aceitam variações ou unidade de medida."
                )
        elif unidade_medida is None:
            raise DadosInvalidos("A unidade de medida é obrigatória para este produto.")
