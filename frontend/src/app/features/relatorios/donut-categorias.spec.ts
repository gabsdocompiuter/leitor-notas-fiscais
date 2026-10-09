import { registerLocaleData } from '@angular/common';
import pt from '@angular/common/locales/pt';
import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { describe, expect, it, vi } from 'vitest';
import { DonutCategorias } from './donut-categorias';
import { ApexDonut } from './apex-donut';
import { apexTeste } from './apex.testing';

registerLocaleData(pt);
describe('Donut de categorias com Apex', () => {
  async function criar(valores = ['75', '25', '0']) {
    TestBed.configureTestingModule({ providers: [apexTeste] });
    const fixture = TestBed.createComponent(DonutCategorias);
    fixture.componentRef.setInput(
      'categorias',
      valores.map((total_pago, i) => ({
        id: `categoria-${i}`,
        nome: `Categoria ${i}`,
        total_pago,
        quantidade_itens: 1,
        quantidades_compradas: [{ quantidade: '3', unidade: 'UN' }],
      })),
    );
    fixture.componentRef.setInput(
      'total',
      String(valores.reduce((soma, valor) => soma + Number(valor), 0)),
    );
    fixture.detectChanges();
    await fixture.whenStable();
    const donut = fixture.debugElement.query(By.directive(ApexDonut))
      .componentInstance as ApexDonut;
    return { fixture, donut };
  }
  it('usa as proporções reais e mantém categorias zero na legenda', async () => {
    const { fixture, donut } = await criar();
    expect(donut.opcoes().series).toEqual([75, 25]);
    expect(fixture.nativeElement.querySelectorAll('.legenda button')).toHaveLength(3);
    const texto = fixture.nativeElement.querySelector('.legenda button').textContent;
    expect(texto.indexOf('75,0%')).toBeLessThan(texto.indexOf('R$'));
    expect(texto).toContain('3 unidades');
    expect(texto).not.toContain('1 item');
  });
  it('representa categoria única e estado sem valores', async () => {
    const { fixture, donut } = await criar(['100']);
    expect(donut.opcoes().series).toEqual([100]);
    fixture.componentRef.setInput('categorias', [
      { id: 'zero', nome: 'Zero', total_pago: '0', quantidade_itens: 1 },
    ]);
    fixture.componentRef.setInput('total', '0');
    fixture.detectChanges();
    await fixture.whenStable();
    expect(donut.opcoes().series).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain('Sem valores para distribuir');
  });
  it('mapeia seleção do Apex, teclado e legenda para a categoria correta', async () => {
    const { fixture, donut } = await criar();
    const emitir = vi.fn();
    fixture.componentInstance.selecionar.subscribe(emitir);
    donut
      .opcoes()
      .chart?.events?.dataPointSelection?.(
        {} as MouseEvent,
        {} as never,
        { dataPointIndex: 1 } as never,
      );
    expect(emitir.mock.lastCall?.[0].id).toBe('categoria-1');
    const path = fixture.nativeElement.querySelector('path');
    path.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    expect(emitir.mock.lastCall?.[0].id).toBe('categoria-0');
    fixture.nativeElement.querySelectorAll('.legenda button')[2].click();
    expect(emitir.mock.lastCall?.[0].id).toBe('categoria-2');
  });
  it('mantém a cor ao mudar a ordenação', async () => {
    const { fixture } = await criar();
    const cor = fixture.componentInstance.grupos()[0].cor;
    fixture.componentRef.setInput(
      'categorias',
      [...fixture.componentInstance.categorias()].reverse(),
    );
    expect(fixture.componentInstance.grupos()[2].cor).toBe(cor);
  });
});
