import { Component, computed, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { EMPTY, Subject, catchError, of, switchMap, timer } from 'rxjs';

import { ApiService } from '../../../core/api/api.service';
import { Tag } from '../../../core/models/api.models';

@Component({
  selector: 'lnf-seletor-tags',
  imports: [FormsModule],
  templateUrl: './seletor-tags.html',
})
export class SeletorTags {
  private readonly api = inject(ApiService);
  private readonly consultas = new Subject<string | null>();
  private ultimoFiltro: string | null = null;

  readonly selecionadas = input<Tag[]>([]);
  readonly ocupado = input(false);
  readonly rotulo = input('Tags do item');
  readonly adicionar = output<string>();
  readonly remover = output<string>();

  readonly busca = signal('');
  readonly aberto = signal(false);
  readonly erro = signal(false);
  readonly opcoes = signal<Tag[]>([]);
  readonly nome = computed(() => this.busca().trim().replace(/\s+/g, ' '));
  readonly sugestoes = computed(() => {
    const selecionadas = new Set(this.selecionadas().map((tag) => tag.id));
    return this.opcoes().filter((tag) => !selecionadas.has(tag.id));
  });
  readonly podeCriar = computed(() => {
    const nome = this.nome().toLocaleLowerCase('pt-BR');
    return nome.length > 0 && !this.tagComNome(nome);
  });

  constructor() {
    this.consultas
      .pipe(
        switchMap((filtro) =>
          filtro === null
            ? EMPTY
            : timer(filtro ? 250 : 0).pipe(
                switchMap(() => this.api.listarTags(filtro || undefined)),
                catchError(() => {
                  this.erro.set(true);
                  return of([] as Tag[]);
                }),
              ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((tags) => this.opcoes.set(tags));
  }

  abrirSugestoes(): void {
    this.aberto.set(true);
    this.consultar();
  }

  atualizarBusca(valor: string): void {
    this.busca.set(valor);
    if (this.aberto()) this.consultar(false);
  }

  fecharSugestoes(): void {
    this.aberto.set(false);
    this.ultimoFiltro = null;
    this.consultas.next(null);
  }

  selecionar(nome: string): void {
    if (this.ocupado()) return;
    this.adicionar.emit(nome);
    this.busca.set('');
    this.aberto.set(true);
  }

  confirmarBusca(evento: Event): void {
    evento.preventDefault();
    const nome = this.nome();
    if (!nome || this.ocupado()) return;
    const existente = this.tagComNome(nome);
    if (existente && this.selecionadas().some((tag) => tag.id === existente.id)) return;
    this.selecionar(existente?.nome ?? nome);
  }

  private consultar(forcar = true): void {
    const filtro = this.nome().length >= 3 ? this.nome() : '';
    if (!forcar && filtro === this.ultimoFiltro) return;
    this.ultimoFiltro = filtro;
    this.erro.set(false);
    this.opcoes.set([]);
    this.consultas.next(filtro);
  }

  private tagComNome(nome: string): Tag | undefined {
    const normalizado = nome.toLocaleLowerCase('pt-BR');
    return [...this.opcoes(), ...this.selecionadas()].find(
      (tag) => tag.nome.toLocaleLowerCase('pt-BR') === normalizado,
    );
  }
}
