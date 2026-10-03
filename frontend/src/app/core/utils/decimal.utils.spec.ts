import { FormControl } from '@angular/forms';
import { describe, expect, it } from 'vitest';
import {
  decimalValido,
  formatarDecimal,
  formatarVariacao,
  limitarEntradaDecimal,
  validarDecimal,
} from './decimal.utils';

describe('decimais padronizados', () => {
  it('usa vírgula decimal, milhar e no máximo três casas sem zeros finais', () => {
    expect(formatarDecimal('1.15000')).toBe('1,15');
    expect(formatarDecimal('1123.15')).toBe('1.123,15');
    expect(formatarDecimal('1.123,15')).toBe('1.123,15');
    expect(formatarDecimal('1.001')).toBe('1,001');
    expect(formatarDecimal('1.12356')).toBe('1,124');
    expect(formatarDecimal('250.000')).toBe('250');
    expect(
      formatarVariacao({
        id: 'v',
        produto_id: 'p',
        quantidade: '1123.15',
        unidade_medida: 'KG',
        nome_exibicao: '1123.15 KG',
      }),
    ).toBe('1.123,15 KG');
  });
  it('limita digitação e colagem e aceita ponto ou vírgula de entrada', () => {
    expect(limitarEntradaDecimal('1,12345')).toBe('1,123');
    expect(limitarEntradaDecimal('1.12345')).toBe('1,123');
    expect(limitarEntradaDecimal('1.123,15')).toBe('1123,15');
    expect(limitarEntradaDecimal(',5')).toBe('0,5');
  });
  it('valida valores programáticos e a precisão do formulário', () => {
    expect(decimalValido(1.001)).toBe(true);
    expect(decimalValido('1,15')).toBe(true);
    expect(decimalValido(1.0001)).toBe(false);
    expect(decimalValido(Infinity)).toBe(false);
    expect(validarDecimal(new FormControl(1.0001))).toEqual({ casasDecimais: true });
  });
});
