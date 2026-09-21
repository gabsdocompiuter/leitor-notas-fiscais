from decimal import Decimal
from uuid import UUID

from ..core.exceptions import Conflito, NaoEncontrado
from ..core.persistence.entity_mapper import EntityMapper
from ..dtos.variacao_produto_dto import VariacaoProdutoDTO
from ..entities import VariacaoProdutoEntity
from ..enums.unidade_medida import UnidadeMedida
from ..repositories import ProdutoRepository, VariacaoProdutoRepository
from .base_service import BaseService


class VariacaoProdutoService(BaseService):
    def listar(self, produto_id: UUID) -> list[VariacaoProdutoDTO]:
        with self.session_factory() as session:
            if ProdutoRepository(session).obter(produto_id) is None:
                raise NaoEncontrado("Produto não encontrado.")
            return [
                EntityMapper.variacao(item)
                for item in VariacaoProdutoRepository(session).listar_por_produto(
                    produto_id
                )
            ]

    def obter(self, variacao_id: UUID) -> VariacaoProdutoDTO:
        with self.session_factory() as session:
            entidade = VariacaoProdutoRepository(session).obter(variacao_id)
            if entidade is None:
                raise NaoEncontrado("Variação não encontrada.")
            return EntityMapper.variacao(entidade)

    def criar(
        self,
        produto_id: UUID,
        quantidade: Decimal,
        unidade_medida: UnidadeMedida,
        descricao: str | None,
    ) -> VariacaoProdutoDTO:
        with self.session_factory.begin() as session:
            produto = ProdutoRepository(session).obter(produto_id)
            if produto is None:
                raise NaoEncontrado("Produto não encontrado.")
            if not produto.contem_variacoes:
                raise Conflito("O produto não está configurado para possuir variações.")
            repositorio = VariacaoProdutoRepository(session)
            entidade = repositorio.obter_por_identidade(
                produto_id, quantidade, unidade_medida
            )
            if entidade is None:
                entidade = repositorio.adicionar(
                    VariacaoProdutoEntity(
                        produto=produto,
                        quantidade=quantidade,
                        unidade_medida=unidade_medida,
                        descricao=self.texto_opcional(descricao),
                    )
                )
            return EntityMapper.variacao(entidade)

    def atualizar(
        self,
        variacao_id: UUID,
        quantidade: Decimal,
        unidade_medida: UnidadeMedida,
        descricao: str | None,
    ) -> VariacaoProdutoDTO:
        with self.session_factory.begin() as session:
            repositorio = VariacaoProdutoRepository(session)
            entidade = repositorio.obter(variacao_id)
            if entidade is None:
                raise NaoEncontrado("Variação não encontrada.")
            if repositorio.esta_em_nota_importada(variacao_id):
                raise Conflito("A variação pertence a uma nota importada e não pode ser alterada.")
            duplicada = repositorio.obter_por_identidade(
                entidade.produto_id, quantidade, unidade_medida
            )
            if duplicada and duplicada.id != variacao_id:
                raise Conflito("Já existe essa variação para o produto.")
            entidade.quantidade = quantidade
            entidade.unidade_medida = unidade_medida
            entidade.descricao = self.texto_opcional(descricao)
            session.flush()
            return EntityMapper.variacao(entidade)
