from enum import Enum


class SituacaoNota(str, Enum):
    LIDA = "lida"
    EM_REVISAO = "em_revisao"
    IMPORTADA = "importada"
