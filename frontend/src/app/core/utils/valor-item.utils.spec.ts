import { describe, expect, it } from 'vitest';
import { valoresItem } from './valor-item.utils';

describe('valor total ou unitário de um item', () => {
  it('interpreta o mesmo valor conforme o tipo escolhido', () => {
    expect(valoresItem(15, 5, 'total')).toEqual({ total: 15, unitario: 3 });
    expect(valoresItem(15, 5, 'unitario')).toEqual({ total: 75, unitario: 15 });
  });
  it('arredonda os centavos com quantidade fracionada como o servidor', () => {
    expect(valoresItem(0.29, 0.5, 'unitario')).toEqual({ total: 0.15, unitario: 0.29 });
    expect(valoresItem(0.1, 3, 'unitario')).toEqual({ total: 0.3, unitario: 0.1 });
    expect(valoresItem(0.01, 0.5, 'unitario')).toEqual({ total: 0.01, unitario: 0.01 });
  });
  it('aceita zero e não calcula totais com entradas inválidas', () => {
    expect(valoresItem(0, 12, 'unitario')).toEqual({ total: 0, unitario: 0 });
    expect(valoresItem(null, 2, 'unitario').total).toBeNull();
    expect(valoresItem(2, 0, 'unitario').total).toBeNull();
    expect(valoresItem(2, 1.0001, 'unitario').total).toBeNull();
    expect(valoresItem(-1, 2, 'total').total).toBeNull();
    expect(valoresItem(1.001, 2, 'unitario').total).toBeNull();
  });
});
