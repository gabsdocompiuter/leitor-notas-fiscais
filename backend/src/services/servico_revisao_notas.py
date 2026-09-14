from decimal import Decimal
from uuid import UUID

from ..core.exceptions import DadosInvalidos
from ..models.nota import Nota
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
        variacao_id: UUID | None,
        quantidade_confirmada: Decimal,
    ) -> Nota:
        if quantidade_confirmada <= 0:
            raise DadosInvalidos("A quantidade confirmada deve ser maior que zero.")
        return self.repositorio.revisar_item(
            chave,
            item_id,
            produto_id,
            marca_id,
            variacao_id,
            quantidade_confirmada,
        )

    def aplicar_classificacoes_automaticas(self, chave: str) -> Nota:
        return self.repositorio.aplicar_classificacoes_automaticas(chave)

    def concluir_importacao(self, chave: str) -> Nota:
        return self.repositorio.concluir_importacao(chave)
