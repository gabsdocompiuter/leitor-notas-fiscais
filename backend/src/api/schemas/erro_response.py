from pydantic import BaseModel


class ErroResponse(BaseModel):
    codigo: str
    mensagem: str
