import type ApexCharts from 'apexcharts';
import { vi } from 'vitest';
import { CarregadorApex } from './apex-donut';

export class ApexSimulado {
  static instancias: ApexSimulado[] = [];
  readonly destroy = vi.fn(() => this.elemento.replaceChildren());
  readonly updateOptions = vi.fn(async (opcoes: ApexCharts.ApexOptions) => {
    this.opcoes = opcoes;
    this.desenhar();
  });
  constructor(
    private elemento: HTMLElement,
    public opcoes: ApexCharts.ApexOptions,
  ) {
    ApexSimulado.instancias.push(this);
  }
  async render() {
    this.desenhar();
  }
  private desenhar() {
    this.elemento.replaceChildren();
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    (this.opcoes.series ?? []).forEach(() => {
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('class', 'apexcharts-pie-area');
      svg.appendChild(path);
    });
    this.elemento.appendChild(svg);
  }
}
export const apexTeste = {
  provide: CarregadorApex,
  useValue: { carregar: async () => ({ default: ApexSimulado }) },
};
