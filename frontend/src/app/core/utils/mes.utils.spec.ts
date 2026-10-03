import { describe, expect, it } from 'vitest';
import { deslocarMes, formatarMes, mesValido } from './mes.utils';

describe('mês considerado', () => {
  it('avança um mês civil e atravessa a virada do ano', () => {
    expect(deslocarMes('2026-12', 1)).toBe('2027-01');
    expect(deslocarMes('2027-01', -1)).toBe('2026-12');
    expect(deslocarMes('2026-01', 1)).toBe('2026-02');
  });
  it('formata a data local sem converter para UTC', () => {
    expect(formatarMes(new Date(2026, 8, 30, 23, 59))).toBe('2026-09');
  });
  it('rejeita meses fora do intervalo suportado', () => {
    expect(mesValido('2026-10')).toBe(true);
    for (const valor of ['2026-13', '2026-00', '0001-01', '9999-12', '2026-1', '']) {
      expect(mesValido(valor)).toBe(false);
    }
  });
});
