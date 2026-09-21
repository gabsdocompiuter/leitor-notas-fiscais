from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from ..core.exceptions import Conflito, DadosInvalidos, NaoEncontrado
from ..core.utils import normalizar_nome
from ..dtos.nota_dto import NotaDTO
from ..enums.situacao_nota import SituacaoNota
from ..entities import (
    ApresentacaoProdutoEntity,
    AssociacaoProdutoEntity,
    ItemEntity,
    ProdutoEntity,
    VariacaoProdutoEntity,
)
from ..core.persistence.entity_mapper import EntityMapper
from ..repositories import (
    ApresentacaoProdutoRepository,
    AssociacaoProdutoRepository,
    ItemRepository,
    MarcaRepository,
    NotaRepository,
    ProdutoRepository,
    VariacaoProdutoRepository,
)


class RevisaoNotaService:
    """Regras de revisão; cada operação é uma única transação atômica."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def revisar_item(
        self,
        chave: str,
        item_id: UUID,
        produto_id: UUID,
        marca_id: UUID | None,
        variacao_id: UUID | None,
        quantidade_confirmada: Decimal,
    ) -> NotaDTO:
        if quantidade_confirmada <= 0:
            raise DadosInvalidos("A quantidade confirmada deve ser maior que zero.")
        with self.session_factory.begin() as session:
            notas = NotaRepository(session)
            nota = notas.obter_por_chave(chave)
            if nota is None:
                raise NaoEncontrado("Nota não encontrada.")
            if nota.situacao == SituacaoNota.IMPORTADA:
                raise Conflito("Uma nota importada não pode mais ser alterada.")
            item = ItemRepository(session).obter_na_nota(item_id, nota.id)
            if item is None:
                raise NaoEncontrado("Item não encontrado nessa nota.")

            produto, variacao = self._validar_classificacao(
                session, produto_id, marca_id, variacao_id, quantidade_confirmada
            )
            apresentacoes = ApresentacaoProdutoRepository(session)
            apresentacao = apresentacoes.obter_por_produto_marca(produto_id, marca_id)
            if apresentacao is None:
                apresentacao = apresentacoes.adicionar(
                    ApresentacaoProdutoEntity(
                        produto=produto,
                        marca=(MarcaRepository(session).obter(marca_id) if marca_id else None),
                    )
                )

            item.apresentacao = apresentacao
            item.variacao = variacao
            item.quantidade_confirmada = quantidade_confirmada
            item.revisado = True
            nota.situacao = SituacaoNota.EM_REVISAO
            self._salvar_associacao(
                session,
                nota.estabelecimento_id,
                item,
                apresentacao,
                variacao,
                quantidade_confirmada / item.quantidade,
            )
            session.flush()
            session.expire_all()
            return EntityMapper.nota(notas.obter(nota.id) or nota)

    def aplicar_classificacoes_automaticas(self, chave: str) -> NotaDTO:
        with self.session_factory.begin() as session:
            notas = NotaRepository(session)
            nota = notas.obter_por_chave(chave)
            if nota is None:
                raise NaoEncontrado("Nota não encontrada.")
            if nota.situacao == SituacaoNota.IMPORTADA:
                return EntityMapper.nota(nota)

            alterados = 0
            associacoes = AssociacaoProdutoRepository(session)
            for item in ItemRepository(session).listar_pendentes(nota.id):
                associacao = associacoes.obter_por_codigo(
                    nota.estabelecimento_id, item.codigo
                )
                if associacao is None:
                    candidatas = associacoes.listar_por_descricao(
                        normalizar_nome(item.descricao_original)
                    )
                    associacao = candidatas[0] if len(candidatas) == 1 else None
                if associacao is None or not self._associacao_valida(associacao):
                    continue
                quantidade = item.quantidade * associacao.fator_conversao
                produto = associacao.apresentacao.produto
                if (produto.tratar_apenas_como_unidades or produto.contem_variacoes) and (
                    item.quantidade != item.quantidade.to_integral_value()
                    or quantidade != quantidade.to_integral_value()
                ):
                    continue
                item.apresentacao = associacao.apresentacao
                item.variacao = associacao.variacao
                item.quantidade_confirmada = quantidade
                item.revisado = True
                alterados += 1
            if alterados:
                nota.situacao = SituacaoNota.EM_REVISAO
            session.flush()
            session.expire_all()
            return EntityMapper.nota(notas.obter(nota.id) or nota)

    def concluir_importacao(self, chave: str) -> NotaDTO:
        with self.session_factory.begin() as session:
            notas = NotaRepository(session)
            nota = notas.obter_por_chave(chave)
            if nota is None:
                raise NaoEncontrado("Nota não encontrada.")
            if nota.situacao == SituacaoNota.IMPORTADA:
                return EntityMapper.nota(nota)
            incompletos = [item for item in nota.itens if not self._item_completo(item)]
            if not nota.itens or incompletos:
                raise Conflito(
                    f"A nota possui {len(incompletos)} item(ns) que ainda precisam de revisão."
                )
            nota.situacao = SituacaoNota.IMPORTADA
            nota.importada_em = datetime.now(timezone.utc)
            session.flush()
            return EntityMapper.nota(nota)

    @staticmethod
    def _validar_classificacao(
        session: Session,
        produto_id: UUID,
        marca_id: UUID | None,
        variacao_id: UUID | None,
        quantidade: Decimal,
    ) -> tuple[ProdutoEntity, VariacaoProdutoEntity | None]:
        produto = ProdutoRepository(session).obter(produto_id)
        if produto is None:
            raise NaoEncontrado("Produto não encontrado.")
        if not produto.nao_solicitar_marca and marca_id is None:
            raise DadosInvalidos("A marca é obrigatória para o produto selecionado.")
        if marca_id is not None and MarcaRepository(session).obter(marca_id) is None:
            raise NaoEncontrado("Marca não encontrada.")

        variacao = None
        if produto.contem_variacoes:
            if variacao_id is None:
                raise DadosInvalidos("A variação é obrigatória para o produto selecionado.")
            variacao = VariacaoProdutoRepository(session).obter(variacao_id)
            if variacao is None or variacao.produto_id != produto_id:
                raise DadosInvalidos("A variação não pertence ao produto selecionado.")
        elif variacao_id is not None:
            raise DadosInvalidos("O produto selecionado não possui variações.")
        if (produto.tratar_apenas_como_unidades or produto.contem_variacoes) and (
            quantidade != quantidade.to_integral_value()
        ):
            raise DadosInvalidos("A quantidade deve ser um número inteiro para esse produto.")
        return produto, variacao

    @staticmethod
    def _item_completo(item: ItemEntity) -> bool:
        if (
            not item.revisado
            or item.apresentacao is None
            or item.quantidade_confirmada is None
            or item.quantidade_confirmada <= 0
        ):
            return False
        produto = item.apresentacao.produto
        if not produto.nao_solicitar_marca and item.apresentacao.marca is None:
            return False
        if (produto.tratar_apenas_como_unidades or produto.contem_variacoes) and (
            item.quantidade_confirmada != item.quantidade_confirmada.to_integral_value()
        ):
            return False
        if produto.contem_variacoes:
            return item.variacao is not None and item.variacao.produto_id == produto.id
        return item.variacao is None

    @staticmethod
    def _associacao_valida(associacao: AssociacaoProdutoEntity) -> bool:
        produto = associacao.apresentacao.produto
        if not produto.nao_solicitar_marca and associacao.apresentacao.marca_id is None:
            return False
        if produto.contem_variacoes:
            return (
                associacao.variacao is not None
                and associacao.variacao.produto_id == produto.id
            )
        return associacao.variacao is None

    @staticmethod
    def _salvar_associacao(
        session: Session,
        estabelecimento_id: UUID,
        item: ItemEntity,
        apresentacao: ApresentacaoProdutoEntity,
        variacao: VariacaoProdutoEntity | None,
        fator: Decimal,
    ) -> None:
        repositorio = AssociacaoProdutoRepository(session)
        associacao = repositorio.obter_por_codigo(estabelecimento_id, item.codigo)
        if associacao is None:
            associacao = AssociacaoProdutoEntity(
                estabelecimento_id=estabelecimento_id,
                codigo_item=item.codigo,
                descricao_original=item.descricao_original,
                descricao_normalizada=normalizar_nome(item.descricao_original),
                apresentacao=apresentacao,
                variacao=variacao,
                fator_conversao=fator,
            )
            repositorio.adicionar(associacao)
            return
        associacao.descricao_original = item.descricao_original
        associacao.descricao_normalizada = normalizar_nome(item.descricao_original)
        associacao.apresentacao = apresentacao
        associacao.variacao = variacao
        associacao.fator_conversao = fator
