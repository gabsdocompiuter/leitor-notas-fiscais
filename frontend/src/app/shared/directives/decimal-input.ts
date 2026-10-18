import { Component, Directive, ElementRef, HostListener, contentChild, forwardRef, inject, input, output, signal } from '@angular/core';
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
  private readonly versao = signal(0);
  private alterar: (valor: number | null) => void = () => {};
  private tocar: () => void = () => {};
  readonly validate = validarDecimal;
  readonly passo = input(1);
  readonly minimo = input(0.001);
  readonly maximo = input(Number.MAX_SAFE_INTEGER);
  readonly inteiro = input(false);
  readonly nomeCampo = input('valor');
  readonly valorAlterado = output<number | null>();

  private numero(): number | null {
    const texto = this.elemento.nativeElement.value;
    if (!texto) return null;
    return Number(texto.replace(/\./g, '').replace(',', '.'));
  }

  private proximo(direcao: number): number | null {
    const atual = this.numero();
    if (atual === null && direcao < 0) return null;
    const base = atual ?? 0;
    const valor = base + direcao * this.passo();
    const arredondado = this.inteiro()
      ? (direcao > 0 ? Math.ceil(valor) : Math.floor(valor))
      : (Math.abs(valor) < 1e12 ? Math.round(valor * 1000) / 1000 : Number(valor.toFixed(3)));
    return Math.min(this.maximo(), Math.max(this.minimo(), arredondado));
  }

  podeAlterar(direcao: number): boolean {
    this.versao();
    const campo = this.elemento.nativeElement;
    const proximo = this.proximo(direcao);
    return !campo.disabled && !campo.readOnly && proximo !== null &&
      Number.isFinite(proximo) && proximo !== this.numero();
  }

  incrementar(direcao: number): void {
    if (!this.podeAlterar(direcao)) return;
    const valor = this.proximo(direcao)!;
    const campo = this.elemento.nativeElement;
    campo.focus();
    campo.value = String(valor).replace('.', ',');
    this.alterar(valor);
    this.valorAlterado.emit(valor);
    this.tocar();
    this.versao.update(valor => valor + 1);
  }

  @HostListener('keydown', ['$event'])
  teclado(evento: KeyboardEvent): void {
    if (evento.key !== 'ArrowUp' && evento.key !== 'ArrowDown') return;
    evento.preventDefault();
    this.incrementar(evento.key === 'ArrowUp' ? 1 : -1);
  }

  writeValue(valor: number | null): void {
    this.elemento.nativeElement.value = valor === null ? '' : formatarDecimal(valor);
    this.versao.update(atual => atual + 1);
  }
  registerOnChange(fn: (valor: number | null) => void): void {
    this.alterar = fn;
  }
  registerOnTouched(fn: () => void): void {
    this.tocar = fn;
  }
  setDisabledState(desabilitado: boolean): void {
    this.elemento.nativeElement.disabled = desabilitado;
    this.versao.update(atual => atual + 1);
  }

  @HostListener('input')
  entrada(): void {
    const campo = this.elemento.nativeElement;
    campo.value = limitarEntradaDecimal(campo.value);
    const valor = campo.value ? Number(campo.value.replace(',', '.')) : null;
    this.alterar(valor);
    this.valorAlterado.emit(valor);
    this.versao.update(atual => atual + 1);
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


@Component({
  selector: 'lnf-numero',
  host: { class: 'lnf-numero' },
  template: `
    <ng-content />
    <span class="lnf-numero-setas">
      <button type="button" [attr.aria-label]="'Aumentar ' + (campo()?.nomeCampo() ?? 'valor')"
        [disabled]="!campo()?.podeAlterar(1)" (click)="campo()?.incrementar(1)">
        <i class="bi bi-caret-up-fill" aria-hidden="true"></i>
      </button>
      <button type="button" [attr.aria-label]="'Diminuir ' + (campo()?.nomeCampo() ?? 'valor')"
        [disabled]="!campo()?.podeAlterar(-1)" (click)="campo()?.incrementar(-1)">
        <i class="bi bi-caret-down-fill" aria-hidden="true"></i>
      </button>
    </span>
  `,
})
export class DecimalStepper {
  readonly campo = contentChild(DecimalInput);
}
