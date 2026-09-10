from collections.abc import Callable

from ..core.exceptions import ErroConsulta, ErroLeitura, ErroPersistencia
from ..models.leitura_nota import LeituraNota
from ..persistence.repositorio_notas import RepositorioNotas
from .consulta import consultar_nota
from .leitura import extrair_nota
from .qrcode import extrair_chave


class ServicoLeituraNotas:
    """Coordena captura, consulta, extração e persistência de uma NFC-e."""

    def __init__(
        self,
        repositorio: RepositorioNotas,
        consultar: Callable[[str], bytes] = consultar_nota,
    ):
        self.repositorio = repositorio
        self.consultar = consultar

    def ler(self, url: str) -> LeituraNota:
        chave = extrair_chave(url)
        leitura = self.repositorio.registrar_leitura(url, chave)
        if leitura.nota is not None:
            return leitura

        try:
            html = self.consultar(url)
            nota = extrair_nota(html, url)
            self.repositorio.salvar(nota, leitura.id)
            resultado = self.repositorio.obter_leitura_por_chave(chave)
            if resultado is None:
                raise ErroPersistencia("A leitura salva não pôde ser recuperada.")
            return resultado
        except (ErroConsulta, ErroLeitura, ErroPersistencia) as erro:
            self.repositorio.registrar_erro(leitura.id, str(erro))
            raise
