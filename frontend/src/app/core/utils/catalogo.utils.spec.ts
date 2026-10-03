import { describe, expect, it } from 'vitest';

import { capitalizarIniciais, filtrarCatalogo } from './catalogo.utils';

interface Opcao {
  nome: string;
}

const opcoes: Opcao[] = [
  { nome: 'Queijo mussarela' },
  { nome: 'Leite Integral' },
  { nome: 'Café torrado' },
];

describe('busca de catálogos', () => {
  it('ignora termos curtos em frases e palavras curtas na comparação inversa', () => {
    const itens = [{ nome: 'Bandeja de Ovos' }, { nome: 'Café' }, { nome: 'De' }];
    expect(filtrarCatalogo(itens, 'cafe de minas', (item) => item.nome)).toEqual([
      { nome: 'Café' },
    ]);
    expect(filtrarCatalogo([{ nome: 'De' }], 'bandeja grande', (item) => item.nome)).toEqual([]);
  });

  it('preserva palavra única curta e mostra catálogo se todos os termos forem descartados', () => {
    const itens = [{ nome: '3M' }, { nome: 'Café' }];
    expect(filtrarCatalogo(itens, '3M', (item) => item.nome)).toEqual([{ nome: '3M' }]);
    expect(filtrarCatalogo(itens, 'a de', (item) => item.nome)).toEqual(itens);
  });

  it('formata a descrição fiscal com as iniciais em maiúsculas', () => {
    expect(capitalizarIniciais('LEIT INT UHT 1L')).toBe('Leit Int Uht 1l');
    expect(capitalizarIniciais('CAFÉ TORRADO-EXTRAFORTE')).toBe('Café Torrado-Extraforte');
  });

  it('relaciona abreviações da descrição fiscal ao nome normalizado', () => {
    const resultado = filtrarCatalogo(opcoes, 'LEIT INT UHT 1L', (item) => item.nome);
    expect(resultado[0].nome).toBe('Leite Integral');
  });

  it('ignora acentos e diferenças entre maiúsculas e minúsculas', () => {
    const resultado = filtrarCatalogo(opcoes, 'CAFE', (item) => item.nome);
    expect(resultado).toEqual([{ nome: 'Café torrado' }]);
  });

  it('não retorna opções sem nenhum termo relacionado', () => {
    expect(filtrarCatalogo(opcoes, 'arroz', (item) => item.nome)).toEqual([]);
  });
});
