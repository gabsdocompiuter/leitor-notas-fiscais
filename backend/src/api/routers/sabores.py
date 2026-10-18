from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import exists, select

from ...core.exceptions import Conflito, NaoEncontrado
from ...entities import ItemEntity, NotaEntity, ProdutoEntity, SaborProdutoEntity
from ...enums.situacao_nota import SituacaoNota
from ...services.produto_service import ProdutoService
from ..dependencies import obter_produto_service
from ..schemas.sabor_produto_response import SaborProdutoResponse as SaborResponse

router = APIRouter(tags=["Catálogos"])
Servico = Annotated[ProdutoService, Depends(obter_produto_service)]


class SaborRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=100)


@router.get("/produtos/{produto_id}/sabores", response_model=list[SaborResponse])
def listar(produto_id: UUID, servico: Servico):
    with servico.session_factory() as session:
        if session.get(ProdutoEntity, produto_id) is None:
            raise NaoEncontrado("Produto não encontrado.")
        return [SaborResponse.model_validate(sabor) for sabor in session.scalars(
            select(SaborProdutoEntity).where(SaborProdutoEntity.produto_id == produto_id)
            .order_by(SaborProdutoEntity.nome)
        )]


@router.post("/produtos/{produto_id}/sabores", response_model=SaborResponse,
             status_code=status.HTTP_201_CREATED)
def criar(produto_id: UUID, entrada: SaborRequest, servico: Servico):
    nome = servico.nome_obrigatorio(entrada.nome)
    with servico.session_factory.begin() as session:
        if session.get(ProdutoEntity, produto_id) is None:
            raise NaoEncontrado("Produto não encontrado.")
        sabor = session.scalar(select(SaborProdutoEntity).where(
            SaborProdutoEntity.produto_id == produto_id, SaborProdutoEntity.nome == nome))
        if sabor is None:
            sabor = SaborProdutoEntity(produto_id=produto_id, nome=nome)
            session.add(sabor)
            session.flush()
        return SaborResponse.model_validate(sabor)


@router.patch("/produtos/{produto_id}/sabores/{sabor_id}", response_model=SaborResponse)
def atualizar(produto_id: UUID, sabor_id: UUID, entrada: SaborRequest, servico: Servico):
    nome = servico.nome_obrigatorio(entrada.nome)
    with servico.session_factory.begin() as session:
        sabor = session.get(SaborProdutoEntity, sabor_id)
        if sabor is None or sabor.produto_id != produto_id:
            raise NaoEncontrado("Sabor não encontrado nesse produto.")
        if session.scalar(select(exists().where(
            ItemEntity.sabor_id == sabor_id, ItemEntity.nota_id == NotaEntity.id,
            NotaEntity.situacao == SituacaoNota.IMPORTADA,
        ))):
            raise Conflito("O sabor pertence a uma nota importada e não pode ser alterado.")
        if session.scalar(select(SaborProdutoEntity.id).where(
            SaborProdutoEntity.produto_id == produto_id, SaborProdutoEntity.nome == nome,
            SaborProdutoEntity.id != sabor_id,
        )):
            raise Conflito("Já existe esse sabor para o produto.")
        sabor.nome = nome
        session.flush()
        return SaborResponse.model_validate(sabor)
