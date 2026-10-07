from dataclasses import dataclass


@dataclass
class RestricoesProdutoDTO:
    pode_alterar_estrutura: bool
    pode_excluir: bool
    motivo_alteracao_estrutura: str | None
    motivo_exclusao: str | None
