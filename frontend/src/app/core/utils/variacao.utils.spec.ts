import { describe, expect, it } from 'vitest';
import { extrairMedida, normalizarQuantidade } from './variacao.utils';

describe('medidas da descrição fiscal', () => {
  it('extrai medida única, decimal e unidades sem distinguir caixa', () => {
    expect(extrairMedida('CAFE PO 3 CORACOES GOURMET 250g SUL DE MINAS')).toEqual({
      quantidade: '250',
      unidade: 'G',
    });
    expect(extrairMedida('REFRIGERANTE 1,5 L')).toEqual({ quantidade: '1.5', unidade: 'L' });
    expect(extrairMedida('ARROZ 01.500kg')).toEqual({ quantidade: '1.5', unidade: 'KG' });
    expect(extrairMedida('SUCO 500 ML')).toEqual({ quantidade: '500', unidade: 'ML' });
  });
  it('não sugere medida ausente, inválida ou ambígua', () => {
    for (const texto of [
      '3 CORACOES',
      'kit 500 ml + 200 ml',
      'produto 0 G',
      '500 GRANEL',
      'ABC250G',
      '1.000,5 G',
    ]) {
      expect(extrairMedida(texto)).toBeNull();
    }
  });
  it('aceita repetição da mesma medida normalizada', () => {
    expect(extrairMedida('250 G embalagem 250,0 g')).toEqual({ quantidade: '250', unidade: 'G' });
  });
  it('normaliza representação decimal para comparar prefixos', () => {
    expect(normalizarQuantidade('0250.000')).toBe('250');
    expect(normalizarQuantidade('1,50')).toBe('1.5');
    expect(normalizarQuantidade('0.0500')).toBe('0.05');
  });
});
