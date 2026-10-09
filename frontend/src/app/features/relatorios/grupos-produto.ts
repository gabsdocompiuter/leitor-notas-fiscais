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
import {
  AgrupadorRelatorio,
  AgrupamentoRelatorio,
  ItensRelatorio,
} from '../../core/models/api.models';
import { mensagemErro } from '../../core/utils/erro-api';
import { ItensRelatorioLista } from './itens-relatorio';
import { QuantidadeCompradaPipe } from './quantidade-relatorio.pipe';

@Component({
  selector: 'lnf-grupos-produto',
  imports: [CurrencyPipe, DecimalPipe, QuantidadeCompradaPipe, ItensRelatorioLista],
  templateUrl: './grupos-produto.html',
})
export class GruposProduto {
  private readonly api = inject(ApiService);
  private readonly elemento = inject<ElementRef<HTMLElement>>(ElementRef);
  private consulta?: Subscription;
  private consultaItens?: Subscription;
  readonly mes = input.required<string>();
  readonly categoriaId = input.required<string>();
  readonly produtoId = input.required<string>();
  readonly opcoes: { valor: AgrupadorRelatorio; nome: string }[] = [
    { valor: 'marca', nome: 'Marca' },
    { valor: 'estabelecimento', nome: 'Estabelecimento' },
    { valor: 'variacao', nome: 'Variação' },
  ];
  readonly agrupador = signal<AgrupadorRelatorio>('marca');
  readonly grupos = signal<AgrupamentoRelatorio[]>([]);
  readonly deslocamento = signal(0);
  readonly limite = 50;
  readonly visiveis = computed(() =>
    this.grupos().slice(this.deslocamento(), this.deslocamento() + this.limite),
  );
  readonly carregando = signal(false);
  readonly erro = signal<string | null>(null);
  readonly expandido = signal<AgrupamentoRelatorio | null>(null);
  readonly paginaItens = signal<ItensRelatorio | null>(null);
  readonly deslocamentoItens = signal(0);
  readonly carregandoItens = signal(false);
  readonly erroItens = signal<string | null>(null);

  constructor() {
    effect(() => {
      this.mes();
      this.categoriaId();
      this.produtoId();
      untracked(() => {
        this.agrupador.set('marca');
        this.carregar();
      });
    });
    inject(DestroyRef).onDestroy(() => {
      this.consulta?.unsubscribe();
      this.consultaItens?.unsubscribe();
    });
  }

  chave(grupo: AgrupamentoRelatorio): string {
    return grupo.id ?? 'sem_grupo';
  }
  idCompras(grupo: AgrupamentoRelatorio): string {
    return `compras-${this.produtoId()}-${this.agrupador()}-${this.chave(grupo)}`;
  }

  selecionar(agrupador: AgrupadorRelatorio): void {
    if (agrupador === this.agrupador()) return;
    this.agrupador.set(agrupador);
    this.carregar();
  }

  private focarSeletor(): void {
    const host = this.elemento.nativeElement;
    if (host.contains(host.ownerDocument.activeElement)) {
      host.querySelector<HTMLButtonElement>(`[data-agrupador="${this.agrupador()}"]`)?.focus();
    }
  }

  carregar(): void {
    this.focarSeletor();
    this.consulta?.unsubscribe();
    this.fecharGrupo();
    this.deslocamento.set(0);
    this.grupos.set([]);
    this.carregando.set(true);
    this.erro.set(null);
    this.consulta = this.api
      .listarAgrupamentosRelatorio(
        this.mes(),
        this.categoriaId(),
        this.produtoId(),
        this.agrupador(),
      )
      .subscribe({
        next: (grupos) => {
          this.grupos.set(grupos);
          this.carregando.set(false);
        },
        error: (erro) => {
          this.erro.set(mensagemErro(erro));
          this.carregando.set(false);
        },
      });
  }

  navegar(quantidade: number): void {
    this.focarSeletor();
    this.fecharGrupo();
    this.deslocamento.update((atual) =>
      Math.max(
        0,
        Math.min(
          Math.floor(Math.max(0, this.grupos().length - 1) / this.limite) * this.limite,
          atual + quantidade * this.limite,
        ),
      ),
    );
  }

  alternar(grupo: AgrupamentoRelatorio): void {
    const fechar = this.expandido() === grupo;
    this.fecharGrupo();
    if (fechar) return;
    this.expandido.set(grupo);
    this.carregarItens();
  }

  private fecharGrupo(): void {
    this.consultaItens?.unsubscribe();
    this.expandido.set(null);
    this.paginaItens.set(null);
    this.deslocamentoItens.set(0);
    this.carregandoItens.set(false);
    this.erroItens.set(null);
  }

  navegarItens(quantidade: number): void {
    this.deslocamentoItens.update((atual) => Math.max(0, atual + quantidade * this.limite));
    this.carregarItens();
  }

  carregarItens(): void {
    const grupo = this.expandido();
    if (!grupo) return;
    const host = this.elemento.nativeElement;
    if (host.contains(host.ownerDocument.activeElement)) {
      [...host.querySelectorAll<HTMLButtonElement>('[data-grupo]')]
        .find((botao) => botao.dataset['grupo'] === this.chave(grupo))
        ?.focus();
    }
    this.consultaItens?.unsubscribe();
    this.paginaItens.set(null);
    this.erroItens.set(null);
    this.carregandoItens.set(true);
    this.consultaItens = this.api
      .listarItensRelatorio(
        this.mes(),
        this.categoriaId(),
        undefined,
        this.deslocamentoItens(),
        this.produtoId(),
        { agrupador: this.agrupador(), grupoId: grupo.id },
      )
      .subscribe({
        next: (pagina) => {
          this.paginaItens.set(pagina);
          this.carregandoItens.set(false);
        },
        error: (erro) => {
          this.erroItens.set(mensagemErro(erro));
          this.carregandoItens.set(false);
        },
      });
  }
}
