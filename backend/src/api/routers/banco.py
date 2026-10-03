from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from ...core.config import LIMITE_IMPORTACAO_BANCO
from ...core.persistence.coordenacao_banco import BancoOcupado
from ...services.banco_service import ArquivoMuitoGrande

router = APIRouter(prefix="/banco", tags=["Sistema"])


class ConfiguracaoBancoResponse(BaseModel):
    permitir_importacao: bool


class ImportacaoBancoResponse(BaseModel):
    mensagem: str


@router.get("/configuracao", response_model=ConfiguracaoBancoResponse)
def configuracao(request: Request):
    return ConfiguracaoBancoResponse(permitir_importacao=request.app.state.permitir_importacao_banco)


@router.get("/exportacao", response_class=FileResponse)
def exportar(request: Request):
    servico = request.app.state.banco_service
    caminho = servico.exportar()
    return FileResponse(
        caminho,
        filename=f"notas-{datetime.now():%Y-%m-%d-%H%M%S}.sqlite3",
        media_type="application/vnd.sqlite3",
        background=BackgroundTask(servico.limpar, caminho),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/importacao", response_model=ImportacaoBancoResponse)
def importar(request: Request, arquivo: Annotated[UploadFile, File()]):
    if not request.app.state.permitir_importacao_banco:
        raise HTTPException(403, {"codigo": "importacao_desabilitada", "mensagem": "Importação de banco desabilitada."})
    try:
        if arquivo.size is not None and arquivo.size > LIMITE_IMPORTACAO_BANCO:
            raise ArquivoMuitoGrande()
        request.app.state.banco_service.importar(arquivo.file)
    except ArquivoMuitoGrande:
        raise HTTPException(413, {"codigo": "arquivo_muito_grande", "mensagem": "O arquivo deve ter no máximo 100 MiB."})
    except BancoOcupado as erro:
        raise HTTPException(503, {"codigo": "banco_ocupado", "mensagem": str(erro)})
    finally:
        arquivo.file.close()
    return ImportacaoBancoResponse(mensagem="Banco importado com sucesso. Uma cópia do banco anterior foi guardada no servidor.")
