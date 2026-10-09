import { CurrencyPipe, DecimalPipe } from '@angular/common';
import {
  Component,
  DestroyRef,
  ElementRef,
  computed,
  effect,
  inject,
  input,
  signal,
  untracked,
} from '@angular/core';
import { Subscription } from 'rxjs';
import { ApiService } from '../../core/api/api.service';
import { GrupoRelatorio, ProdutoRelatorio } from '../../core/models/api.models';
import { mensagemErro } from '../../core/utils/erro-api';
import { ApexDonut } from './apex-donut';
import { GruposProduto } from './grupos-produto';
import { QuantidadeCompradaPipe } from './quantidade-relatorio.pipe';

@Component({
  selector: 'lnf-produtos-categoria',
  imports: [CurrencyPipe, DecimalPipe, ApexDonut, GruposProduto, QuantidadeCompradaPipe],
  templateUrl: './produtos-categoria.html',
})
export class ProdutosCategoria {
  private readonly api = inject(ApiService);
  private readonly elemento = inject<ElementRef<HTMLElement>>(ElementRef);
  private consulta?: Subscription;
  readonly mes = input.required<string>();
  readonly categoria = input.required<GrupoRelatorio>();
  readonly produtos = signal<ProdutoRelatorio[]>([]);
  readonly carregando = signal(false);
  readonly erro = signal<string | null>(null);
  readonly deslocamento = signal(0);
  readonly limite = 50;
  readonly visiveis = computed(() =>
    this.produtos().slice(this.deslocamento(), this.deslocamento() + this.limite),
  );
  readonly expandido = signal<string | null>(null);

  constructor() {
    effect(() => {
      this.mes();
      this.categoria();
      untracked(() => this.carregar());
    });
    inject(DestroyRef).onDestroy(() => {
      this.consulta?.unsubscribe();
    });
  }

  carregar(): void {
    this.focarModal();
    this.consulta?.unsubscribe();
    this.fecharProduto();
    this.deslocamento.set(0);
    this.produtos.set([]);
    this.carregando.set(true);
    this.erro.set(null);
    this.consulta = this.api.listarProdutosRelatorio(this.mes(), this.categoria().id).subscribe({
      next: (produtos) => {
        this.produtos.set(produtos);
        this.carregando.set(false);
      },
      error: (erro) => {
        this.erro.set(mensagemErro(erro));
        this.carregando.set(false);
      },
    });
  }

  percentual(valor: string): number {
    const total = Number(this.categoria().total_pago);
    return total > 0 ? (Number(valor) / total) * 100 : 0;
  }

  navegar(quantidade: number): void {
    this.focarModal();
    this.fecharProduto();
    this.deslocamento.update((valor) =>
      Math.max(
        0,
        Math.min(
          Math.floor(Math.max(0, this.produtos().length - 1) / this.limite) * this.limite,
          valor + quantidade * this.limite,
        ),
      ),
    );
  }

  alternar(produto: ProdutoRelatorio): void {
    const fechar = this.expandido() === produto.id;
    this.fecharProduto();
    if (fechar) return;
    this.expandido.set(produto.id);
  }

  private fecharProduto(): void {
    this.expandido.set(null);
  }

  private focarModal(): void {
    const elemento = this.elemento.nativeElement;
    if (elemento.contains(elemento.ownerDocument.activeElement)) {
      elemento
        .closest('[role="dialog"]')
        ?.querySelector<HTMLButtonElement>('[data-fechar]')
        ?.focus();
    }
  }
}
