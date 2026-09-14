from fastapi import APIRouter

from ...models.unidade_medida import UnidadeMedida
from ..schemas.unidade_medida_response import UnidadeMedidaResponse


router = APIRouter(prefix="/unidades-medida", tags=["Catálogos"])


@router.get("", response_model=list[UnidadeMedidaResponse], summary="Listar unidades de medida")
def listar_unidades_medida() -> list[UnidadeMedidaResponse]:
    return [UnidadeMedidaResponse.from_entity(unidade) for unidade in UnidadeMedida]
