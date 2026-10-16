import { registerLocaleData } from '@angular/common';
import localePt from '@angular/common/locales/pt';
import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, Subject } from 'rxjs';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiService } from '../../../core/api/api.service';
import {
  CompraManualRequest,
  Estabelecimento,
  Nota,
  Produto,
} from '../../../core/models/api.models';
import { CompraManual, dataLocalHoje } from './compra-manual';

registerLocaleData(localePt);

describe('compra manual', () => {
  const loja: Estabelecimento = {
    id: 'loja',
    cnpj: null,
    razao_social: null,
    apelido: 'Feira',
    nome_exibicao: 'Feira',
  };
  const produto: Produto = {
    id: 'banana',
    nome: 'Banana',
    categoria: { id: 'cat', nome: 'Alimentação' },
    nao_solicitar_marca: true,
    tratar_apenas_como_unidades: false,
    contem_variacoes: false,
    unidade_medida: 'KG',
  };
  const unidades: Produto = {
    ...produto,
    id: 'ovos',
    nome: 'Ovos',
    tratar_apenas_como_unidades: true,
    unidade_medida: null,
  };

  beforeEach(() => {
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: vi.fn(),
    });
  });
  afterEach(() => {
    document.body.classList.remove('modal-open');
    vi.restoreAllMocks();
  });

  function criar() {
    const resposta = new Subject<Nota>();
    const api = {
      listarEstabelecimentos: () => of([loja]),
      listarProdutos: () => of([produto, unidades]),
      listarCategorias: () => of([produto.categoria]),
      listarMarcas: () => of([]),
      listarUnidadesMedida: () => of([{ codigo: 'KG', descricao: 'Quilograma' }]),
      criarCompraManual: vi.fn((_compra: CompraManualRequest) => resposta),
    };
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: ApiService, useValue: api }],
    });
    const navegar = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    const fixture = TestBed.createComponent(CompraManual);
    fixture.detectChanges();
    const componente = fixture.componentInstance;
    return { fixture, componente, api, resposta, navegar };
  }

  function preencher(contexto: ReturnType<typeof criar>, escolhido = produto) {
    contexto.componente.selecionarEstabelecimento(loja);
    contexto.componente.abrirSeletor('produto', 0);
    contexto.componente.selecionarProduto(escolhido);
    contexto.componente.itens.at(0).patchValue({ quantidade_confirmada: 1.5, valor_total: 12.34 });
    contexto.fixture.detectChanges();
  }

  it('usa a data brasileira mesmo quando UTC já mudou de dia', () => {
    expect(dataLocalHoje(new Date('2026-10-02T01:00:00Z'))).toBe('2026-10-01');
  });

  it('inicia com um item cinza e os dois botões abaixo da lista', () => {
    const { fixture, componente } = criar();
    expect(componente.itens.length).toBe(1);
    expect(componente.formulario.controls.data.value).toBe(dataLocalHoje());
    const cartao = fixture.nativeElement.querySelector('article');
    expect(cartao.classList.contains('border-secondary')).toBe(true);
    expect(cartao.classList.contains('border-warning')).toBe(false);
    expect(cartao.classList.contains('border-success')).toBe(false);
    const botoes = fixture.nativeElement.querySelectorAll('fieldset > div:last-child button');
    expect(Array.from(botoes, (botao: any) => botao.textContent.trim())).toEqual([
      'Adicionar item',
      'Concluir',
    ]);
  });

  it('adiciona, mantém preenchimento, foca o novo produto e preserva um item', async () => {
    const contexto = criar();
    preencher(contexto);
    contexto.componente.adicionarItem();
    contexto.fixture.detectChanges();
    await contexto.fixture.whenStable();
    expect(contexto.componente.itens.length).toBe(2);
    expect(contexto.componente.itens.at(0).get('valor_total')?.value).toBe(12.34);
    const botoes = contexto.fixture.nativeElement.querySelectorAll('[data-produto]');
    expect(document.activeElement).toBe(botoes[1]);
    contexto.componente.removerItem(1);
    contexto.componente.removerItem(0);
    expect(contexto.componente.itens.length).toBe(1);
  });

  it('exige estabelecimento, produto e valores válidos antes de salvar', () => {
    const contexto = criar();
    contexto.componente.concluir();
    expect(contexto.api.criarCompraManual).not.toHaveBeenCalled();
    expect(contexto.componente.formulario.controls.estabelecimento_id.touched).toBe(true);
    preencher(contexto);
    contexto.componente.itens.at(0).patchValue({ valor_total: 1.001 });
    contexto.componente.concluir();
    expect(contexto.api.criarCompraManual).not.toHaveBeenCalled();
    expect(contexto.componente.itens.at(0).get('valor_total')?.invalid).toBe(true);
  });

  it('calcula os totais, bloqueia envio repetido e navega pelo UUID', () => {
    const contexto = criar();
    preencher(contexto);
    expect(contexto.componente.precoUnitario(contexto.componente.itens.at(0))).toBeCloseTo(
      12.34 / 1.5,
    );
    expect(contexto.componente.total()).toBe(12.34);
    contexto.componente.concluir();
    contexto.componente.concluir();
    contexto.fixture.detectChanges();
    expect(contexto.api.criarCompraManual).toHaveBeenCalledTimes(1);
    expect(contexto.api.criarCompraManual).toHaveBeenCalledWith({
      estabelecimento_id: 'loja',
      data: dataLocalHoje(),
      itens: [
        {
          produto_id: 'banana',
          marca_id: null,
          variacao_id: null,
          quantidade_confirmada: 1.5,
          quantidade_pacotes: null,
          unidades_por_pacote: null,
          valor_total: '12.34',
        },
      ],
    });
    expect(contexto.fixture.nativeElement.querySelector('fieldset').disabled).toBe(true);
    contexto.resposta.next({ id: 'uuid-compra' } as Nota);
    expect(contexto.navegar).toHaveBeenCalledWith(['/notas', 'uuid-compra', 'revisao']);
  });

  it('permite escolher valor unitário, atualiza o total e envia a escolha', () => {
    const contexto = criar();
    preencher(contexto);
    const form = contexto.componente.itens.at(0);
    form.patchValue({ quantidade_confirmada: 5, valor_total: 15 });
    contexto.fixture.detectChanges();
    const seletor = contexto.fixture.nativeElement.querySelector('[formControlName="tipo_valor"]') as HTMLSelectElement;
    expect(seletor.value).toBe('total');
    seletor.value = 'unitario';
    seletor.dispatchEvent(new Event('change', { bubbles: true }));
    contexto.fixture.detectChanges();
    expect(form.get('valor_total')?.value).toBe(15);
    expect(contexto.componente.total()).toBe(75);
    expect(contexto.fixture.nativeElement.textContent).toContain('Total do item:');
    contexto.componente.concluir();
    expect(contexto.api.criarCompraManual).toHaveBeenCalledWith(expect.objectContaining({
      itens: [expect.objectContaining({ quantidade_confirmada: 5, valor_unitario: '15.00' })],
    }));
    expect(contexto.api.criarCompraManual.mock.calls[0][0].itens[0].valor_total).toBeUndefined();
  });

  it('calcula o preço unitário por unidade mesmo ao informar pacotes', () => {
    const contexto = criar();
    preencher(contexto, unidades);
    const form = contexto.componente.itens.at(0);
    form.patchValue({
      quantidade_confirmada: 2, tipo_quantidade: 'pacotes', unidades_por_pacote: 6,
      tipo_valor: 'unitario', valor_total: 5,
    });
    contexto.fixture.detectChanges();
    expect(contexto.componente.total()).toBe(60);
    expect(contexto.fixture.nativeElement.textContent).toContain('Valor por unidade do produto');
    contexto.componente.concluir();
    expect(contexto.api.criarCompraManual).toHaveBeenCalledWith(expect.objectContaining({
      itens: [expect.objectContaining({ quantidade_confirmada: 12, valor_unitario: '5.00' })],
    }));
  });

  it('não envia um valor total calculado acima do limite', () => {
    const contexto = criar();
    preencher(contexto);
    contexto.componente.itens.at(0).patchValue({
      quantidade_confirmada: 2, tipo_valor: 'unitario', valor_total: 9999999999999.99,
    });
    contexto.componente.concluir();
    expect(contexto.api.criarCompraManual).not.toHaveBeenCalled();
  });

  it('preserva o preenchimento e libera nova tentativa após erro', () => {
    const contexto = criar();
    preencher(contexto);
    contexto.componente.concluir();
    contexto.resposta.error(
      new HttpErrorResponse({
        status: 422,
        error: { mensagem: 'Revise o item.' },
      }),
    );
    contexto.fixture.detectChanges();
    expect(contexto.componente.salvando()).toBe(false);
    expect(contexto.componente.itens.at(0).get('valor_total')?.value).toBe(12.34);
    expect(contexto.componente.estabelecimento()?.id).toBe('loja');
    expect(contexto.componente.erro()).toBeTruthy();
  });

  it('valida unidades inteiras e converte pacotes para a quantidade total', () => {
    const contexto = criar();
    preencher(contexto, unidades);
    contexto.componente.concluir();
    expect(contexto.api.criarCompraManual).not.toHaveBeenCalled();
    contexto.componente.itens.at(0).patchValue({
      quantidade_confirmada: 2,
      tipo_quantidade: 'pacotes',
      unidades_por_pacote: 6,
    });
    contexto.componente.concluir();
    expect(contexto.api.criarCompraManual.mock.calls[0][0].itens[0]).toMatchObject({
      quantidade_confirmada: 12,
      quantidade_pacotes: 2,
      unidades_por_pacote: 6,
    });
  });

  it('exige marca e variação conforme o produto e limpa a seleção ao trocar produto', () => {
    const contexto = criar();
    const variado: Produto = {
      ...produto,
      id: 'iogurte',
      contem_variacoes: true,
      nao_solicitar_marca: false,
    };
    contexto.componente.registrarProduto(variado);
    preencher(contexto, variado);
    const form = contexto.componente.itens.at(0);
    expect(form.get('marca_id')?.invalid).toBe(true);
    expect(form.get('variacao_id')?.invalid).toBe(true);
    form.patchValue({ marca_id: 'marca', variacao_id: 'variacao' });
    contexto.componente.selecionarProduto(produto);
    expect(form.get('marca_id')?.value).toBeNull();
    expect(form.get('variacao_id')?.value).toBeNull();
    expect(form.valid).toBe(true);
  });
});
