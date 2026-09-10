from fastapi import APIRouter

from ...core.version import __version__
from ..schemas.version_response import VersionResponse


router = APIRouter(tags=["Sistema"])


@router.get("/version", response_model=VersionResponse, summary="Consultar versão")
def obter_versao() -> VersionResponse:
    return VersionResponse(version=__version__)
