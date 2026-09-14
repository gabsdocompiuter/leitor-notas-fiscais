import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../core/api/api.service';
import { Categoria, Marca } from '../../core/models/api.models';
import { mensagemErro } from '../../core/utils/erro-api';

@Component({ selector: 'lnf-catalogo-nomes', imports: [FormsModule, RouterLink], template: `
<div class="container page-section"><a routerLink="/cadastros" class="back-link"><i class="bi bi-arrow-left me-2"></i>Cadastros</a><div class="d-flex justify-content-between align-items-center my-4"><div><span class="eyebrow">Cadastro</span><h1 class="h2 mb-0">{{ titulo }}</h1></div><button class="btn btn-primary" (click)="novo()"><i class="bi bi-plus-lg me-2"></i>Novo</button></div>
@if (erro()) { <div class="alert alert-danger">{{ erro() }}</div> }
<div class="input-group mb-3"><span class="input-group-text"><i class="bi bi-search"></i></span><input class="form-control" placeholder="Pesquisar" [(ngModel)]="busca" (ngModelChange)="carregar()"></div>
@if (editando()) { <form class="card p-3 mb-3" (ngSubmit)="salvar()"><label class="form-label">Nome</label><div class="d-flex gap-2"><input class="form-control" required maxlength="100" [(ngModel)]="nome" name="nome" autofocus><button class="btn btn-primary" [disabled]="salvando() || !nome.trim()">Salvar</button><button type="button" class="btn btn-outline-secondary" (click)="cancelar()">Cancelar</button></div></form> }
<div class="list-group">@for (item of itens(); track item.id) { <button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" (click)="editar(item)"><span>{{ item.nome }}</span><i class="bi bi-pencil"></i></button> } @empty { <div class="text-center text-secondary py-5">Nenhum cadastro encontrado.</div> }</div></div>` })
export class CatalogoNomes implements OnInit {
  private api = inject(ApiService); private route = inject(ActivatedRoute);
  readonly itens = signal<(Categoria | Marca)[]>([]); readonly erro = signal<string | null>(null); readonly editando = signal(false); readonly salvando = signal(false);
  tipo!: 'categorias' | 'marcas'; titulo = ''; busca = ''; nome = ''; id: string | null = null;
  ngOnInit(): void { this.tipo = this.route.snapshot.data['tipo']; this.titulo = this.tipo === 'categorias' ? 'Categorias' : 'Marcas'; this.carregar(); }
  carregar(): void { const req = this.tipo === 'categorias' ? this.api.listarCategorias(this.busca) : this.api.listarMarcas(this.busca); req.subscribe({ next: (x) => this.itens.set(x), error: (e) => this.erro.set(mensagemErro(e)) }); }
  novo(): void { this.id = null; this.nome = ''; this.editando.set(true); }
  editar(item: Categoria | Marca): void { this.id = item.id; this.nome = item.nome; this.editando.set(true); }
  cancelar(): void { this.editando.set(false); }
  salvar(): void { const nome = this.nome.trim(); if (!nome) return; this.salvando.set(true); const req = this.tipo === 'categorias' ? (this.id ? this.api.atualizarCategoria(this.id, nome) : this.api.criarCategoria(nome)) : (this.id ? this.api.atualizarMarca(this.id, nome) : this.api.criarMarca(nome)); req.subscribe({ next: () => { this.salvando.set(false); this.editando.set(false); this.carregar(); }, error: (e) => { this.salvando.set(false); this.erro.set(mensagemErro(e)); } }); }
}
