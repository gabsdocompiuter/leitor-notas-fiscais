import { Pipe, PipeTransform } from '@angular/core';
import { QuantidadeRelatorio, UnidadeQuantidade } from '../../core/models/api.models';

const nomes: Record<UnidadeQuantidade, string> = {
  UN: 'unidades',
  KG: 'kg',
  G: 'g',
  L: 'L',
  ML: 'mL',
};
const ordem: UnidadeQuantidade[] = ['UN', 'KG', 'G', 'L', 'ML'];

// Formata a string decimal sem arredondar nem converter a soma para ponto flutuante.
export function formatarQuantidadeRelatorio(valor: string, unidade: UnidadeQuantidade): string {
  const [inteiro, fracao = ''] = valor.split('.');
  const decimais = fracao.replace(/0+$/, '');
  const numero = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (decimais ? ',' + decimais : '');
  const nome = unidade === 'UN' && /^0*1(?:\.0*)?$/.test(valor) ? 'unidade' : nomes[unidade];
  return `${numero} ${nome}`;
}

@Pipe({ name: 'quantidadeComprada' })
export class QuantidadeCompradaPipe implements PipeTransform {
  transform(
    valor: string | null | undefined,
    unidade: UnidadeQuantidade | null | undefined,
  ): string {
    return valor != null && unidade
      ? formatarQuantidadeRelatorio(valor, unidade)
      : 'Quantidade não informada';
  }
}

@Pipe({ name: 'quantidadesCompradas' })
export class QuantidadesCompradasPipe implements PipeTransform {
  transform(valores: QuantidadeRelatorio[] | undefined): string {
    return [...(valores ?? [])]
      .sort((a, b) => ordem.indexOf(a.unidade) - ordem.indexOf(b.unidade))
      .map((q) => formatarQuantidadeRelatorio(q.quantidade, q.unidade))
      .join(' · ');
  }
}
