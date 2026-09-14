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
        unidade_corrigida: UnidadeMedida,
        quantidade_normalizada: Decimal,
    ) -> Nota:
        if quantidade_normalizada <= 0:
            raise DadosInvalidos("A quantidade normalizada deve ser maior que zero.")
        return self.repositorio.revisar_item(
            chave,
            item_id,
            produto_id,
            marca_id,
            unidade_corrigida,
            quantidade_normalizada,
        )

    def aplicar_classificacoes_automaticas(self, chave: str) -> Nota:
        return self.repositorio.aplicar_classificacoes_automaticas(chave)

    def concluir_importacao(self, chave: str) -> Nota:
        return self.repositorio.concluir_importacao(chave)
