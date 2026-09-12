import { ItemNota, Nota, SituacaoNota } from '../models/api.models';

export function quantidadeItensPendentes(nota: Nota): number {
  return nota.itens.filter((item) => !item.revisado).length;
}

export function todosItensRevisados(nota: Nota): boolean {
  return nota.itens.length > 0 && quantidadeItensPendentes(nota) === 0;
}

export function rotuloSituacao(situacao: SituacaoNota): string {
  return {
    lida: 'Lida',
    em_revisao: 'Em revisão',
    importada: 'Importada',
  }[situacao];
}

export function possuiPendencia(item: ItemNota): boolean {
  return !item.revisado || item.alertas.length > 0;
}
