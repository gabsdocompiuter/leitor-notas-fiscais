import { CurrencyPipe, DatePipe } from '@angular/common';
import { Component, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AgrupadorRelatorio, ItensRelatorio } from '../../core/models/api.models';
import { QuantidadeCompradaPipe } from './quantidade-relatorio.pipe';

@Component({
  selector: 'lnf-itens-relatorio',
  imports: [CurrencyPipe, DatePipe, RouterLink, QuantidadeCompradaPipe],
  templateUrl: './itens-relatorio.html',
})
export class ItensRelatorioLista {
  readonly pagina = input<ItensRelatorio | null>(null);
  readonly carregando = input(false);
  readonly erro = input<string | null>(null);
  readonly deslocamento = input(0);
  readonly limite = input(50);
  readonly compacto = input(false);
  readonly agrupador = input<AgrupadorRelatorio | null>(null);
  readonly navegar = output<number>();
  readonly tentar = output<void>();
}
