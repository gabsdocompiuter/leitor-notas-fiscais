import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { describe, expect, it } from 'vitest';
import { DecimalInput } from './decimal-input';

@Component({
  imports: [ReactiveFormsModule, DecimalInput],
  template: '<input lnfDecimal [formControl]="valor" />',
})
class CampoTeste {
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
