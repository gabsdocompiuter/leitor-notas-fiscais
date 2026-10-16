from pydantic import BaseModel, StrictBool


class IgnorarNotaRequest(BaseModel):
    ignorada: StrictBool


class IgnorarItemRequest(BaseModel):
    ignorado: StrictBool
