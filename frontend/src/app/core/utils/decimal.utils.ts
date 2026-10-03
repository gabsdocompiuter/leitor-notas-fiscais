import { AbstractControl, ValidationErrors } from '@angular/forms';
import { VariacaoProduto } from '../models/api.models';

export function formatarDecimal(valor: string | number): string {
  const texto = String(valor);
  const numero = Number(texto.includes(',') ? texto.replace(/\./g, '').replace(',', '.') : texto);
  return Number.isFinite(numero)
    ? numero.toLocaleString('pt-BR', { maximumFractionDigits: 3 })
    : '';
}

export function formatarVariacao(variacao: VariacaoProduto): string {
  return `${formatarDecimal(variacao.quantidade)} ${variacao.unidade_medida}`;
}

export function limitarEntradaDecimal(valor: string): string {
  const texto = (valor.includes(',') ? valor.replace(/\./g, '') : valor.replace('.', ',')).replace(
    /[^\d,]/g,
    '',
  );
  const [inteiro, ...partes] = texto.split(',');
  return partes.length ? `${inteiro || '0'},${partes.join('').slice(0, 3)}` : inteiro;
}

export function decimalValido(valor: string | number | null): boolean {
  if (valor === null || valor === '') return false;
  const texto = String(valor).replace(',', '.');
  return /^\d+(?:\.\d{1,3})?$/.test(texto) && Number.isFinite(Number(texto));
}

export function validarDecimal(controle: AbstractControl): ValidationErrors | null {
  return controle.value === null || controle.value === '' || decimalValido(controle.value)
    ? null
    : { casasDecimais: true };
}
