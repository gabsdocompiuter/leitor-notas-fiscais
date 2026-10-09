import { describe, expect, it } from 'vitest';
import { QuantidadeCompradaPipe, QuantidadesCompradasPipe } from './quantidade-relatorio.pipe';

describe('Quantidades compradas nos relatórios', () => {
  const quantidade = new QuantidadeCompradaPipe();
  it('formata unidades, peso e volume sem perder casas decimais', () => {
    expect(quantidade.transform('1.000', 'UN')).toBe('1 unidade');
    expect(quantidade.transform('3', 'UN')).toBe('3 unidades');
    expect(quantidade.transform('750.000', 'G')).toBe('750 g');
    expect(quantidade.transform('1.500', 'KG')).toBe('1,5 kg');
    expect(quantidade.transform('1000.123450', 'ML')).toBe('1.000,12345 mL');
    expect(quantidade.transform('2', 'L')).toBe('2 L');
    expect(quantidade.transform('9007199254740993.00001', 'G')).toBe(
      '9.007.199.254.740.993,00001 g',
    );
  });
  it('mantém as grandezas separadas e ordenadas', () => {
    const valores = [
      { quantidade: '2', unidade: 'L' as const },
      { quantidade: '750', unidade: 'G' as const },
      { quantidade: '3', unidade: 'UN' as const },
      { quantidade: '1.5', unidade: 'KG' as const },
      { quantidade: '25', unidade: 'ML' as const },
    ];
    expect(new QuantidadesCompradasPipe().transform(valores)).toBe(
      '3 unidades · 1,5 kg · 750 g · 2 L · 25 mL',
    );
    expect(valores[0].unidade).toBe('L');
    expect(new QuantidadesCompradasPipe().transform([])).toBe('');
  });
  it('não inventa quantidades ausentes', () => {
    expect(quantidade.transform(null, 'UN')).toBe('Quantidade não informada');
    expect(quantidade.transform('0', 'UN')).toBe('0 unidades');
  });
});
