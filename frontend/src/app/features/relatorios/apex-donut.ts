import { CurrencyPipe } from '@angular/common';
import { DOCUMENT } from '@angular/common';
import {
  Component,
  DestroyRef,
  ElementRef,
  Injectable,
  PendingTasks,
  afterRenderEffect,
  computed,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import type ApexCharts from 'apexcharts';
import { GrupoRelatorio } from '../../core/models/api.models';

export function corGrupo(id: string): string {
  let hash = 0;
  for (const letra of id) hash = (Math.imul(hash, 31) + letra.charCodeAt(0)) >>> 0;
  return `hsl(${(hash * 137) % 360} 68% 52%)`;
}

export function linhasRotulo(nome: string, limite = 20): string[] {
  const partes = nome.match(new RegExp(`.{1,${limite}}(?:\\s|$)|\\S{1,${limite}}`, 'g')) ?? [nome];
  return partes.map((parte) => parte.trim()).filter(Boolean);
}

@Injectable({ providedIn: 'root' })
export class CarregadorApex {
  carregar() {
    return import('apexcharts/donut');
  }
}

@Component({
  selector: 'lnf-apex-donut',
  imports: [CurrencyPipe],
  template: `
    <div class="area" [class.externa]="externos()">
      <div
        #grafico
        class="grafico"
        [class.d-none]="positivos().length === 0"
        (keydown)="teclado($event)"
      ></div>
      @if (positivos().length === 0) {
        <div class="sem-valores mx-auto d-flex flex-column justify-content-center text-center">
          <span class="small text-body-secondary">{{ tituloTotal() }}</span>
          <strong>{{ +total() | currency: 'BRL' : 'symbol' : '1.2-2' : 'pt-BR' }}</strong>
        </div>
        <p class="small text-body-secondary text-center mt-2 mb-0">Sem valores para distribuir</p>
      }
    </div>
    @if (erro()) {
      <p class="small text-danger text-center" role="alert">Não foi possível exibir o gráfico.</p>
    }
  `,
  styles: `
    :host {
      display: block;
      min-width: 0;
    }
    .area {
      overflow-x: auto;
    }
    .grafico {
      width: 100%;
      max-width: 320px;
      margin-inline: auto;
    }
    .externa .grafico {
      max-width: none;
    }
    .sem-valores {
      width: 240px;
      height: 240px;
      border: 36px solid var(--bs-secondary-bg);
      border-radius: 50%;
    }
  `,
})
export class ApexDonut {
  private readonly documento = inject(DOCUMENT);
  private readonly loader = inject(CarregadorApex);
  private readonly pendencias = inject(PendingTasks);
  private readonly elemento = viewChild.required<ElementRef<HTMLElement>>('grafico');
  private readonly tema = signal(this.documento.documentElement.getAttribute('data-bs-theme'));
  private instancia?: ApexCharts;
  private destruido = false;
  private fila: Promise<void> = Promise.resolve();
  readonly grupos = input.required<GrupoRelatorio[]>();
  readonly total = input.required<string>();
  readonly externos = input(false);
  readonly tituloTotal = input('Total do mês');
  readonly selecionar = output<GrupoRelatorio>();
  readonly erro = signal(false);
  readonly positivos = computed(() =>
    this.grupos().filter((grupo) => Number(grupo.total_pago) > 0),
  );

  constructor() {
    const observador = new MutationObserver(() =>
      this.tema.set(this.documento.documentElement.getAttribute('data-bs-theme')),
    );
    observador.observe(this.documento.documentElement, {
      attributes: true,
      attributeFilter: ['data-bs-theme'],
    });
    afterRenderEffect(() => {
      const options = this.opcoes();
      const concluir = this.pendencias.add();
      this.fila = this.fila
        .then(async () => {
          if (this.destruido) return;
          if (!this.positivos().length) {
            this.instancia?.destroy();
            this.instancia = undefined;
            return;
          }
          if (!this.instancia) {
            const { default: Apex } = await this.loader.carregar();
            if (this.destruido) return;
            this.instancia = new Apex(this.elemento().nativeElement, options);
            await this.instancia.render();
          } else {
            await this.instancia.updateOptions(options, false, false);
          }
          if (!this.destruido) this.prepararFatias();
          this.erro.set(false);
        })
        .catch(() => {
          if (!this.destruido) this.erro.set(true);
        })
        .finally(concluir);
    });
    inject(DestroyRef).onDestroy(() => {
      this.destruido = true;
      observador.disconnect();
      this.instancia?.destroy();
    });
  }

  opcoes(): ApexCharts.ApexOptions {
    const grupos = this.positivos();
    const externo = this.externos();
    const cor = this.tema() === 'dark' ? '#dee2e6' : '#212529';
    const moeda = (valor: number | string) =>
      new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(valor));
    return {
      series: grupos.map((grupo) => Number(grupo.total_pago)),
      labels: grupos.map((grupo) => grupo.nome),
      colors: grupos.map((grupo) => corGrupo(grupo.id)),
      chart: {
        type: 'donut',
        height: externo ? Math.max(560, grupos.length * 32) : 280,
        fontFamily: 'inherit',
        foreColor: cor,
        background: 'transparent',
        animations: { enabled: false },
        toolbar: { show: false },
        accessibility: {
          enabled: true,
          description: externo ? 'Distribuição por produto' : 'Distribuição por categoria',
          keyboard: { enabled: true },
        },
        events: {
          mounted: () => this.prepararFatias(),
          updated: () => this.prepararFatias(),
          dataPointSelection: (_event, _chart, config) => {
            const grupo = grupos[config?.dataPointIndex ?? -1];
            if (grupo) {
              const acionador =
                this.elemento().nativeElement.querySelectorAll<SVGElement>('.apexcharts-pie-area')[
                  config?.dataPointIndex ?? -1
                ];
              acionador?.focus();
              this.selecionar.emit(grupo);
            }
          },
        },
      },
      legend: { show: false },
      responsive: externo
        ? [
            {
              breakpoint: 480,
              options: {
                chart: { height: Math.max(400, grupos.length * 40) },
                dataLabels: { style: { fontSize: '10px' } },
                plotOptions: {
                  pie: {
                    dataLabels: {
                      external: {
                        fontSize: '10px',
                        formatter: (nome: string) => linhasRotulo(nome, 12),
                        connector: { length: 8, gap: 3 },
                      },
                    },
                  },
                },
              },
            },
          ]
        : [],
      stroke: { width: 2, colors: [this.tema() === 'dark' ? '#212529' : '#fff'] },
      dataLabels: {
        enabled: externo,
        formatter: (valor) =>
          `${Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`,
      },
      tooltip: {
        theme: this.tema() === 'dark' ? 'dark' : 'light',
        y: {
          formatter: (valor) => {
            const soma = grupos.reduce((total, grupo) => total + Number(grupo.total_pago), 0);
            const percentual = soma ? (valor / soma) * 100 : 0;
            return `${moeda(valor)} · ${percentual.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
          },
        },
      },
      plotOptions: {
        pie: {
          expandOnClick: false,
          dataLabels: {
            minAngleToShowLabel: 10,
            external: {
              show: externo,
              fontSize: '12px',
              color: cor,
              formatter: (nome) => linhasRotulo(nome),
              connector: { show: true, length: 12 },
            },
          },
          donut: {
            size: '65%',
            labels: {
              show: !externo,
              name: { show: true, color: cor, fontSize: '13px' },
              value: { show: true, color: cor, fontSize: '16px', formatter: moeda },
              total: {
                show: true,
                showAlways: true,
                label: this.tituloTotal(),
                color: cor,
                formatter: () => moeda(this.total()),
              },
            },
          },
        },
      },
    };
  }

  private prepararFatias(): void {
    if (this.externos()) return;
    const grupos = this.positivos();
    this.elemento()
      .nativeElement.querySelectorAll('.apexcharts-pie-area')
      .forEach((fatia, indice) => {
        const grupo = grupos[indice];
        if (!grupo) return;
        fatia.setAttribute('tabindex', '0');
        fatia.setAttribute('role', 'button');
        fatia.setAttribute('aria-haspopup', 'dialog');
        fatia.setAttribute('aria-label', `Ver detalhes de ${grupo.nome}`);
        fatia.setAttribute('data-grupo-id', grupo.id);
      });
  }

  teclado(evento: KeyboardEvent): void {
    if (evento.key !== 'Enter' && evento.key !== ' ') return;
    const alvo = evento.target as Element;
    const id = alvo.getAttribute('data-grupo-id');
    const grupo = this.positivos().find((grupo) => grupo.id === id);
    if (grupo) {
      evento.preventDefault();
      this.selecionar.emit(grupo);
    }
  }
}
