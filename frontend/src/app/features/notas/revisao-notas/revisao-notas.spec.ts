import { registerLocaleData } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
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
      ignorada: situacao === 'ignorada',
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
          ignorado: false,
          tags: [{ id: 'tag', nome: 'Festa' }],
          ...item,
        },
      ],
    };
    const resposta = new Subject<Nota>();
    const api = {
      obterNota: () => of(nota),
      aplicarClassificacoesAutomaticas: vi.fn(() => of(nota)),
      listarProdutos: () => of([produto, produtoPeso]),
      listarCategorias: () => of([]),
      listarMarcas: () => of([]),
      listarUnidadesMedida: () => of([]),
      listarTags: () => of(nota.itens[0].tags),
      definirTagsItem: vi.fn(() => resposta),
      definirCompetencia: vi.fn(() => resposta),
      definirNotaIgnorada: vi.fn(() => resposta),
      definirItemIgnorado: vi.fn(() => resposta),
      concluirImportacao: vi.fn(() => resposta),
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

  it.each(['KG', 'G'])('reconhece produto em %s e sugere 1 sem confirmar automaticamente', (unidade) => {
    const { fixture, nota, api, resposta } = criar({
      apresentacao: { id: 'ap', produto, marca: null },
      unidade_original: unidade, quantidade: '0.148',
    });
    expect(api.aplicarClassificacoesAutomaticas).toHaveBeenCalledWith(nota.chave);
    const form = fixture.componentInstance.formularioItem('item')!;
    expect(form.get('produto_id')?.value).toBe(produto.id);
    expect(form.get('quantidade_confirmada')?.value).toBe(1);
    expect(nota.itens[0].quantidade_confirmada).toBeNull();
    expect(api.revisarItem).not.toHaveBeenCalled();
    expect(fixture.componentInstance.podeImportar(nota)).toBe(false);
    expect(fixture.nativeElement.textContent).toContain(
      'Produto reconhecido pelo histórico. Confira a quantidade de unidades; a nota informa peso.',
    );
    for (const invalida of [0, -1, 1.5]) {
      form.patchValue({ quantidade_confirmada: invalida });
      fixture.componentInstance.salvarItem(nota.itens[0]);
      expect(api.revisarItem).not.toHaveBeenCalled();
    }
    form.patchValue({ quantidade_confirmada: 2 });
    fixture.componentInstance.salvarItem(nota.itens[0]);
    expect(api.revisarItem).toHaveBeenCalledWith(nota.chave, 'item', expect.objectContaining({
      produto_id: produto.id, quantidade_confirmada: 2,
    }));
    resposta.next({ ...nota, itens: [{ ...nota.itens[0], revisado: true, quantidade_confirmada: '2' }] });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('Produto reconhecido pelo histórico.');
    expect(fixture.componentInstance.podeImportar(fixture.componentInstance.nota()!)).toBe(true);
  });

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
    const campo = fixture.nativeElement.querySelector('#considerar-proximo-mes') as HTMLInputElement;
    campo.checked = true;
    campo.dispatchEvent(new Event('change'));
    expect(api.definirCompetencia).toHaveBeenCalledWith('1'.repeat(44), true);
    resposta.error(new Error('Falha'));
    fixture.detectChanges();
    expect(campo.checked).toBe(false);
    expect(fixture.componentInstance.nota()?.considerar_proximo_mes).toBe(false);
  });

  function marcarIgnorar(fixture: ReturnType<typeof criar>['fixture'], item = false, marcado = true) {
    const campos = fixture.nativeElement.querySelectorAll('input[type=checkbox]');
    const campo = campos[item ? 2 : 0] as HTMLInputElement;
    campo.checked = marcado;
    campo.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    return campo;
  }

  it('confirma nota somente no modal e preserva o formulário em edição', () => {
    const { fixture, nota, api, resposta } = criar();
    const form = fixture.componentInstance.formularioItem('item')!;
    form.patchValue({ produto_id: 'em-edicao', quantidade_confirmada: 3 });
    const campo = marcarIgnorar(fixture);
    expect(campo.checked).toBe(false);
    expect(api.definirNotaIgnorada).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('[role=dialog]').textContent).toContain('NFC-e 1');
    fixture.componentInstance.confirmarIgnorar();
    fixture.componentInstance.confirmarIgnorar();
    expect(api.definirNotaIgnorada).toHaveBeenCalledExactlyOnceWith(nota.chave, true);
    resposta.next({ ...nota, ignorada: true, situacao: 'ignorada' });
    fixture.detectChanges();
    expect(campo.checked).toBe(true);
    expect(fixture.nativeElement.querySelector('[role=dialog]')).toBeNull();
    expect(form.get('produto_id')?.value).toBe('em-edicao');
    expect(form.get('quantidade_confirmada')?.value).toBe(3);
  });

  it('cancela a marcação do item sem salvar e devolve foco por Escape', async () => {
    const { fixture, api } = criar();
    const campo = marcarIgnorar(fixture, true);
    await fixture.whenStable();
    const dialogo = fixture.nativeElement.querySelector('[role=dialog]') as HTMLElement;
    const botoes = dialogo.querySelectorAll('button');
    expect(document.activeElement).toBe(botoes[1]);
    botoes[0].focus();
    botoes[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true }));
    expect(document.activeElement).toBe(botoes[2]);
    botoes[2].dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true }));
    expect(document.activeElement).toBe(botoes[0]);
    dialogo.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=dialog]')).toBeNull();
    expect(api.definirItemIgnorado).not.toHaveBeenCalled();
    expect(campo.checked).toBe(false);
    expect(document.activeElement).toBe(campo);
  });

  it('confirma item e bloqueia importação quando todos os itens estão ignorados', () => {
    const { fixture, nota, api, resposta } = criar();
    marcarIgnorar(fixture, true);
    fixture.componentInstance.confirmarIgnorar();
    expect(api.definirItemIgnorado).toHaveBeenCalledWith(nota.chave, 'item', true);
    resposta.next({ ...nota, itens: [{ ...nota.itens[0], ignorado: true }] });
    fixture.detectChanges();
    const atual = fixture.componentInstance.nota()!;
    expect(fixture.componentInstance.itensPendentes(atual)).toBe(0);
    expect(fixture.componentInstance.podeImportar(atual)).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('pelo menos um item não ignorado');
    fixture.componentInstance.concluirImportacao();
    expect(api.concluirImportacao).not.toHaveBeenCalled();
  });

  it('mantém modal e checkbox salvo após falha na confirmação', () => {
    const { fixture, resposta } = criar();
    const campo = marcarIgnorar(fixture, true);
    fixture.componentInstance.confirmarIgnorar();
    resposta.error(new HttpErrorResponse({ status: 500, error: { mensagem: 'Falha ao salvar' } }));
    fixture.detectChanges();
    expect(campo.checked).toBe(false);
    expect(fixture.nativeElement.querySelector('[role=dialog]').textContent).toContain('Falha ao salvar');
    expect(fixture.componentInstance.salvandoMetadados()).toBe(false);
  });

  it('desmarca sem modal e preserva ignorado se faltar revisão na nota importada', () => {
    const { fixture, nota, api, resposta } = criar({ ignorado: true }, 'importada');
    fixture.componentInstance.editarItem(nota.itens[0]);
    fixture.detectChanges();
    const campo = marcarIgnorar(fixture, true, false);
    expect(api.definirItemIgnorado).toHaveBeenCalledWith(nota.chave, 'item', false);
    expect(fixture.nativeElement.querySelector('[role=dialog]')).toBeNull();
    resposta.error(new HttpErrorResponse({ status: 409, error: { mensagem: 'Revise e confirme o item antes de incluí-lo novamente nos relatórios.' } }));
    fixture.detectChanges();
    expect(campo.checked).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Revise e confirme o item');
    expect(fixture.componentInstance.itemEstaEmEdicao(nota.itens[0])).toBe(true);
  });

  it('só permite ignorar um item confirmado após entrar na edição e fecha ao confirmar', async () => {
    const { fixture, nota, api, resposta } = criar({
      revisado: true, apresentacao: { id: 'ap', produto, marca: null }, quantidade_confirmada: '1',
    });
    const campo = marcarIgnorar(fixture, true);
    expect(campo.disabled).toBe(true);
    expect(campo.checked).toBe(false);
    expect(fixture.nativeElement.querySelector('[role=dialog]')).toBeNull();
    expect(api.definirItemIgnorado).not.toHaveBeenCalled();
    fixture.nativeElement.querySelector('button[aria-label="Editar item"]').click();
    fixture.detectChanges();
    expect(campo.disabled).toBe(false);
    marcarIgnorar(fixture, true);
    fixture.componentInstance.confirmarIgnorar();
    resposta.next({ ...nota, itens: [{ ...nota.itens[0], ignorado: true }] });
    fixture.detectChanges();
    expect(campo.checked).toBe(true);
    expect(campo.disabled).toBe(true);
    expect(fixture.componentInstance.itemEditando()).toBeNull();
    expect(fixture.componentInstance.formularioItem('item')?.get('quantidade_confirmada')?.disabled).toBe(true);
    expect(fixture.nativeElement.querySelector('form button[type=submit]')).toBeNull();
    expect(fixture.nativeElement.querySelector('button[aria-label="Editar item"]')).not.toBeNull();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(document.activeElement).toBe(fixture.nativeElement.querySelector('button[aria-label="Editar item"]'));
  });

  it('mostra um item ignorado sem revisão como concluído e permite reabrir e cancelar', () => {
    const { fixture, nota } = criar({ ignorado: true });
    const item = nota.itens[0];
    const form = fixture.componentInstance.formularioItem(item.id)!;
    form.markAllAsTouched();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.is-invalid')).toBeNull();
    expect(fixture.componentInstance.itemConcluido(item)).toBe(true);
    expect(fixture.componentInstance.itemEstaEmEdicao(item)).toBe(false);
    expect(form.get('quantidade_confirmada')?.disabled).toBe(true);
    expect(fixture.nativeElement.querySelector('form button[type=submit]')).toBeNull();
    fixture.componentInstance.editarItem(item);
    fixture.detectChanges();
    expect(fixture.componentInstance.itemEstaEmEdicao(item)).toBe(true);
    expect(form.get('quantidade_confirmada')?.enabled).toBe(true);
    fixture.componentInstance.cancelarEdicao(item);
    fixture.detectChanges();
    expect(fixture.componentInstance.itemEstaEmEdicao(item)).toBe(false);
    expect(form.get('quantidade_confirmada')?.disabled).toBe(true);
  });

  it('bloqueia todos os campos de uma nota ignorada e mantém a opção de restaurá-la', async () => {
    const { fixture, nota, api } = criar({
      apresentacao: { id: 'ap', produto, marca: null }, quantidade_confirmada: '1',
    }, 'ignorada');
    await fixture.whenStable();
    fixture.detectChanges();
    const campos = fixture.nativeElement.querySelectorAll('input[type=checkbox]') as NodeListOf<HTMLInputElement>;
    expect(campos[0].disabled).toBe(false);
    expect(campos[0].checked).toBe(true);
    expect(campos[1].disabled).toBe(true);
    expect(campos[2].disabled).toBe(true);
    for (const campo of fixture.nativeElement.querySelectorAll('input:not([type=checkbox]), form button.form-control')) {
      expect(campo.disabled, campo.outerHTML).toBe(true);
    }
    expect(fixture.nativeElement.querySelector('button[aria-label="Editar estabelecimento"]').disabled).toBe(true);
    expect(fixture.nativeElement.querySelector('button[aria-label="Editar item"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('form button[type=submit]')).toBeNull();
    expect(fixture.nativeElement.querySelector('[role=progressbar]')).toBeNull();
    expect(fixture.nativeElement.textContent).not.toContain('Requer atenção');
    expect(fixture.nativeElement.textContent).not.toContain('Concluir importação');
    fixture.componentInstance.editarItem(nota.itens[0]);
    fixture.componentInstance.adicionarTag('Nova');
    fixture.componentInstance.removerTag(nota.itens[0], 'tag');
    fixture.componentInstance.abrirEdicaoEstabelecimento();
    fixture.componentInstance.concluirImportacao();
    expect(fixture.componentInstance.itemEditando()).toBeNull();
    expect(fixture.componentInstance.modalEstabelecimentoAberto()).toBe(false);
    expect(api.definirTagsItem).not.toHaveBeenCalled();
    expect(api.concluirImportacao).not.toHaveBeenCalled();
  });

  it('restaura a situação e desbloqueia itens pendentes ao desmarcar a nota ignorada', () => {
    const { fixture, nota, api, resposta } = criar({}, 'ignorada');
    marcarIgnorar(fixture, false, false);
    expect(api.definirNotaIgnorada).toHaveBeenCalledWith(nota.chave, false);
    resposta.next({ ...nota, ignorada: false, situacao: 'em_revisao' });
    fixture.detectChanges();
    expect(fixture.componentInstance.nota()?.situacao).toBe('em_revisao');
    expect(fixture.componentInstance.itemEstaEmEdicao(nota.itens[0])).toBe(true);
    expect(fixture.componentInstance.formularioItem('item')?.get('quantidade_confirmada')?.enabled).toBe(true);
    expect(fixture.nativeElement.querySelector('form button[type=submit]')).not.toBeNull();
  });
});
