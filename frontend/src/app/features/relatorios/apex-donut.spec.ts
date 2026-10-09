import { registerLocaleData } from '@angular/common';
import pt from '@angular/common/locales/pt';
import { TestBed } from '@angular/core/testing';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApexDonut, CarregadorApex, linhasRotulo } from './apex-donut';
import { apexTeste, ApexSimulado } from './apex.testing';

registerLocaleData(pt);
describe('Integração Apex', () => {
  afterEach(() => document.documentElement.removeAttribute('data-bs-theme'));
  function criar() {
    const fixture = TestBed.createComponent(ApexDonut);
    fixture.componentRef.setInput('grupos', [
      { id: 'a', nome: 'Produto com nome muito longo', total_pago: '50', quantidade_itens: 1 },
    ]);
    fixture.componentRef.setInput('total', '50');
    return fixture;
  }
  it('atualiza o tema sem mudar as cores e destrói a instância ao sair', async () => {
    TestBed.configureTestingModule({ providers: [apexTeste] });
    const fixture = criar();
    fixture.detectChanges();
    await fixture.whenStable();
    const instancia = ApexSimulado.instancias.at(-1)!;
    const cores = fixture.componentInstance.opcoes().colors;
    document.documentElement.setAttribute('data-bs-theme', 'dark');
    await Promise.resolve();
    fixture.detectChanges();
    await fixture.whenStable();
    expect(instancia.updateOptions).toHaveBeenCalled();
    expect(fixture.componentInstance.opcoes().chart?.foreColor).toBe('#dee2e6');
    expect(fixture.componentInstance.opcoes().colors).toEqual(cores);
    fixture.destroy();
    expect(instancia.destroy).toHaveBeenCalledOnce();
  });
  it('não cria gráficos depois de sair durante o carregamento da biblioteca', async () => {
    let resolver!: (value: unknown) => void;
    const construir = vi.fn();
    TestBed.configureTestingModule({
      providers: [
        {
          provide: CarregadorApex,
          useValue: { carregar: () => new Promise((resolve) => (resolver = resolve)) },
        },
      ],
    });
    const fixture = criar();
    fixture.detectChanges();
    await Promise.resolve();
    await Promise.resolve();
    fixture.destroy();
    resolver({ default: construir });
    await Promise.resolve();
    await Promise.resolve();
    expect(construir).not.toHaveBeenCalled();
  });
  it('quebra rótulos externos sem perder palavras ou sequências longas', () => {
    const texto = 'Café torrado e moído embalagem de 500 gramas';
    expect(linhasRotulo(texto).join(' ')).toBe(texto);
    expect(linhasRotulo('a'.repeat(50)).every((linha) => linha.length <= 20)).toBe(true);
  });
});
