from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ...services.tag_service import TagService
from ..dependencies import obter_tag_service
from ..schemas.tag_request import TagRequest
from ..schemas.tag_response import TagResponse

router = APIRouter(prefix="/tags", tags=["Catálogos"])


@router.get("", response_model=list[TagResponse], summary="Sugerir as cinco tags mais utilizadas")
def listar_tags(
    servico: Annotated[TagService, Depends(obter_tag_service)],
    busca: Annotated[str | None, Query(max_length=100, description="Filtra pelo nome a partir de três caracteres.")] = None,
) -> list[TagResponse]:
    return [TagResponse.from_entity(tag) for tag in servico.listar(busca)]


@router.post("", response_model=TagResponse, status_code=201, summary="Criar ou reutilizar tag")
def criar_tag(
    entrada: TagRequest,
    servico: Annotated[TagService, Depends(obter_tag_service)],
) -> TagResponse:
    return TagResponse.from_entity(servico.criar(entrada.nome))
