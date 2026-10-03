from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from ..entities.nota_entity import NotaEntity
from ..enums.situacao_nota import SituacaoNota
from .nota_repository import NotaRepository


class RelatorioRepository:
    def __init__(self, session: Session):
        self.session = session

    def listar_notas_mes(
        self, anterior: datetime, inicio: datetime, seguinte: datetime
    ) -> list[NotaEntity]:
        consulta = (
            select(NotaEntity)
            .options(*NotaRepository.opcoes_carregamento())
            .where(
                NotaEntity.situacao == SituacaoNota.IMPORTADA,
                or_(
                    and_(
                        NotaEntity.considerar_proximo_mes.is_(False),
                        NotaEntity.emissao >= inicio,
                        NotaEntity.emissao < seguinte,
                    ),
                    and_(
                        NotaEntity.considerar_proximo_mes.is_(True),
                        NotaEntity.emissao >= anterior,
                        NotaEntity.emissao < inicio,
                    ),
                ),
            )
            .order_by(NotaEntity.emissao.desc(), NotaEntity.id)
        )
        return list(self.session.scalars(consulta))
