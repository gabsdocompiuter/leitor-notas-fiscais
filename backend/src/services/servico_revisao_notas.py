from decimal import Decimal
from uuid import UUID

from ..core.exceptions import DadosInvalidos
from ..models.nota import Nota
from ..models.unidade_medida import UnidadeMedida
from ..persistence.repositorio_revisao import RepositorioRevisao


class ServicoRevisaoNotas:
    def __init__(self, repositorio: RepositorioRevisao):
        self.repositorio = repositorio

    def revisar_item(
        self,
        chave: str,
        item_id: UUID,
        produto_id: UUID,
        marca_id: UUID | None,
        marca_confirmada: bool,
        conteudo_embalagem: Decimal | None,
        unidade_embalagem: UnidadeMedida | None,
        unidade_corrigida: UnidadeMedida,
        quantidade_normalizada: Decimal,
    ) -> Nota:
        if not marca_confirmada:
            raise DadosInvalidos(
                "A marca deve ser informada ou sua ausência precisa ser confirmada."
            )
        if (conteudo_embalagem is None) != (unidade_embalagem is None):
            raise DadosInvalidos(
                "Conteúdo e unidade da embalagem devem ser informados juntos."
            )
        if conteudo_embalagem is not None and conteudo_embalagem <= 0:
            raise DadosInvalidos("O conteúdo da embalagem deve ser maior que zero.")
        if quantidade_normalizada <= 0:
            raise DadosInvalidos("A quantidade normalizada deve ser maior que zero.")
        return self.repositorio.revisar_item(
            chave,
            item_id,
            produto_id,
            marca_id,
            marca_confirmada,
            conteudo_embalagem,
            unidade_embalagem,
            unidade_corrigida,
            quantidade_normalizada,
        )

    def aplicar_classificacoes_automaticas(self, chave: str) -> Nota:
        return self.repositorio.aplicar_classificacoes_automaticas(chave)

    def concluir_importacao(self, chave: str) -> Nota:
        return self.repositorio.concluir_importacao(chave)
