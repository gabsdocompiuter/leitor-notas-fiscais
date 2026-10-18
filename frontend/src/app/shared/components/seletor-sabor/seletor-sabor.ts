import { Component, ElementRef, OnChanges, OnDestroy, computed, inject, input, output, signal, viewChild } from '@angular/core';
import { ApiService } from '../../../core/api/api.service';
import { SaborProduto } from '../../../core/models/api.models';
import { mensagemErro } from '../../../core/utils/erro-api';
import { capitalizarIniciais } from '../../../core/utils/catalogo.utils';
import { PesquisaSabor } from './pesquisa-sabor';

@Component({
  selector: 'lnf-seletor-sabor',
  imports: [PesquisaSabor],
  template: `
    <label class="form-label" [for]="id()">Sabor</label>
    <button #campo type="button" class="form-control d-flex align-items-center justify-content-between text-start"
      [id]="id()" [disabled]="disabled() || carregando()" (click)="abrir()">
      <span [class.text-body-secondary]="!nomeSelecionado()">{{ nomeSelecionado() || 'Selecionar sabor' }}</span>
      <i class="bi bi-search" aria-hidden="true"></i>
    </button>
    @if (erro()) { <div class="text-danger small" role="alert">{{ erro() }}</div> }
    @if (aberto()) {
      <lnf-pesquisa-sabor [produtoId]="produtoId()" [registros]="sabores()"
        [contexto]="contexto()" [buscaInicial]="buscaInicial()"
        (fechar)="fechar()" (registroSelecionado)="selecionar($event.id)"
        (cadastroCriado)="registrar($event)" />
    }
  `,
})
export class SeletorSabor implements OnChanges, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly campo = viewChild<ElementRef<HTMLButtonElement>>('campo');
  readonly produtoId = input.required<string>();
  readonly valor = input<string | null>(null);
  readonly disabled = input(false);
  readonly id = input('sabor');
  readonly contexto = input('');
  readonly alterado = output<string | null>();
  readonly sabores = signal<SaborProduto[]>([]);
  readonly erro = signal<string | null>(null);
  readonly carregando = signal(false);
  readonly aberto = signal(false);
  readonly buscaInicial = signal('');
  readonly nomeSelecionado = computed(() => this.sabores().find(s => s.id === this.valor())?.nome ?? '');
  private produtoCarregado = '';

  ngOnChanges(): void {
    if (this.disabled() && this.aberto()) this.fechar();
    const produtoId = this.produtoId();
    if (this.produtoCarregado === produtoId) return;
    this.fechar();
    this.produtoCarregado = produtoId;
    this.sabores.set([]);
    this.erro.set(null);
    this.carregando.set(true);
    this.api.listarSabores(produtoId).subscribe({
      next: sabores => {
        if (produtoId !== this.produtoId()) return;
        this.sabores.set(sabores);
        this.carregando.set(false);
      },
      error: erro => {
        if (produtoId !== this.produtoId()) return;
        this.erro.set(mensagemErro(erro));
        this.carregando.set(false);
      },
    });
  }

  abrir(): void {
    if (this.disabled() || this.carregando()) return;
    this.buscaInicial.set(capitalizarIniciais(this.contexto()));
    this.aberto.set(true);
    document.body.classList.add('modal-open');
  }

  fechar(): void {
    if (!this.aberto()) return;
    this.aberto.set(false);
    document.body.classList.remove('modal-open');
    this.campo()?.nativeElement.focus();
  }

  selecionar(id: string | null): void {
    if (this.disabled()) return;
    this.alterado.emit(id);
    this.fechar();
  }

  registrar(sabor: SaborProduto): void {
    if (sabor.produto_id !== this.produtoId()) return;
    this.sabores.update(atuais => [...atuais.filter(s => s.id !== sabor.id), sabor]
      .sort((a, b) => a.nome.localeCompare(b.nome)));
  }

  ngOnDestroy(): void {
    if (this.aberto()) document.body.classList.remove('modal-open');
  }
}
