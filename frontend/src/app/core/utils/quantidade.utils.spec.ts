import { describe, expect, it } from 'vitest';
import { Produto } from '../models/api.models';
import { sugerirQuantidade } from './quantidade.utils';

function produto(opcoes: Partial<Produto>): Produto {
  return {
    id: 'produto', nome: 'Produto', categoria: { id: 'categoria', nome: 'Categoria' },
    nao_solicitar_marca: false, tratar_apenas_como_unidades: false,
    contem_variacoes: false, unidade_medida: 'G', ...opcoes,
  };
}

describe('sugestão da quantidade na importação', () => {
  it('deixa em branco uma quantidade fracionária para produto por unidade', () => {
    expect(sugerirQuantidade('1.5', 'UN', produto({ tratar_apenas_como_unidades: true, unidade_medida: null }))).toBeNull();
  });

  it('aceita quantidade inteira para produto com variações', () => {
    expect(sugerirQuantidade('2', 'UN', produto({ contem_variacoes: true }))).toBe(2);
  });

  it('converte peso e volume entre unidades compatíveis', () => {
    expect(sugerirQuantidade('1.5', 'KG', produto({ unidade_medida: 'G' }))).toBe(1500);
    expect(sugerirQuantidade('500', 'ML', produto({ unidade_medida: 'L' }))).toBe(0.5);
  });

  it('mantém o número quando as unidades são incompatíveis', () => {
    expect(sugerirQuantidade('3', 'UN', produto({ unidade_medida: 'KG' }))).toBe(3);
  });
});
