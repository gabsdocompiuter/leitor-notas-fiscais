import { Directive, ElementRef, HostListener, forwardRef, inject } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, NG_VALIDATORS, Validator } from '@angular/forms';
import {
  formatarDecimal,
  limitarEntradaDecimal,
  validarDecimal,
} from '../../core/utils/decimal.utils';

@Directive({
  selector: 'input[lnfDecimal]',
  host: { type: 'text', inputmode: 'decimal' },
  providers: [
    { provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => DecimalInput), multi: true },
    { provide: NG_VALIDATORS, useExisting: forwardRef(() => DecimalInput), multi: true },
  ],
})
export class DecimalInput implements ControlValueAccessor, Validator {
  private readonly elemento = inject<ElementRef<HTMLInputElement>>(ElementRef);
  private alterar: (valor: number | null) => void = () => {};
  private tocar: () => void = () => {};
  readonly validate = validarDecimal;

  writeValue(valor: number | null): void {
    this.elemento.nativeElement.value = valor === null ? '' : formatarDecimal(valor);
  }
  registerOnChange(fn: (valor: number | null) => void): void {
    this.alterar = fn;
  }
  registerOnTouched(fn: () => void): void {
    this.tocar = fn;
  }
  setDisabledState(desabilitado: boolean): void {
    this.elemento.nativeElement.disabled = desabilitado;
  }

  @HostListener('input')
  entrada(): void {
    const campo = this.elemento.nativeElement;
    campo.value = limitarEntradaDecimal(campo.value);
    this.alterar(campo.value ? Number(campo.value.replace(',', '.')) : null);
  }
  @HostListener('blur')
  sair(): void {
    const campo = this.elemento.nativeElement;
    if (campo.value) campo.value = formatarDecimal(campo.value);
    this.tocar();
  }

  @HostListener('focus')
  focar(): void {
    this.elemento.nativeElement.value = this.elemento.nativeElement.value.replace(/\./g, '');
  }
}
