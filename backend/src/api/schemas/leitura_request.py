from pydantic import BaseModel, Field

from ...core.config import URL_NOTA


class LeituraRequest(BaseModel):
    url: str = Field(
        min_length=1,
        description="Link do QR Code, chave de acesso de 44 dígitos ou link de consulta da SEFAZ RS.",
        examples=[
            URL_NOTA,
            "43261008593122000302650530001850701977539572",
            "https://www.sefaz.rs.gov.br/NFE/NFE-NFC.aspx?chaveNFe=43261008593122000302650530001850701977539572",
        ],
    )
