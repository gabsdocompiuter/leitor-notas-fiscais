from contextlib import contextmanager
from threading import Condition
from typing import Iterator


class BancoOcupado(Exception):
    pass


class CoordenacaoBanco:
    """Coordena requisições completas, incluindo chamadas à SEFAZ, em um processo."""

    def __init__(self):
        self._condicao = Condition()
        self._ativas = 0
        self._importando = False
        self._substituindo = False
        self._indisponivel = False

    def entrar(self, importacao: bool = False) -> int | None:
        with self._condicao:
            if self._indisponivel:
                return 503
            if importacao:
                if self._importando:
                    return 409
                self._importando = True
            else:
                if self._substituindo:
                    return 503
                self._ativas += 1
            return None

    def sair(self, importacao: bool = False) -> None:
        with self._condicao:
            if importacao:
                self._importando = False
            else:
                self._ativas -= 1
            self._condicao.notify_all()

    @property
    def indisponivel(self) -> bool:
        with self._condicao:
            return self._indisponivel

    def bloquear(self) -> None:
        with self._condicao:
            self._indisponivel = True

    @contextmanager
    def substituir(self) -> Iterator[None]:
        with self._condicao:
            self._substituindo = True
            self._condicao.notify_all()
        try:
            with self._condicao:
                if not self._condicao.wait_for(lambda: self._ativas == 0, timeout=60):
                    raise BancoOcupado("O banco está em uso. Tente importar novamente.")
            yield
        finally:
            with self._condicao:
                self._substituindo = False
                self._condicao.notify_all()
