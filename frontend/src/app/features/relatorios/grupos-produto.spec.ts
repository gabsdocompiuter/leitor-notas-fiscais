import { registerLocaleData } from '@angular/common';
import pt from '@angular/common/locales/pt';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { afterEach, describe, expect, it } from 'vitest';
import { GruposProduto } from './grupos-produto';
import { AgrupamentoRelatorio } from '../../core/models/api.models';

registerLocaleData(pt);
describe('Agrupamentos de compras', () => {
  const grupos: AgrupamentoRelatorio[] = [
    {
      id: 'marca',
      nome: 'Rodeio',
      quantidade_registros: 2,
      quantidade_comprada: '1.41',
      unidade_quantidade: 'KG',
      total_pago: '57.93',
      media_por_compra: '28.97',
      quantidade_unidades: '3',
    },
    {
      id: null,
      nome: 'Sem marca',
      quantidade_registros: 1,
      quantidade_comprada: '0.8',
      unidade_quantidade: 'KG',
      total_pago: '31.51',
      media_por_compra: '31.51',
      quantidade_unidades: '2',
    },
  ];
  afterEach(() => TestBed.inject(HttpTestingController).verify());
  function criar(flush = true) {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    const fixture = TestBed.createComponent(GruposProduto);
    const http = TestBed.inject(HttpTestingController);
    fixture.componentRef.setInput('mes', '2026-10');
    fixture.componentRef.setInput('categoriaId', 'categoria');
    fixture.componentRef.setInput('produtoId', 'produto');
    fixture.detectChanges();
    const resumos = () => http.expectOne((r) => r.url.endsWith('/mensal/agrupamentos'));
    const compras = () => http.expectOne((r) => r.url.endsWith('/mensal/itens'));
    const inicial = resumos();
    if (flush) {
      inicial.flush(grupos);
      fixture.detectChanges();
    }
    return { fixture, http, resumos, compras, inicial, componente: fixture.componentInstance };
  }
  it('inicia por marca e mostra a média somente para várias compras', () => {
    const { fixture, http, inicial } = criar();
    expect(inicial.request.params.get('agrupador')).toBe('marca');
    const botoes = fixture.nativeElement.querySelectorAll('[data-grupo]');
    expect(botoes[0].textContent).toContain('3x');
    expect(botoes[0].textContent).toContain('1,41 kg');
    expect(botoes[0].textContent).toContain('Média por compra: R$');
    expect(botoes[0].textContent).toContain('28,97');
    expect(botoes[1].textContent).not.toContain('Média por compra');
    expect(botoes[1].textContent).toContain('2x');
    http.expectNone((r) => r.url.endsWith('/mensal/itens'));
  });
  it('filtra o grupo sem marca e mantém detalhes compactos e links das notas', () => {
    const { fixture, compras } = criar();
    fixture.nativeElement.querySelector('[data-grupo="sem_grupo"]').click();
    fixture.detectChanges();
    const pedido = compras();
    expect(pedido.request.params.get('grupo_id')).toBe('sem_grupo');
    expect(pedido.request.params.get('agrupador')).toBe('marca');
    expect(pedido.request.params.get('categoria_id')).toBe('categoria');
    expect(pedido.request.params.get('produto_id')).toBe('produto');
    pedido.flush({
      total: 1,
      itens: [
        {
          id: 'item',
          produto: 'Queijo Mussarela',
          categoria: 'Alimentação',
          quantidade_comprada: '0.8',
          unidade_quantidade: 'KG',
          quantidade_unidades: '2',
          variacao: '400 G',
          estabelecimento: 'Macromix',
          emissao: '2026-10-05',
          valor_pago: '31.51',
          valor_bruto: '31.8',
          desconto_rateado: '0.29',
          tags: [{ id: 'tag', nome: 'Mensal' }],
          considerar_proximo_mes: true,
          chave_nota: 'chave',
          numero_nota: '235852',
        },
      ],
    });
    fixture.detectChanges();
    const lista = fixture.nativeElement.querySelector('lnf-itens-relatorio');
    expect(lista.textContent).toContain('2 unidades');
    expect(lista.textContent).toContain('400 G');
    for (const texto of [
      '0,8 kg',
      'Macromix',
      '05/10/2026',
      'Mensal',
      'mês seguinte',
      'Ver nota 235852',
    ])
      expect(lista.textContent).toContain(texto);
    for (const texto of ['Queijo Mussarela', 'Alimentação', 'Bruto', 'Desconto'])
      expect(lista.textContent).not.toContain(texto);
    expect(lista.querySelector('a').getAttribute('href')).toBe('/notas/chave/revisao');
  });
  it('omite o prefixo quando não há unidades conhecidas sem esconder a quantidade real', () => {
    const { fixture, inicial } = criar(false);
    inicial.flush([{...grupos[0], quantidade_unidades:null}]);
    fixture.detectChanges();
    const resumo = fixture.nativeElement.querySelector('[data-grupo]').textContent;
    expect(resumo).not.toContain('2x');
    expect(resumo).not.toContain('3x');
    expect(resumo).toContain('1,41 kg');
    expect(resumo).toContain('Média por compra');
  });
  it('troca agrupador, cancela consultas, limpa a expansão e mantém foco', () => {
    const { fixture, compras, resumos, componente } = criar();
    componente.alternar(grupos[0]);
    const anterior = compras();
    const variacao = fixture.nativeElement.querySelector('[data-agrupador="variacao"]');
    variacao.focus();
    variacao.click();
    fixture.detectChanges();
    expect(anterior.cancelled).toBe(true);
    expect(componente.expandido()).toBeNull();
    expect(document.activeElement).toBe(variacao);
    const consulta = resumos();
    expect(consulta.request.params.get('agrupador')).toBe('variacao');
    fixture.nativeElement.querySelector('[data-agrupador="estabelecimento"]').click();
    fixture.detectChanges();
    expect(consulta.cancelled).toBe(true);
    resumos().flush([]);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Nenhum grupo encontrado');
  });
  it('pagina 51 grupos sem somar apenas a página e cancela as compras anteriores', () => {
    const { fixture, inicial, compras, componente } = criar(false);
    inicial.flush(Array.from({ length: 51 }, (_, i) => ({ ...grupos[0], id: `grupo-${i}` })));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('[data-grupo]')).toHaveLength(50);
    componente.alternar(componente.grupos()[0]);
    const antigo = compras();
    componente.alternar(componente.grupos()[1]);
    expect(antigo.cancelled).toBe(true);
    compras().flush({ itens: [], total: 51 });
    fixture.detectChanges();
    const proxima = fixture.nativeElement.querySelector('lnf-itens-relatorio button:last-child');
    proxima.focus();
    proxima.click();
    fixture.detectChanges();
    expect(document.activeElement).toBe(
      fixture.nativeElement.querySelector('[data-grupo="grupo-1"]'),
    );
    const pagina = compras();
    expect(pagina.request.params.get('deslocamento')).toBe('50');
    componente.navegar(1);
    expect(pagina.cancelled).toBe(true);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('[data-grupo]')).toHaveLength(1);
    expect(fixture.nativeElement.textContent).toContain('51 grupos');
  });
  it('permite retry de grupos e compras e cancela ao mudar produto ou destruir', () => {
    const { fixture, inicial, resumos, compras, componente } = criar(false);
    inicial.flush({}, { status: 500, statusText: 'Erro' });
    fixture.detectChanges();
    fixture.nativeElement.querySelector('.card-body button').click();
    resumos().flush(grupos);
    fixture.detectChanges();
    componente.alternar(grupos[0]);
    compras().flush({}, { status: 500, statusText: 'Erro' });
    fixture.detectChanges();
    fixture.nativeElement.querySelector('lnf-itens-relatorio button').click();
    const pedido = compras();
    fixture.componentRef.setInput('produtoId', 'outro');
    fixture.detectChanges();
    expect(pedido.cancelled).toBe(true);
    const novo = resumos();
    expect(novo.request.params.get('produto_id')).toBe('outro');
    expect(novo.request.params.get('agrupador')).toBe('marca');
    fixture.destroy();
    expect(novo.cancelled).toBe(true);
  });
});
