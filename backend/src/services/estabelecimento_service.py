from uuid import UUID

from ..core.exceptions import NaoEncontrado
from ..core.utils import limpar_nome
from ..core.persistence.entity_mapper import EntityMapper
from ..dtos.estabelecimento_dto import EstabelecimentoDTO
from ..repositories import EstabelecimentoRepository
from .base_service import BaseService


class EstabelecimentoService(BaseService):
    def listar(self, busca: str | None = None) -> list[EstabelecimentoDTO]:
        with self.session_factory() as session:
            entidades = EstabelecimentoRepository(session).listar(
                limpar_nome(busca) if busca else None
            )
            return [EntityMapper.estabelecimento(item) for item in entidades]

    def obter(self, estabelecimento_id: UUID) -> EstabelecimentoDTO:
        with self.session_factory() as session:
            entidade = EstabelecimentoRepository(session).obter(estabelecimento_id)
            if entidade is None:
                raise NaoEncontrado("Estabelecimento não encontrado.")
            return EntityMapper.estabelecimento(entidade)

    def atualizar_apelido(
        self, estabelecimento_id: UUID, apelido: str | None
    ) -> EstabelecimentoDTO:
        with self.session_factory.begin() as session:
            entidade = EstabelecimentoRepository(session).obter(estabelecimento_id)
            if entidade is None:
                raise NaoEncontrado("Estabelecimento não encontrado.")
            entidade.apelido = self.texto_opcional(apelido)
            session.flush()
            return EntityMapper.estabelecimento(entidade)
