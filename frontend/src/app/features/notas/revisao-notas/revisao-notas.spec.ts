import { registerLocaleData } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import localePt from '@angular/common/locales/pt';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of, Subject } from 'rxjs';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiService } from '../../../core/api/api.service';
import { ItemNota, Nota, Produto } from '../../../core/models/api.models';
import { RevisaoNotas } from './revisao-notas';

registerLocaleData(localePt);

describe('metadados na revisão', () => {
  beforeEach(() => {
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  });
  afterEach(() => vi.restoreAllMocks());
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
      listarSabores: () => of([]),
      listarMarcas: () => of([]),
      listarUnidadesMedida: () => of([]),
      listarTags: () => of(nota.itens[0].tags),
      definirTagsItem: vi.fn(() => resposta),
      definirCompetencia: vi.fn(() => resposta),
      definirNotaIgnorada: vi.fn(() => resposta),
      definirItemIgnorado: vi.fn(() => resposta),
      concluirImportacao: vi.fn(() => resposta),
      revisarItem: vi.fn(() => resposta),
      adicionarItemManual: vi.fn(() => resposta),
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

  it('oculta sabor conforme a preferência do produto e volta a exibir ao desmarcar', () => {
    const { fixture, nota } = criar();
    const semSabor = { ...produto, nao_solicitar_sabor: true };
    fixture.componentInstance.produtos.set([semSabor, produtoPeso]);
    selecionar(fixture, nota, semSabor);
    expect(fixture.nativeElement.querySelector('lnf-seletor-sabor')).toBeNull();
    const comSabor = { ...semSabor, nao_solicitar_sabor: false };
    fixture.componentInstance.produtos.set([comSabor, produtoPeso]);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('lnf-seletor-sabor')).not.toBeNull();
  });

  function criarNavegacao(revisado = false, situacao: Nota['situacao'] = 'lida') {
    const contexto = criar({
      revisado, apresentacao: { id: 'ap', produto, marca: null }, quantidade_confirmada: '1',
    }, situacao);
    contexto.nota.itens = ['anterior', 'item', 'automatico', 'ignorado', 'proximo'].map((id, indice) => ({
      ...contexto.nota.itens[0], id, numero: indice + 1,
      revisado: id === 'item' && revisado, ignorado: id === 'ignorado',
    }));
    contexto.nota.quantidade_itens = contexto.nota.itens.length;
    contexto.fixture.componentInstance.carregar();
    contexto.fixture.detectChanges();
    const cartoes = contexto.fixture.nativeElement.querySelectorAll('[data-item-id]') as NodeListOf<HTMLElement>;
    cartoes.forEach((cartao, indice) => {
      vi.spyOn(cartao, 'getBoundingClientRect').mockReturnValue({ top: (indice + 1) * 200 } as DOMRect);
    });
    return contexto;
  }

  function criarManual() {
    const contexto = criar({
      descricao_original: 'Areia gatos', quantidade: '1', unidade_original: 'UN',
      quantidade_confirmada: '1', valor_unitario: '60.00', valor_total: '60.00',
      revisado: true, apresentacao: { id: 'ap', produto, marca: null },
    }, 'importada');
    contexto.nota.origem = 'manual';
    contexto.fixture.componentInstance.carregar();
    contexto.fixture.detectChanges();
    return contexto;
  }

  it('mantém Adicionar item após concluir e abre um cartão com foco no produto', async () => {
    const { fixture, nota } = criarManual();
    const componente = fixture.componentInstance;
    const botao = [...fixture.nativeElement.querySelectorAll('button')].find(
      (atual: any) => atual.textContent.trim() === 'Adicionar item',
    ) as HTMLButtonElement;
    expect(botao.disabled).toBe(false);
    expect(fixture.nativeElement.querySelector('[role=progressbar]')).toBeNull();
    botao.click();
    fixture.detectChanges();
    await fixture.whenStable();
    const novo = componente.novoItem()!;
    const cartao = fixture.nativeElement.querySelector('[data-item-id="novo-item-manual"]');
    expect(cartao).not.toBeNull();
    expect(cartao.classList.contains('border-secondary')).toBe(true);
    expect(cartao.querySelector('form button')).toBe(document.activeElement);
    expect(cartao.querySelector('lnf-seletor-tags')).toBeNull();
    expect(cartao.textContent).not.toContain('Ignorar item');
    expect(componente.formularioItem(novo.id)?.get('quantidade_confirmada')?.value).toBe(1);
    expect(componente.formularioItem(novo.id)?.get('valor_total')?.value).toBeNull();
    componente.adicionarItem();
    expect(componente.itensExibidos()).toHaveLength(2);
    expect(nota.itens).toHaveLength(1);
    componente.cancelarEdicao(novo);
    fixture.detectChanges();
    expect(componente.novoItem()).toBeNull();
    expect(componente.itensExibidos()).toHaveLength(1);
    expect(botao.disabled).toBe(false);
  });

  it('valida e salva novo item na compra concluída uma vez e permite adicionar outro', () => {
    const { fixture, nota, api, resposta } = criarManual();
    const componente = fixture.componentInstance;
    componente.adicionarItem();
    const novo = componente.novoItem()!;
    componente.salvarItem(novo);
    expect(api.adicionarItemManual).not.toHaveBeenCalled();
    componente.itemModal.set(novo);
    componente.selecionarProduto(produto);
    const form = componente.formularioItem(novo.id)!;
    form.patchValue({ quantidade_confirmada: 3, tipo_valor: 'unitario', valor_total: 2.50 });
    componente.salvarItem(novo);
    componente.salvarItem(novo);
    expect(api.revisarItem).not.toHaveBeenCalled();
    expect(api.adicionarItemManual).toHaveBeenCalledExactlyOnceWith(nota.chave, {
      produto_id: produto.id, quantidade_confirmada: 3,
      quantidade_pacotes: null, unidades_por_pacote: null, sabor_id: null, variacao_id: null, valor_unitario: '2.50',
    });
    const salvo: ItemNota = {
      ...novo, id: 'salvo', quantidade: '3', quantidade_confirmada: '3',
      valor_total: '7.50', valor_unitario: '2.50', revisado: true,
      apresentacao: { id: 'nova-ap', produto, marca: null },
    };
    resposta.next({ ...nota, itens: [...nota.itens, salvo], quantidade_itens: 2, valor_total: '17.50', valor_a_pagar: '17.50' });
    fixture.detectChanges();
    expect(componente.novoItem()).toBeNull();
    expect(componente.nota()?.valor_total).toBe('17.50');
    expect(componente.nota()?.situacao).toBe('importada');
    expect(componente.itensExibidos()).toHaveLength(2);
    componente.adicionarItem();
    expect(componente.novoItem()?.numero).toBe(3);
    expect(componente.itensExibidos()).toHaveLength(3);
  });

  it('preserva o novo item quando o servidor falha', () => {
    const { fixture, api, resposta } = criarManual();
    const componente = fixture.componentInstance;
    componente.adicionarItem();
    const novo = componente.novoItem()!;
    componente.itemModal.set(novo);
    componente.selecionarProduto(produtoPeso);
    const form = componente.formularioItem(novo.id)!;
    form.patchValue({ quantidade_confirmada: 2.5, valor_total: 12.34 });
    componente.salvarItem(novo);
    expect(api.adicionarItemManual).toHaveBeenCalledOnce();
    resposta.error(new HttpErrorResponse({ status: 500 }));
    expect(componente.itemSalvando()).toBeNull();
    expect(componente.novoItem()).toBe(novo);
    expect(form.getRawValue()).toMatchObject({
      produto_id: produtoPeso.id, quantidade_confirmada: 2.5, valor_total: 12.34,
    });
    expect(componente.erro()).toBeTruthy();
  });

  it('preserva o formulário do novo item ao atualizar metadados', () => {
    const { fixture, nota, resposta } = criarManual();
    const componente = fixture.componentInstance;
    componente.adicionarItem();
    const novo = componente.novoItem()!;
    const form = componente.formularioItem(novo.id)!;
    form.patchValue({ produto_id: produto.id, valor_total: 15 });
    componente.definirCompetencia({ target: { checked: true } } as unknown as Event);
    resposta.next({ ...nota, considerar_proximo_mes: true });
    expect(componente.novoItem()).toBe(novo);
    expect(componente.formularioItem(novo.id)).toBe(form);
    expect(form.get('valor_total')?.value).toBe(15);
  });

  it('não adiciona itens a notas fiscais ou compras ignoradas', () => {
    const { fixture } = criar();
    const componente = fixture.componentInstance;
    componente.adicionarItem();
    expect(componente.novoItem()).toBeNull();
    expect(fixture.nativeElement.textContent).not.toContain('Adicionar item');
    componente.nota.update((nota) => nota ? { ...nota, origem: 'manual', situacao: 'importada', ignorada: true } : null);
    componente.adicionarItem();
    expect(componente.novoItem()).toBeNull();
  });

  it('atualiza o cabeçalho manual durante a edição e restaura ao cancelar', () => {
    const { fixture, nota } = criarManual();
    const componente = fixture.componentInstance;
    const item = nota.itens[0];
    componente.editarItem(item);
    const form = componente.formularioItem(item.id)!;
    expect(form.get('valor_total')?.enabled).toBe(true);
    expect(form.get('valor_total')?.value).toBe(60);
    form.patchValue({ quantidade_confirmada: 5 });
    selecionar(fixture, nota, produtoPeso);
    expect(form.get('quantidade_confirmada')?.value).toBe(5);
    form.patchValue({ valor_total: 75 });
    fixture.detectChanges();
    const cartao = fixture.nativeElement.querySelector('article') as HTMLElement;
    expect(cartao.querySelector('h3')?.textContent).toBe('Farinha');
    const resumo = cartao.querySelector('p')!.textContent!;
    expect(resumo).toContain('5 G');
    expect(resumo).toContain('15,00');
    expect(resumo).toContain('75,00');
    expect(resumo).not.toContain('1 UN');
    componente.cancelarEdicao(item);
    fixture.detectChanges();
    expect(cartao.querySelector('h3')?.textContent).toBe(produto.nome);
    expect(cartao.querySelector('p')?.textContent).toContain('1 UN');
    expect(form.get('valor_total')?.value).toBe(60);
    expect(form.get('valor_total')?.disabled).toBe(true);
  });

  it('usa os dados confirmados em compras manuais já ajustadas anteriormente', () => {
    const { fixture, nota } = criarManual();
    nota.itens[0] = {
      ...nota.itens[0], apresentacao: { id: 'ap', produto: produtoPeso, marca: null },
      quantidade_confirmada: '5',
    };
    fixture.componentInstance.carregar();
    fixture.detectChanges();
    const cartao = fixture.nativeElement.querySelector('article') as HTMLElement;
    expect(cartao.querySelector('h3')?.textContent).toBe('Farinha');
    expect(cartao.querySelector('p')?.textContent).toContain('5 G');
    expect(cartao.querySelector('p')?.textContent).toContain('12,00');
    expect(cartao.textContent).not.toContain('Areia gatos');
  });

  it('salva o valor manual e mantém o resumo atualizado após a resposta', () => {
    const { fixture, nota, resposta, api } = criarManual();
    const componente = fixture.componentInstance;
    const item = nota.itens[0];
    componente.editarItem(item);
    const form = selecionar(fixture, nota, produtoPeso);
    form.patchValue({ quantidade_confirmada: 5, valor_total: 75 });
    componente.salvarItem(item);
    expect(api.revisarItem).toHaveBeenCalledWith(nota.chave, item.id, {
      produto_id: produtoPeso.id, quantidade_confirmada: 5,
      quantidade_pacotes: null, unidades_por_pacote: null, sabor_id: null, variacao_id: null, valor_total: '75.00',
    });
    resposta.next({
      ...nota, valor_total: '75.00', valor_a_pagar: '75.00',
      itens: [{ ...item, descricao_original: 'Farinha', quantidade: '5', unidade_original: 'G',
        quantidade_confirmada: '5', valor_total: '75.00', valor_unitario: '15.000000',
        apresentacao: { id: 'ap', produto: produtoPeso, marca: null } }],
    });
    fixture.detectChanges();
    const cartao = fixture.nativeElement.querySelector('article') as HTMLElement;
    expect(cartao.querySelector('h3')?.textContent).toBe('Farinha');
    expect(cartao.querySelector('p')?.textContent).toContain('5 G');
    expect(cartao.querySelector('p')?.textContent).toContain('75,00');
    expect(componente.formularioItem(item.id)?.get('valor_total')?.disabled).toBe(true);
    expect(componente.nota()?.valor_a_pagar).toBe('75.00');
  });

  it('mostra a quantidade total e o preço por unidade ao editar pacotes', () => {
    const { fixture, nota } = criarManual();
    const componente = fixture.componentInstance;
    componente.editarItem(nota.itens[0]);
    componente.formularioItem(nota.itens[0].id)!.patchValue({
      tipo_quantidade: 'pacotes', quantidade_confirmada: 2, unidades_por_pacote: 6,
    });
    fixture.detectChanges();
    const resumo = fixture.nativeElement.querySelector('article p').textContent;
    expect(resumo).toContain('12 UN');
    expect(resumo).toContain('5,00');
    expect(resumo).toContain('60,00');
  });

  it('alterna entre valor total e unitário na edição sem modificar o número informado', () => {
    const { fixture, nota, api } = criarManual();
    const componente = fixture.componentInstance;
    componente.editarItem(nota.itens[0]);
    const form = componente.formularioItem(nota.itens[0].id)!;
    form.patchValue({ quantidade_confirmada: 5, valor_total: 15 });
    fixture.detectChanges();
    const seletor = fixture.nativeElement.querySelector('[formControlName="tipo_valor"]') as HTMLSelectElement;
    expect(seletor.disabled).toBe(false);
    seletor.value = 'unitario';
    seletor.dispatchEvent(new Event('change', { bubbles: true }));
    fixture.detectChanges();
    expect(form.get('valor_total')?.value).toBe(15);
    expect(componente.resumoItem(nota.itens[0])).toMatchObject({ valor_unitario: 15, valor_total: 75 });
    componente.salvarItem(nota.itens[0]);
    expect(api.revisarItem).toHaveBeenCalledWith(nota.chave, nota.itens[0].id, {
      produto_id: produto.id, quantidade_confirmada: 5, quantidade_pacotes: null,
      unidades_por_pacote: null, sabor_id: null, variacao_id: null, valor_unitario: '15.00',
    });
  });

  it('restaura valor e tipo ao cancelar a edição e preserva o preço unitário salvo', () => {
    const { fixture, nota } = criarManual();
    const componente = fixture.componentInstance;
    const item = nota.itens[0];
    componente.editarItem(item);
    componente.formularioItem(item.id)!.patchValue({ tipo_valor: 'unitario', valor_total: 5 });
    componente.cancelarEdicao(item);
    expect(componente.formularioItem(item.id)!.getRawValue()).toMatchObject({ tipo_valor: 'total', valor_total: 60 });
    expect(componente.formularioItem(item.id)!.get('tipo_valor')?.disabled).toBe(true);
    Object.assign(item, { quantidade: '0.5', quantidade_confirmada: '0.5', valor_total: '0.15',
      valor_unitario: '0.29', apresentacao: { id: 'ap', produto: produtoPeso, marca: null } });
    componente.carregar();
    fixture.detectChanges();
    expect(componente.resumoItem(item).valor_unitario).toBe(0.29);
    expect(componente.resumoItem(item).valor_total).toBe(0.15);
  });

  it('valida o valor manual antes de enviar os ajustes', () => {
    const { fixture, nota, api } = criarManual();
    const componente = fixture.componentInstance;
    componente.editarItem(nota.itens[0]);
    const form = componente.formularioItem(nota.itens[0].id)!;
    for (const valor of [null, -1, 1.001]) {
      form.patchValue({ valor_total: valor });
      componente.salvarItem(nota.itens[0]);
    }
    expect(api.revisarItem).not.toHaveBeenCalled();
    form.patchValue({ valor_total: 0 });
    componente.salvarItem(nota.itens[0]);
    expect(api.revisarItem).toHaveBeenCalledWith(nota.chave, nota.itens[0].id, expect.objectContaining({ valor_total: '0.00' }));
  });

  it('preserva o cabeçalho fiscal e não oferece edição de valor em notas importadas', () => {
    const { fixture, nota, api } = criar({
      revisado: true, apresentacao: { id: 'ap', produto, marca: null }, quantidade_confirmada: '1',
    }, 'importada');
    fixture.componentInstance.editarItem(nota.itens[0]);
    const form = selecionar(fixture, nota, produtoPeso);
    form.patchValue({ quantidade_confirmada: 5 });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('article h3').textContent).toBe('Produto');
    expect(fixture.nativeElement.querySelector('article p').textContent).toContain('1 UN');
    expect(fixture.nativeElement.querySelector('[formControlName="valor_total"]')).toBeNull();
    expect(form.get('valor_total')?.disabled).toBe(true);
    fixture.componentInstance.salvarItem(nota.itens[0]);
    expect(api.revisarItem).toHaveBeenCalledWith(nota.chave, nota.itens[0].id, {
      produto_id: produtoPeso.id, quantidade_confirmada: 5, quantidade_pacotes: null,
      unidades_por_pacote: null, sabor_id: null, variacao_id: null,
    });
  });

  it('exibe a compra manual com borda cinza e sem dados ou link fiscal', () => {
    const { fixture, nota } = criar({
      revisado: true, apresentacao: { id: 'ap', produto, marca: null }, quantidade_confirmada: '1',
    }, 'importada');
    Object.assign(nota, {
      origem: 'manual', chave: null, numero: null, serie: null, url_origem: null,
      estabelecimento: { id: 'loja', nome_exibicao: 'Feira', apelido: 'Feira', cnpj: null, razao_social: null },
    });
    fixture.componentInstance.carregar();
    fixture.detectChanges();
    const cartao = fixture.nativeElement.querySelector('article');
    expect(cartao.classList.contains('border-secondary')).toBe(true);
    expect(cartao.classList.contains('border-success')).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('Compra manual · Concluída');
    expect(fixture.nativeElement.textContent).not.toContain('NFC-e');
    expect(fixture.nativeElement.textContent).not.toContain('Ver nota original na SEFAZ');
  });

  it.each([false, true])('avança após salvar item (já revisado: %s), pulando automáticos e ignorados', async (revisado) => {
    const { fixture, nota, resposta } = criarNavegacao(revisado);
    const item = nota.itens[1];
    if (revisado) fixture.componentInstance.editarItem(item);
    fixture.componentInstance.salvarItem(item);
    expect(window.scrollTo).not.toHaveBeenCalled();
    resposta.next({ ...nota, itens: nota.itens.map((atual) => ({
      ...atual, revisado: ['item', 'automatico'].includes(atual.id),
    })) });
    fixture.detectChanges();
    await fixture.whenStable();
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 984, behavior: 'smooth' });
  });

  it('volta à primeira pendência quando não há outra abaixo', async () => {
    const { fixture, nota, resposta } = criarNavegacao();
    fixture.componentInstance.salvarItem(nota.itens[4]);
    resposta.next({ ...nota, itens: nota.itens.map((item) => ({ ...item, revisado: item.id !== 'anterior' })) });
    fixture.detectChanges();
    await fixture.whenStable();
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 184, behavior: 'smooth' });
  });

  it.each([false, true])('vai ao banner ao salvar a última pendência ou ajuste (já revisado: %s)', async (revisado) => {
    const { fixture, nota, resposta } = criarNavegacao(revisado);
    const banner = fixture.nativeElement.querySelector('section.card.mt-4') as HTMLElement;
    vi.spyOn(banner, 'getBoundingClientRect').mockReturnValue({ top: 1400 } as DOMRect);
    const item = nota.itens[1];
    if (revisado) fixture.componentInstance.editarItem(item);
    fixture.componentInstance.salvarItem(item);
    resposta.next({ ...nota, itens: nota.itens.map((atual) => ({ ...atual, revisado: true })) });
    fixture.detectChanges();
    await fixture.whenStable();
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 1384, behavior: 'smooth' });
    expect(fixture.nativeElement.querySelector('button[aria-label="Ir para o primeiro item não revisado"]')).toBeNull();
  });

  it('mantém a posição ao editar uma nota importada', async () => {
    const { fixture, nota, resposta } = criarNavegacao(true, 'importada');
    fixture.componentInstance.editarItem(nota.itens[1]);
    fixture.componentInstance.salvarItem(nota.itens[1]);
    resposta.next(nota);
    fixture.detectChanges();
    await fixture.whenStable();
    expect(window.scrollTo).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('button[aria-label="Ir para o primeiro item não revisado"]')).toBeNull();
  });

  it('atalho volta à primeira pendência abaixo do cabeçalho e respeita movimento reduzido', async () => {
    const { fixture } = criarNavegacao();
    const cabecalho = document.createElement('header');
    cabecalho.className = 'sticky-top';
    document.body.append(cabecalho);
    vi.spyOn(cabecalho, 'getBoundingClientRect').mockReturnValue({ height: 80 } as DOMRect);
    const mediaAnterior = window.matchMedia;
    window.matchMedia = vi.fn().mockReturnValue({ matches: true });
    try {
      fixture.nativeElement.querySelector('button[aria-label="Ir para o primeiro item não revisado"]').click();
      fixture.detectChanges();
      await fixture.whenStable();
      expect(window.scrollTo).toHaveBeenCalledWith({ top: 104, behavior: 'instant' });
    } finally {
      cabecalho.remove();
      window.matchMedia = mediaAnterior;
    }
  });

  it.each(['invalido', 'erro'])('não rola quando o salvamento falha: %s', async (cenario) => {
    const { fixture, nota, resposta, api } = criarNavegacao();
    if (cenario === 'invalido') fixture.componentInstance.formularioItem('item')!.patchValue({ produto_id: '' });
    fixture.componentInstance.salvarItem(nota.itens[1]);
    if (cenario === 'erro') resposta.error(new Error('Falha ao salvar'));
    else expect(api.revisarItem).not.toHaveBeenCalled();
    fixture.detectChanges();
    await fixture.whenStable();
    expect(window.scrollTo).not.toHaveBeenCalled();
  });

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
      quantidade_pacotes: quantidade, unidades_por_pacote: 30, sabor_id: null, variacao_id: null,
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
      quantidade_pacotes: null, unidades_por_pacote: null, sabor_id: null, variacao_id: null,
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
