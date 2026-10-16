import { ItemNota, Nota, SituacaoNota } from '../models/api.models';

export function quantidadeItensPendentes(nota: Nota): number {
  return nota.itens.filter((item) => !item.ignorado && !item.revisado).length;
}

export function todosItensRevisados(nota: Nota): boolean {
  return !nota.ignorada && nota.itens.some((item) => !item.ignorado) && quantidadeItensPendentes(nota) === 0;
}

export function rotuloSituacao(situacao: SituacaoNota): string {
  return {
    lida: 'Aguardando revisão',
    em_revisao: 'Em revisão',
    importada: 'Importada',
    ignorada: 'Ignorada',
  }[situacao];
}

export function possuiPendencia(item: ItemNota): boolean {
  return !item.ignorado && (!item.revisado || item.alertas.length > 0);
}
