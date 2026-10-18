import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { describe, expect, it } from 'vitest';
import { DecimalInput, DecimalStepper } from './decimal-input';

@Component({
  imports: [ReactiveFormsModule, DecimalInput, DecimalStepper],
  template: '<lnf-numero><input lnfDecimal [passo]="passo" [minimo]="minimo" [maximo]="maximo" [inteiro]="inteiro" [formControl]="valor" /></lnf-numero>',
})
class CampoTeste {
  passo = 1;
  minimo = 0.001;
  maximo = Number.MAX_SAFE_INTEGER;
  inteiro = false;
  readonly valor = new FormControl<number | null>(1123.15);
}

describe('entrada decimal', () => {
  it('formata, limita casas, mantém modelo numérico e respeita desabilitação', async () => {
    await TestBed.configureTestingModule({ imports: [CampoTeste] }).compileComponents();
    const fixture = TestBed.createComponent(CampoTeste);
    fixture.detectChanges();
    const campo = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    expect(campo.value).toBe('1.123,15');
    campo.dispatchEvent(new Event('focus'));
    expect(campo.value).toBe('1123,15');
    campo.value = '1.123,15678';
    campo.dispatchEvent(new Event('input'));
    expect(campo.value).toBe('1123,156');
    expect(fixture.componentInstance.valor.value).toBe(1123.156);
    campo.dispatchEvent(new Event('blur'));
    expect(campo.value).toBe('1.123,156');
    expect(fixture.componentInstance.valor.touched).toBe(true);
    fixture.componentInstance.valor.setValue(1.0001);
    expect(fixture.componentInstance.valor.invalid).toBe(true);
    fixture.componentInstance.valor.disable();
    expect(campo.disabled).toBe(true);
  });
});


describe('setas do campo decimal', () => {
  async function montar() {
    await TestBed.configureTestingModule({ imports: [CampoTeste] }).compileComponents();
    const fixture = TestBed.createComponent(CampoTeste);
    fixture.detectChanges();
    const campo = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    const [aumentar, diminuir] = Array.from(fixture.nativeElement.querySelectorAll('button')) as HTMLButtonElement[];
    return { fixture, campo, aumentar, diminuir, modelo: fixture.componentInstance };
  }

  it('preserva frações e atualiza o modelo pelos botões e teclado sem enviar formulário', async () => {
    const { fixture, campo, aumentar, diminuir, modelo } = await montar();
    modelo.valor.setValue(1123);
    fixture.detectChanges();
    aumentar.click();
    expect(modelo.valor.value).toBe(1124);
    modelo.valor.setValue(1123.15);
    fixture.detectChanges();
    expect(aumentar.type).toBe('button');
    expect(diminuir.type).toBe('button');
    aumentar.click();
    expect(modelo.valor.value).toBe(1124.15);
    expect(campo.value).toBe('1124,15');
    expect(modelo.valor.touched).toBe(true);
    campo.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', cancelable: true }));
    expect(modelo.valor.value).toBe(1123.15);
    modelo.passo = 0.01;
    modelo.valor.setValue(0.1);
    fixture.detectChanges();
    aumentar.click();
    expect(modelo.valor.value).toBe(0.11);
    diminuir.click();
    expect(modelo.valor.value).toBe(0.1);
  });

  it('respeita vazio, limites, desabilitação e quantidades inteiras', async () => {
    const { fixture, aumentar, diminuir, modelo } = await montar();
    modelo.valor.setValue(null);
    fixture.detectChanges();
    expect(diminuir.disabled).toBe(true);
    aumentar.click();
    expect(modelo.valor.value).toBe(1);
    modelo.minimo = 1;
    modelo.maximo = 3;
    modelo.inteiro = true;
    modelo.valor.setValue(1.5);
    fixture.detectChanges();
    aumentar.click();
    expect(modelo.valor.value).toBe(3);
    fixture.detectChanges();
    expect(aumentar.disabled).toBe(true);
    diminuir.click();
    diminuir.click();
    fixture.detectChanges();
    expect(modelo.valor.value).toBe(1);
    expect(diminuir.disabled).toBe(true);
    modelo.valor.disable();
    fixture.detectChanges();
    expect(aumentar.disabled).toBe(true);
    expect(diminuir.disabled).toBe(true);
  });

  it('limita a redução de quantidade fracionada ao mínimo e impede erro acumulado', async () => {
    const { fixture, aumentar, diminuir, modelo } = await montar();
    modelo.valor.setValue(0.5);
    fixture.detectChanges();
    diminuir.click();
    expect(modelo.valor.value).toBe(0.001);
    modelo.passo = 0.01;
    modelo.minimo = 0;
    modelo.valor.setValue(1.005);
    fixture.detectChanges();
    for (let i = 0; i < 10; i++) aumentar.click();
    expect(modelo.valor.value).toBe(1.105);
  });
});
