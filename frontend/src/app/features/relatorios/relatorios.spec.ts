import { registerLocaleData } from '@angular/common';
import pt from '@angular/common/locales/pt';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { afterEach, describe, expect, it } from 'vitest';
import { Relatorios } from './relatorios';
import { apexTeste } from './apex.testing';
registerLocaleData(pt);
describe('Relatórios por categoria', () => {
  const grupo = { id: 'categoria-a', nome: 'Alimentação', total_pago: '100', quantidade_itens: 51 };
  afterEach(() => TestBed.inject(HttpTestingController).verify());
  function criar() {
    const parametros = new BehaviorSubject(convertToParamMap({ mes: '2026-10' }));
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        apexTeste,
        { provide: ActivatedRoute, useValue: { queryParamMap: parametros } },
      ],
    });
    const fixture = TestBed.createComponent(Relatorios);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http
      .expectOne((r) => r.url.endsWith('/relatorios/mensal'))
      .flush({
        mes: '2026-10',
        total_pago: '100',
        total_desconto: '0',
        quantidade_notas: 1,
        quantidade_itens: 51,
        total_mes_anterior: '0',
        categorias: [grupo],
        tags: [grupo],
      });
    fixture.detectChanges();
    const abrir = () => {
      const botao = fixture.nativeElement.querySelector(
        'lnf-donut-categorias button',
      ) as HTMLButtonElement;
      botao.click();
      fixture.detectChanges();
      return botao;
    };
    const produtos = () => http.expectOne((r) => r.url.endsWith('/mensal/produtos'));
    return { fixture, http, parametros, abrir, produtos, componente: fixture.componentInstance };
  }
  it('abre modal, mantém foco e cancela resumo ao fechar por Escape', async () => {
    const { fixture, abrir, produtos } = criar();
    const botao = abrir();
    const pedido = produtos();
    expect(pedido.request.params.get('categoria_id')).toBe(grupo.id);
    await fixture.whenStable();
    const dialogo = fixture.nativeElement.querySelector('[role=dialog]');
    const fechar = dialogo.querySelector('[data-fechar]');
    expect(document.activeElement).toBe(fechar);
    fechar.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }),
    );
    expect(document.activeElement).toBe(fechar);
    fechar.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();
    await fixture.whenStable();
    expect(pedido.cancelled).toBe(true);
    expect(fixture.nativeElement.querySelector('[role=dialog]')).toBeNull();
    expect(document.activeElement).toBe(botao);
  });
  it('cancela o resumo ao trocar o mês e mantém o estado sem compras', () => {
    const { fixture, abrir, produtos, parametros, http } = criar();
    abrir();
    const pedido = produtos();
    parametros.next(convertToParamMap({ mes: '2026-09' }));
    fixture.detectChanges();
    expect(pedido.cancelled).toBe(true);
    http
      .expectOne((r) => r.url.endsWith('/relatorios/mensal'))
      .flush({
        quantidade_notas: 0,
        total_pago: '0',
        total_mes_anterior: '0',
        total_desconto: '0',
        quantidade_itens: 0,
      });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=dialog]')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Nenhuma compra neste mês');
  });
  it('mantém tags no painel e limpa a rolagem ao sair', () => {
    const { fixture, componente, http, abrir, produtos } = criar();
    componente.selecionarGrupo('tag', grupo);
    http.expectOne((r) => r.url.endsWith('/mensal/itens')).flush({ itens: [], total: 0 });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=dialog]')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Nenhum item encontrado');
    abrir();
    const pedido = produtos();
    fixture.destroy();
    expect(pedido.cancelled).toBe(true);
    expect(document.body.style.overflow).not.toBe('hidden');
  });
});
