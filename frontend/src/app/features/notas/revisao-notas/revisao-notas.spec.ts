import { registerLocaleData } from '@angular/common';
import localePt from '@angular/common/locales/pt';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of, Subject } from 'rxjs';
import { describe, expect, it, vi } from 'vitest';

import { ApiService } from '../../../core/api/api.service';
import { Nota } from '../../../core/models/api.models';
import { RevisaoNotas } from './revisao-notas';

registerLocaleData(localePt);

describe('metadados na revisão', () => {
  function criar() {
    const nota: Nota = {
      id: 'nota',
      chave: '1'.repeat(44),
      numero: '1',
      serie: '1',
      estabelecimento: {
        id: 'loja',
        cnpj: '1',
        razao_social: 'Loja',
        apelido: null,
        nome_exibicao: 'Loja',
      },
      emissao: '2026-12-31T23:59:00',
      quantidade_itens: 1,
      valor_total: '10.00',
      desconto: '0.00',
      valor_a_pagar: '10.00',
      url_origem: '',
      situacao: 'lida',
      importada_em: null,
      considerar_proximo_mes: false,
      itens: [
        {
          id: 'item',
          numero: 1,
          codigo: '1',
          descricao_original: 'Produto',
          quantidade: '1',
          unidade_original: 'UN',
          valor_unitario: '10.00',
          valor_total: '10.00',
          alertas: [],
          apresentacao: null,
          variacao: null,
          quantidade_confirmada: null,
          revisado: false,
          tags: [{ id: 'tag', nome: 'Festa' }],
        },
      ],
    };
    const resposta = new Subject<Nota>();
    const api = {
      obterNota: () => of(nota),
      listarProdutos: () => of([]),
      listarCategorias: () => of([]),
      listarMarcas: () => of([]),
      listarUnidadesMedida: () => of([]),
      listarTags: () => of(nota.itens[0].tags),
      definirTagsItem: vi.fn(() => resposta),
      definirCompetencia: vi.fn(() => resposta),
    };
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: ApiService, useValue: api },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ chave: nota.chave }) } },
        },
      ],
    });
    const fixture = TestBed.createComponent(RevisaoNotas);
    fixture.detectChanges();
    return { fixture, nota, resposta, api };
  }

  it('salvar tags preserva a classificação ainda não confirmada', () => {
    const { fixture, nota, resposta } = criar();
    const form = fixture.componentInstance.formularioItem('item')!;
    form.patchValue({ produto_id: 'produto-em-edicao', quantidade_confirmada: 3 });
    fixture.componentInstance.removerTag(nota.itens[0], 'tag');
    resposta.next({ ...nota, itens: [{ ...nota.itens[0], tags: [] }] });
    expect(fixture.componentInstance.formularioItem('item')).toBe(form);
    expect(form.get('produto_id')?.value).toBe('produto-em-edicao');
    expect(form.get('quantidade_confirmada')?.value).toBe(3);
    expect(fixture.componentInstance.nota()?.itens[0].tags).toEqual([]);
  });

  it('falha ao mudar o mês mantém o checkbox no valor salvo', () => {
    const { fixture, resposta, api } = criar();
    const campo = fixture.nativeElement.querySelector('input[type=checkbox]') as HTMLInputElement;
    campo.checked = true;
    campo.dispatchEvent(new Event('change'));
    expect(api.definirCompetencia).toHaveBeenCalledWith('1'.repeat(44), true);
    resposta.error(new Error('Falha'));
    fixture.detectChanges();
    expect(campo.checked).toBe(false);
    expect(fixture.componentInstance.nota()?.considerar_proximo_mes).toBe(false);
  });
});
