from enum import Enum


class UnidadeMedida(str, Enum):
    UNIDADE = "UN"
    QUILOGRAMA = "KG"
    GRAMA = "G"
    LITRO = "L"
    MILILITRO = "ML"
