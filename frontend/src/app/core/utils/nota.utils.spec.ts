import { describe, expect, it } from 'vitest';

import { Nota } from '../models/api.models';
import { quantidadeItensPendentes, rotuloSituacao, todosItensRevisados } from './nota.utils';

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
    considerar_proximo_mes: false,
    ignorada: false,
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
      tags: [],
      apresentacao: null,
      variacao: null,
      quantidade_confirmada: null,
      quantidade_pacotes: null,
      unidades_por_pacote: null,
      revisado,
      ignorado: false,
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

  it('apresenta a situação lida como aguardando revisão', () => {
    expect(rotuloSituacao('lida')).toBe('Aguardando revisão');
    expect(rotuloSituacao('ignorada')).toBe('Ignorada');
  });

  it('dispensa ignorados, mas exige pelo menos um item considerado para importar', () => {
    const nota = criarNota([true, false]);
    nota.itens[1].ignorado = true;
    expect(quantidadeItensPendentes(nota)).toBe(0);
    expect(todosItensRevisados(nota)).toBe(true);
    nota.itens[0].ignorado = true;
    expect(todosItensRevisados(nota)).toBe(false);
  });

  it('não permite importar uma nota ignorada mesmo com itens revisados', () => {
    const nota = criarNota([true]);
    nota.ignorada = true;
    nota.situacao = 'ignorada';
    expect(todosItensRevisados(nota)).toBe(false);
  });
});
