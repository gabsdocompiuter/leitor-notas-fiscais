from uuid import UUID

from ..core.exceptions import DadosInvalidos, NaoEncontrado
from ..entities.estabelecimento_entity import EstabelecimentoEntity
from ..core.utils import limpar_nome
from ..core.persistence.entity_mapper import EntityMapper
from ..dtos.estabelecimento_dto import EstabelecimentoDTO
from ..repositories import EstabelecimentoRepository
from .base_service import BaseService


class EstabelecimentoService(BaseService):
    def criar(self, apelido: str) -> EstabelecimentoDTO:
        apelido = limpar_nome(apelido)
        if not apelido or len(apelido) > 100:
            raise DadosInvalidos("O apelido deve ter entre 1 e 100 caracteres.")
        with self.session_factory.begin() as session:
            entidade = EstabelecimentoRepository(session).adicionar(
                EstabelecimentoEntity(apelido=apelido, cnpj=None, razao_social=None)
            )
            return EntityMapper.estabelecimento(entidade)

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
            apelido = self.texto_opcional(apelido)
            if apelido and len(apelido) > 100:
                raise DadosInvalidos("O apelido deve ter no máximo 100 caracteres.")
            if not entidade.razao_social and not apelido:
                raise DadosInvalidos("O apelido é obrigatório para estabelecimentos manuais.")
            entidade.apelido = apelido
            session.flush()
            return EntityMapper.estabelecimento(entidade)
