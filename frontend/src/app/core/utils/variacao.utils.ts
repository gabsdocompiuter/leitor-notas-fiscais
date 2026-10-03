import { UnidadeMedida } from '../models/api.models';

export function normalizarQuantidade(valor: string): string {
  const texto = valor.trim().replace(',', '.');
  if (!/^\d+(?:\.\d*)?$/.test(texto)) return texto;
  const [inteiro, decimal = ''] = texto.split('.');
  const fracao = decimal.replace(/0+$/, '');
  return `${inteiro.replace(/^0+(?=\d)/, '')}${fracao ? `.${fracao}` : ''}`;
}

export function extrairMedida(
  descricao: string,
): { quantidade: string; unidade: UnidadeMedida } | null {
  const medidas = new Map<string, { quantidade: string; unidade: UnidadeMedida }>();
  const padrao = /(?:^|[^\p{L}\p{N}.,])([0-9]+(?:[.,][0-9]+)?)\s*(KG|ML|G|L)(?!\p{L}|\p{N})/giu;
  for (const match of descricao.matchAll(padrao)) {
    const quantidade = normalizarQuantidade(
      Number(Number(match[1].replace(',', '.')).toFixed(3)).toString(),
    );
    if (Number(quantidade) < 0.001 || !Number.isFinite(Number(quantidade))) continue;
    const unidade = match[2].toUpperCase() as UnidadeMedida;
    medidas.set(`${quantidade}:${unidade}`, { quantidade, unidade });
  }
  return medidas.size === 1 ? [...medidas.values()][0] : null;
}
