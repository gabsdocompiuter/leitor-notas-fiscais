from pydantic import BaseModel, Field

from ...core.config import URL_NOTA


class LeituraRequest(BaseModel):
    url: str = Field(
        min_length=1,
        description="Conteúdo completo lido do QR Code da NFC-e.",
        examples=[URL_NOTA],
    )
