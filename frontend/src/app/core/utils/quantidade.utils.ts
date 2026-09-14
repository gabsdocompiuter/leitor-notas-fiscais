import { Produto, UnidadeMedida } from '../models/api.models';

export function sugerirQuantidade(
  quantidadeOriginal: string,
  unidadeOriginal: string,
  produto: Produto,
): number | null {
  const quantidade = Number(quantidadeOriginal);
  if (!Number.isFinite(quantidade)) return null;
  if (produto.tratar_apenas_como_unidades || produto.contem_variacoes) {
    return Number.isInteger(quantidade) ? quantidade : null;
  }
  return converterQuantidade(quantidade, unidadeOriginal, produto.unidade_medida);
}

export function converterQuantidade(
  quantidade: number,
  unidadeOriginal: string,
  unidadeDestino: UnidadeMedida | null,
): number {
  const origem = unidadeOriginal.toUpperCase();
  if (!unidadeDestino || origem === unidadeDestino) return quantidade;
  const fatores: Record<string, number> = {
    'KG:G': 1000,
    'G:KG': 0.001,
    'L:ML': 1000,
    'ML:L': 0.001,
  };
  return quantidade * (fatores[`${origem}:${unidadeDestino}`] ?? 1);
}
