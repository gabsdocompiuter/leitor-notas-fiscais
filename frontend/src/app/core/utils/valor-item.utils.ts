export type TipoValorItem = 'total' | 'unitario';

export function valoresItem(
  valor: number | null,
  quantidade: number | null,
  tipo: TipoValorItem = 'total',
): { total: number | null; unitario: number | null } {
  if (valor === null || !Number.isFinite(valor) || valor < 0 ||
      valor > 9999999999999.99 || !/^\d+(?:\.\d{1,2})?$/.test(String(valor))) {
    return { total: null, unitario: null };
  }
  const quantidadeValida = quantidade !== null && Number.isFinite(quantidade) &&
    quantidade > 0 && /^\d+(?:\.\d{1,3})?$/.test(String(quantidade));
  if (tipo === 'total') {
    return { total: valor, unitario: quantidadeValida ? valor / quantidade! : null };
  }
  if (!quantidadeValida) return { total: null, unitario: valor };
  const [inteiro, fracao = ''] = String(quantidade).split('.');
  const milesimos = BigInt(inteiro) * 1000n + BigInt(fracao.padEnd(3, '0'));
  const centavos = BigInt(valor.toFixed(2).replace('.', ''));
  // Arredondamento monetário de metade para cima, igual ao Decimal do servidor.
  const total = Number((centavos * milesimos + 500n) / 1000n) / 100;
  return { total, unitario: valor };
}
