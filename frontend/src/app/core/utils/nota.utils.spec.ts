import { describe, expect, it } from 'vitest';

import { Nota } from '../models/api.models';
import { quantidadeItensPendentes, todosItensRevisados } from './nota.utils';

function criarNota(revisoes: boolean[]): Nota {
  return {
    id: 'nota',
    chave: '1'.repeat(44),
    numero: '1',
    serie: '1',
    estabelecimento: {
      id: 'est',
      cnpj: '1',
      razao_social: 'Mercado',
      apelido: null,
      nome_exibicao: 'Mercado',
    },
    emissao: '2026-09-12T10:00:00',
    quantidade_itens: revisoes.length,
    valor_total: '10.00',
    desconto: '0.00',
    valor_a_pagar: '10.00',
    url_origem: 'https://example.test',
    situacao: 'em_revisao',
    importada_em: null,
    itens: revisoes.map((revisado, numero) => ({
      id: String(numero),
      numero,
      codigo: '',
      descricao_original: 'Item',
      quantidade: '1',
      unidade_original: 'UN',
      valor_unitario: '10.00',
      valor_total: '10.00',
      alertas: [],
      apresentacao: null,
      unidade_corrigida: null,
      quantidade_normalizada: null,
      revisado,
    })),
  };
}

describe('estado de revisão da nota', () => {
  it('conta somente os itens ainda não revisados', () => {
    expect(quantidadeItensPendentes(criarNota([true, false, false]))).toBe(2);
  });

  it('só libera a importação quando há itens e todos estão revisados', () => {
    expect(todosItensRevisados(criarNota([true, true]))).toBe(true);
    expect(todosItensRevisados(criarNota([true, false]))).toBe(false);
    expect(todosItensRevisados(criarNota([]))).toBe(false);
  });
});
