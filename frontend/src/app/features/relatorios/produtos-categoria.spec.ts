import { registerLocaleData } from '@angular/common';
import pt from '@angular/common/locales/pt';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { afterEach, describe, expect, it } from 'vitest';
import { ProdutosCategoria } from './produtos-categoria';
import { ApexDonut } from './apex-donut';
import { apexTeste } from './apex.testing';

registerLocaleData(pt);
describe('Produtos da categoria', () => {
  const categoria = { id: 'categoria', nome: 'Categoria', total_pago: '102', quantidade_itens: 51 };
  const produtos = Array.from({ length: 51 }, (_, i) => ({
    id: `produto-${i}`,
    nome: `Produto ${i}`,
    total_pago: '2',
    valor_bruto: '3',
    desconto_rateado: '1',
    quantidade_itens: 1,
    quantidade_comprada: '3',
    unidade_quantidade: 'UN' as const,
  }));
  afterEach(() => TestBed.inject(HttpTestingController).verify());
  function criar(flush = true) {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), apexTeste],
    });
    const fixture = TestBed.createComponent(ProdutosCategoria);
    const http = TestBed.inject(HttpTestingController);
    fixture.componentRef.setInput('mes', '2026-10');
    fixture.componentRef.setInput('categoria', categoria);
    fixture.detectChanges();
    const resumo = http.expectOne((r) => r.url.endsWith('/mensal/produtos'));
    if (flush) {
      resumo.flush(produtos);
      fixture.detectChanges();
    }
    const grupos = () => http.expectOne((r) => r.url.endsWith('/mensal/agrupamentos'));
    return { fixture, http, resumo, grupos, componente: fixture.componentInstance };
  }
  it('pagina os produtos, mantém o gráfico inteiro e apresenta o resumo compacto', () => {
    const { fixture, http, componente, grupos } = criar();
    const grafico = fixture.debugElement.query(By.directive(ApexDonut))
      .componentInstance as ApexDonut;
    expect(grafico.opcoes().series).toHaveLength(51);
    expect(grafico.opcoes().legend?.show).toBe(false);
    expect(grafico.opcoes().plotOptions?.pie?.dataLabels?.external?.show).toBe(true);
    expect(fixture.nativeElement.querySelectorAll('[data-produto]')).toHaveLength(50);
    const texto = fixture.nativeElement.querySelector('[data-produto]').textContent;
    expect(texto).toContain('3 unidades');
    expect(texto).not.toContain('Bruto');
    expect(texto).not.toContain('Desconto');
    http.expectNone((r) => r.url.endsWith('/mensal/itens'));
    componente.navegar(1);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('[data-produto]')).toHaveLength(1);
    expect(grafico.opcoes().series).toHaveLength(51);
    fixture.nativeElement.querySelector('[data-produto]').click();
    fixture.detectChanges();
    const pedido = grupos();
    expect(pedido.request.params.get('produto_id')).toBe('produto-50');
    expect(pedido.request.params.get('agrupador')).toBe('marca');
    pedido.flush([]);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Nenhum grupo encontrado');
  });
  it('mantém apenas um produto aberto e reinicia o agrupador em marca', () => {
    const { fixture, componente, grupos } = criar();
    componente.alternar(produtos[0]);
    fixture.detectChanges();
    const anterior = grupos();
    componente.alternar(produtos[1]);
    fixture.detectChanges();
    expect(anterior.cancelled).toBe(true);
    grupos().flush([]);
    fixture.detectChanges();
    fixture.nativeElement.querySelector('[data-agrupador="variacao"]').click();
    fixture.detectChanges();
    grupos().flush([]);
    componente.alternar(produtos[1]);
    fixture.detectChanges();
    componente.alternar(produtos[1]);
    fixture.detectChanges();
    const reaberto = grupos();
    expect(reaberto.request.params.get('agrupador')).toBe('marca');
    reaberto.flush([]);
  });
  it('permite retry e cancela grupos ao trocar mês ou destruir', () => {
    const { fixture, componente, http, resumo, grupos } = criar(false);
    resumo.flush({}, { status: 500, statusText: 'Erro' });
    fixture.detectChanges();
    fixture.nativeElement.querySelector('button').click();
    http.expectOne((r) => r.url.endsWith('/mensal/produtos')).flush(produtos);
    fixture.detectChanges();
    componente.alternar(produtos[0]);
    fixture.detectChanges();
    const pedido = grupos();
    fixture.componentRef.setInput('mes', '2026-09');
    fixture.detectChanges();
    expect(pedido.cancelled).toBe(true);
    const novo = http.expectOne((r) => r.url.endsWith('/mensal/produtos'));
    expect(novo.request.params.get('mes')).toBe('2026-09');
    fixture.destroy();
    expect(novo.cancelled).toBe(true);
  });
});
