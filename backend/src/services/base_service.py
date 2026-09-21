from sqlalchemy.orm import Session, sessionmaker

from ..core.exceptions import DadosInvalidos
from ..core.utils import limpar_nome


class BaseService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    @staticmethod
    def nome_obrigatorio(valor: str) -> str:
        nome = limpar_nome(valor)
        if not nome:
            raise DadosInvalidos("O nome não pode ficar vazio.")
        return nome

    @staticmethod
    def texto_opcional(valor: str | None) -> str | None:
        texto = limpar_nome(valor) if valor else ""
        return texto or None
