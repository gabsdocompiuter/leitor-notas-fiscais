from uuid import UUID

from sqlalchemy import text

from ..core.exceptions import Conflito, DadosInvalidos, NaoEncontrado
from ..core.utils import limpar_nome
from ..core.persistence.entity_mapper import EntityMapper
from ..dtos.produto_dto import ProdutoDTO
from ..dtos.restricoes_produto_dto import RestricoesProdutoDTO
from ..entities import ProdutoEntity
from ..enums.unidade_medida import UnidadeMedida
from ..repositories import CategoriaRepository, ProdutoRepository
from .base_service import BaseService


class ProdutoService(BaseService):
    @staticmethod
    def _restricoes(repositorio: ProdutoRepository, produto_id: UUID) -> RestricoesProdutoDTO:
        possui_itens = repositorio.possui_itens(produto_id)
        estrutura_bloqueada = possui_itens or repositorio.possui_associacoes(produto_id)
        return RestricoesProdutoDTO(
            pode_alterar_estrutura=not estrutura_bloqueada,
            pode_excluir=not possui_itens,
            motivo_alteracao_estrutura=(
                "Unidade e modo de quantidade não podem ser alterados porque o produto "
                "possui itens em notas ou associações de classificação automática."
                if estrutura_bloqueada else None
            ),
            motivo_exclusao=(
                "O produto possui itens vinculados a notas e não pode ser excluído."
                if possui_itens else None
            ),
        )

    def obter_restricoes(self, produto_id: UUID) -> RestricoesProdutoDTO:
        with self.session_factory() as session:
            repositorio = ProdutoRepository(session)
            if repositorio.obter(produto_id) is None:
                raise NaoEncontrado("Produto não encontrado.")
            return self._restricoes(repositorio, produto_id)

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
            # Reserva a escrita antes de verificar vínculos, evitando uso concorrente
            # entre a validação e a alteração no SQLite.
            session.execute(text("BEGIN IMMEDIATE"))
            entidade = repositorio.obter(produto_id)
            if entidade is None:
                raise NaoEncontrado("Produto não encontrado.")
            estrutura_alterada = (
                entidade.tratar_apenas_como_unidades != tratar_apenas_como_unidades
                or entidade.contem_variacoes != contem_variacoes
                or entidade.unidade_medida != unidade_medida
            )
            if estrutura_alterada:
                restricoes = self._restricoes(repositorio, produto_id)
                if not restricoes.pode_alterar_estrutura:
                    raise Conflito(restricoes.motivo_alteracao_estrutura)
            if entidade.contem_variacoes and not contem_variacoes and repositorio.possui_variacoes(produto_id):
                raise Conflito("Não é possível desativar variações enquanto houver variações cadastradas.")
            categoria = CategoriaRepository(session).obter(categoria_id)
            if categoria is None:
                raise NaoEncontrado("Categoria não encontrada.")
            duplicado = repositorio.obter_por_identidade(nome, categoria_id)
            if duplicado and duplicado.id != produto_id:
                raise Conflito("Já existe esse produto na categoria informada.")
            if entidade.nao_solicitar_marca and not nao_solicitar_marca:
                repositorio.invalidar_revisoes_sem_marca(produto_id)
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
            session.execute(text("BEGIN IMMEDIATE"))
            repositorio = ProdutoRepository(session)
            entidade = repositorio.obter(produto_id)
            if entidade is None:
                raise NaoEncontrado("Produto não encontrado.")
            restricoes = self._restricoes(repositorio, produto_id)
            if not restricoes.pode_excluir:
                raise Conflito(restricoes.motivo_exclusao)
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
