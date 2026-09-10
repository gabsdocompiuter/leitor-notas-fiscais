from fastapi import APIRouter

from ..schemas.health_response import HealthResponse


router = APIRouter(tags=["Sistema"])


@router.get("/health", response_model=HealthResponse, summary="Verificar disponibilidade")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
