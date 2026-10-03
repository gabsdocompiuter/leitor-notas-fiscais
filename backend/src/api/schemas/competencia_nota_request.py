from pydantic import BaseModel


class CompetenciaNotaRequest(BaseModel):
    considerar_proximo_mes: bool
