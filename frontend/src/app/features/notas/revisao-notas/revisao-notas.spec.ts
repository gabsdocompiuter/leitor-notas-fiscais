import { registerLocaleData } from '@angular/common';
import localePt from '@angular/common/locales/pt';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of, Subject } from 'rxjs';
import { describe, expect, it, vi } from 'vitest';

import { ApiService } from '../../../core/api/api.service';
import { ItemNota, Nota, Produto } from '../../../core/models/api.models';
import { RevisaoNotas } from './revisao-notas';

registerLocaleData(localePt);

describe('metadados na revisão', () => {
  const produto: Produto = {
    id: 'produto', nome: 'Filtro de café', categoria: { id: 'cat', nome: 'Alimentos' },
    nao_solicitar_marca: true, tratar_apenas_como_unidades: true,
    contem_variacoes: false, unidade_medida: null,
  };
  const produtoPeso: Produto = {
    ...produto, id: 'peso', nome: 'Farinha', tratar_apenas_como_unidades: false,
    unidade_medida: 'G',
  };
  function criar(item: Partial<ItemNota> = {}, situacao: Nota['situacao'] = 'lida') {
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
      situacao,
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
          quantidade_pacotes: null,
          unidades_por_pacote: null,
          revisado: false,
          tags: [{ id: 'tag', nome: 'Festa' }],
          ...item,
        },
      ],
    };
    const resposta = new Subject<Nota>();
    const api = {
      obterNota: () => of(nota),
      listarProdutos: () => of([produto, produtoPeso]),
      listarCategorias: () => of([]),
      listarMarcas: () => of([]),
      listarUnidadesMedida: () => of([]),
      listarTags: () => of(nota.itens[0].tags),
      definirTagsItem: vi.fn(() => resposta),
      definirCompetencia: vi.fn(() => resposta),
      revisarItem: vi.fn(() => resposta),
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

  function selecionar(fixture: ReturnType<typeof criar>['fixture'], nota: Nota, escolhido = produto) {
    fixture.componentInstance.itemModal.set(nota.itens[0]);
    fixture.componentInstance.selecionarProduto(escolhido);
    fixture.detectChanges();
    return fixture.componentInstance.formularioItem('item')!;
  }

  it.each([1, 2])('salva %s pacotes e restaura o conteúdo ao receber a nota', (quantidade) => {
    const { fixture, nota, resposta, api } = criar();
    const form = selecionar(fixture, nota);
    form.patchValue({ tipo_quantidade: 'pacotes', quantidade_confirmada: quantidade, unidades_por_pacote: 30 });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain(`${quantidade * 30} unidades`);
    fixture.componentInstance.salvarItem(nota.itens[0]);
    expect(api.revisarItem).toHaveBeenCalledWith(nota.chave, 'item', {
      produto_id: 'produto', quantidade_confirmada: quantidade * 30,
      quantidade_pacotes: quantidade, unidades_por_pacote: 30, variacao_id: null,
    });
    resposta.next({ ...nota, itens: [{
      ...nota.itens[0], apresentacao: { id: 'ap', produto, marca: null }, revisado: true,
      quantidade_confirmada: String(quantidade * 30), quantidade_pacotes: String(quantidade),
      unidades_por_pacote: '30',
    }] });
    const restaurado = fixture.componentInstance.formularioItem('item')!;
    expect(restaurado.get('quantidade_confirmada')?.value).toBe(quantidade);
    expect(restaurado.get('tipo_quantidade')?.value).toBe('pacotes');
    expect(restaurado.get('unidades_por_pacote')?.value).toBe(30);
  });

  it('alterna o seletor preservando a quantidade e exige conteúdo somente em pacotes', () => {
    const { fixture, nota, api } = criar();
    const form = selecionar(fixture, nota);
    const seletor = fixture.nativeElement.querySelector('select[formControlName=tipo_quantidade]') as HTMLSelectElement;
    form.patchValue({ quantidade_confirmada: 2 });
    seletor.value = 'pacotes';
    seletor.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    expect(form.get('quantidade_confirmada')?.value).toBe(2);
    expect(form.get('unidades_por_pacote')?.value).toBeNull();
    expect(form.invalid).toBe(true);
    expect(fixture.nativeElement.querySelector('#unidades-pacote-item')).not.toBeNull();
    for (const unidades of [0, -1, 1.5]) {
      form.patchValue({ unidades_por_pacote: unidades });
      fixture.componentInstance.salvarItem(nota.itens[0]);
      expect(api.revisarItem).not.toHaveBeenCalled();
    }
    for (const quantidade of [0, -1, 1.5]) {
      form.patchValue({ quantidade_confirmada: quantidade, unidades_por_pacote: 30 });
      expect(form.invalid).toBe(true);
    }
    form.patchValue({ quantidade_confirmada: 2, unidades_por_pacote: 30 });
    seletor.value = 'unidades';
    seletor.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    expect(form.get('quantidade_confirmada')?.value).toBe(2);
    expect(fixture.nativeElement.querySelector('#unidades-pacote-item')).toBeNull();
    fixture.componentInstance.salvarItem(nota.itens[0]);
    expect(api.revisarItem).toHaveBeenCalledWith(nota.chave, 'item', {
      produto_id: 'produto', quantidade_confirmada: 2,
      quantidade_pacotes: null, unidades_por_pacote: null, variacao_id: null,
    });
  });

  it('trocar o produto reinicializa embalagem e mantém conversões de peso', () => {
    const { fixture, nota } = criar({ quantidade: '0.350', unidade_original: 'KG' });
    const form = selecionar(fixture, nota);
    expect(form.get('quantidade_confirmada')?.value).toBe(1);
    form.patchValue({ tipo_quantidade: 'pacotes', unidades_por_pacote: 30 });
    selecionar(fixture, nota, produtoPeso);
    expect(form.get('tipo_quantidade')?.value).toBe('unidades');
    expect(form.get('unidades_por_pacote')?.value).toBeNull();
    expect(form.get('quantidade_confirmada')?.value).toBe(350);
    expect(fixture.nativeElement.querySelector('select[formControlName=tipo_quantidade]')).toBeNull();
  });

  it('reabre e permite editar pacotes de uma nota importada e cancelar alterações', () => {
    const { fixture, nota, api } = criar({
      apresentacao: { id: 'ap', produto, marca: null }, revisado: true,
      quantidade_confirmada: '60', quantidade_pacotes: '2', unidades_por_pacote: '30',
    }, 'importada');
    const form = fixture.componentInstance.formularioItem('item')!;
    expect(form.get('quantidade_confirmada')?.value).toBe(2);
    expect(form.get('tipo_quantidade')?.disabled).toBe(true);
    expect(form.get('unidades_por_pacote')?.disabled).toBe(true);
    fixture.componentInstance.editarItem(nota.itens[0]);
    expect(form.get('tipo_quantidade')?.enabled).toBe(true);
    form.patchValue({ quantidade_confirmada: 3, unidades_por_pacote: 40 });
    fixture.componentInstance.cancelarEdicao(nota.itens[0]);
    expect(form.get('quantidade_confirmada')?.value).toBe(2);
    expect(form.get('unidades_por_pacote')?.value).toBe(30);
    expect(form.get('tipo_quantidade')?.disabled).toBe(true);
    fixture.componentInstance.editarItem(nota.itens[0]);
    form.patchValue({ quantidade_confirmada: 3 });
    fixture.componentInstance.salvarItem(nota.itens[0]);
    expect(api.revisarItem).toHaveBeenCalledWith(nota.chave, 'item', expect.objectContaining({
      quantidade_confirmada: 90, quantidade_pacotes: 3, unidades_por_pacote: 30,
    }));
  });

  it('preserva quantidades confirmadas de notas por peso e não infere pacotes antigos', () => {
    const { fixture, nota } = criar({
      unidade_original: 'KG', quantidade: '0.350', quantidade_confirmada: '30', revisado: true,
      apresentacao: { id: 'ap', produto, marca: null },
    });
    const form = fixture.componentInstance.formularioItem('item')!;
    expect(form.get('quantidade_confirmada')?.value).toBe(30);
    expect(form.get('tipo_quantidade')?.value).toBe('unidades');
    fixture.componentInstance.editarItem(nota.itens[0]);
    selecionar(fixture, nota);
    expect(form.get('quantidade_confirmada')?.value).toBe(30);
  });

  it('ao editar outro item, restaura e bloqueia o formulário anterior', () => {
    const { fixture, nota } = criar({
      apresentacao: { id: 'ap', produto, marca: null }, revisado: true,
      quantidade_confirmada: '60', quantidade_pacotes: '2', unidades_por_pacote: '30',
    });
    const primeiro = nota.itens[0];
    const segundo = { ...primeiro, id: 'segundo', numero: 2 };
    nota.itens.push(segundo);
    fixture.componentInstance.carregar();
    const form = fixture.componentInstance.formularioItem('item')!;
    fixture.componentInstance.editarItem(primeiro);
    form.patchValue({ quantidade_confirmada: 3 });
    fixture.componentInstance.editarItem(segundo);
    expect(form.get('quantidade_confirmada')?.value).toBe(2);
    expect(form.get('tipo_quantidade')?.disabled).toBe(true);
    expect(fixture.componentInstance.formularioItem('segundo')?.get('tipo_quantidade')?.enabled).toBe(true);
  });

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
