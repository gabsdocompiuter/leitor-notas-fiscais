from pydantic import BaseModel, ConfigDict


class RestricoesProdutoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pode_alterar_estrutura: bool
    pode_excluir: bool
    motivo_alteracao_estrutura: str | None
    motivo_exclusao: str | None
