from enum import Enum


class UnidadeMedida(str, Enum):
    QUILOGRAMA = "KG"
    GRAMA = "G"
    LITRO = "L"
    MILILITRO = "ML"

    @property
    def descricao(self) -> str:
        return {
            self.QUILOGRAMA: "Quilograma",
            self.GRAMA: "Grama",
            self.LITRO: "Litro",
            self.MILILITRO: "Mililitro",
        }[self]
