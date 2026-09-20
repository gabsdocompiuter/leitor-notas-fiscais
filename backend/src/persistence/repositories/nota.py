from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from ...core.exceptions import ErroPersistencia
from ...models.nota import Nota
from ...models.situacao_nota import SituacaoNota
from ..entities import (
    ApresentacaoProdutoEntity,
    CategoriaEntity,
    EstabelecimentoEntity,
    ItemEntity,
    MarcaEntity,
    NotaEntity,
    ProdutoEntity,
    VariacaoProdutoEntity,
)
from .base import Repository


class NotaRepository(Repository[NotaEntity]):
    @staticmethod
    def _opcoes_carregamento() -> tuple[object, ...]:
        apresentacao = joinedload(ItemEntity.apresentacao)
        return (
            joinedload(NotaEntity.estabelecimento),
            selectinload(NotaEntity.itens)
            .options(
                apresentacao.joinedload(ApresentacaoProdutoEntity.produto).joinedload(
                    ProdutoEntity.categoria
                ),
                apresentacao.joinedload(ApresentacaoProdutoEntity.marca),
                joinedload(ItemEntity.variacao)
                .joinedload(VariacaoProdutoEntity.produto)
                .joinedload(ProdutoEntity.categoria),
            ),
        )

    def obter(self, entidade_id: UUID) -> NotaEntity | None:
        return self.session.scalar(
            select(NotaEntity)
            .options(*self._opcoes_carregamento())
            .where(NotaEntity.id == entidade_id)
        )

    def obter_por_chave(self, chave: str) -> NotaEntity | None:
        return self.session.scalar(
            select(NotaEntity)
            .options(*self._opcoes_carregamento())
            .where(NotaEntity.chave == chave)
        )

    def listar(
        self,
        situacao: SituacaoNota | None = None,
        limite: int = 100,
        deslocamento: int = 0,
    ) -> list[NotaEntity]:
        consulta = select(NotaEntity).options(*self._opcoes_carregamento())
        if situacao is not None:
            consulta = consulta.where(NotaEntity.situacao == situacao)
        consulta = consulta.order_by(NotaEntity.emissao.desc(), NotaEntity.id)
        return list(self.session.scalars(consulta.limit(limite).offset(deslocamento)))

    def adicionar_modelo(self, nota: Nota) -> NotaEntity:
        if (
            not nota.itens
            or len(nota.itens) != nota.quantidade_itens
            or sum((item.valor_total for item in nota.itens), Decimal(0)) != nota.valor_total
            or nota.valor_total - nota.desconto != nota.valor_a_pagar
        ):
            raise ErroPersistencia("A nota está incompleta ou seus totais são inconsistentes.")

        estabelecimento = self.session.scalar(
            select(EstabelecimentoEntity).where(
                EstabelecimentoEntity.cnpj == nota.estabelecimento.cnpj
            )
        )
        if estabelecimento is None:
            estabelecimento = EstabelecimentoEntity(
                id=nota.estabelecimento.id,
                cnpj=nota.estabelecimento.cnpj,
                razao_social=nota.estabelecimento.razao_social,
                apelido=nota.estabelecimento.apelido,
            )
            self.session.add(estabelecimento)

        entidade = NotaEntity(
            id=nota.id,
            chave=nota.chave,
            numero=nota.numero,
            serie=nota.serie,
            estabelecimento=estabelecimento,
            emissao=nota.emissao,
            quantidade_itens=nota.quantidade_itens,
            valor_total=nota.valor_total,
            desconto=nota.desconto,
            valor_a_pagar=nota.valor_a_pagar,
            url_origem=nota.url_origem,
            situacao=nota.situacao,
            importada_em=nota.importada_em,
        )
        self.session.add(entidade)
        for item in nota.itens:
            apresentacao = (
                self._obter_ou_adicionar_apresentacao(item.apresentacao)
                if item.apresentacao else None
            )
            variacao = (
                self._obter_ou_adicionar_variacao(item.variacao)
                if item.variacao else None
            )
            entidade.itens.append(
                ItemEntity(
                    id=item.id,
                    numero=item.numero,
                    codigo=item.codigo,
                    descricao_original=item.descricao_original,
                    quantidade=item.quantidade,
                    unidade_original=item.unidade_original,
                    valor_unitario=item.valor_unitario,
                    valor_total=item.valor_total,
                    alertas=item.alertas,
                    apresentacao=apresentacao,
                    variacao=variacao,
                    quantidade_confirmada=item.quantidade_confirmada,
                    revisado=item.revisado,
                )
            )
        self.session.flush()
        return self.obter(entidade.id) or entidade

    def _obter_ou_adicionar_apresentacao(self, modelo) -> ApresentacaoProdutoEntity:
        existente = self.session.get(ApresentacaoProdutoEntity, modelo.id)
        if existente:
            return existente
        produto = self._obter_ou_adicionar_produto(modelo.produto)
        marca = None
        if modelo.marca:
            marca = self.session.get(MarcaEntity, modelo.marca.id)
            if marca is None:
                marca = MarcaEntity(id=modelo.marca.id, nome=modelo.marca.nome)
                self.session.add(marca)
        entidade = ApresentacaoProdutoEntity(
            id=modelo.id, produto=produto, marca=marca
        )
        self.session.add(entidade)
        return entidade

    def _obter_ou_adicionar_produto(self, modelo) -> ProdutoEntity:
        existente = self.session.get(ProdutoEntity, modelo.id)
        if existente:
            return existente
        categoria = self.session.get(CategoriaEntity, modelo.categoria.id)
        if categoria is None:
            categoria = CategoriaEntity(
                id=modelo.categoria.id, nome=modelo.categoria.nome
            )
            self.session.add(categoria)
        produto = ProdutoEntity(
            id=modelo.id,
            nome=modelo.nome,
            categoria=categoria,
            nao_solicitar_marca=modelo.nao_solicitar_marca,
            tratar_apenas_como_unidades=modelo.tratar_apenas_como_unidades,
            contem_variacoes=modelo.contem_variacoes,
            unidade_medida=modelo.unidade_medida,
        )
        self.session.add(produto)
        return produto

    def _obter_ou_adicionar_variacao(self, modelo) -> VariacaoProdutoEntity:
        existente = self.session.get(VariacaoProdutoEntity, modelo.id)
        if existente:
            return existente
        entidade = VariacaoProdutoEntity(
            id=modelo.id,
            produto=self._obter_ou_adicionar_produto(modelo.produto),
            quantidade=modelo.quantidade,
            unidade_medida=modelo.unidade_medida,
            descricao=modelo.descricao,
        )
        self.session.add(entidade)
        return entidade
