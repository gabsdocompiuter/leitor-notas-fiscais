import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, computed, input, output } from '@angular/core';
import { GrupoRelatorio } from '../../core/models/api.models';
import { ApexDonut, corGrupo } from './apex-donut';
import { QuantidadesCompradasPipe } from './quantidade-relatorio.pipe';

@Component({
  selector: 'lnf-donut-categorias',
  imports: [CurrencyPipe, DecimalPipe, ApexDonut, QuantidadesCompradasPipe],
  templateUrl: './donut-categorias.html',
  styleUrl: './donut-categorias.scss',
})
export class DonutCategorias {
  readonly categorias = input.required<GrupoRelatorio[]>();
  readonly total = input.required<string>();
  readonly selecionar = output<GrupoRelatorio>();
  readonly grupos = computed(() =>
    this.categorias().map((grupo) => ({
      grupo,
      cor: corGrupo(grupo.id),
      percentual:
        Number(this.total()) > 0 ? (Number(grupo.total_pago) / Number(this.total())) * 100 : 0,
    })),
  );

  escolher(grupo: GrupoRelatorio, evento: Event): void {
    (evento.currentTarget as HTMLButtonElement).focus();
    this.selecionar.emit(grupo);
  }
}
