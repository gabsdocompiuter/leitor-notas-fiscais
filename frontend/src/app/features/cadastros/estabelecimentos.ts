import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/api/api.service';
import { Estabelecimento } from '../../core/models/api.models';
import { mensagemErro } from '../../core/utils/erro-api';

@Component({ selector: 'lnf-estabelecimentos', imports: [FormsModule, RouterLink], template: `
<div class="container page-section"><a routerLink="/cadastros" class="back-link"><i class="bi bi-arrow-left me-2"></i>Cadastros</a><div class="my-4"><span class="eyebrow">Cadastro</span><h1 class="h2">Estabelecimentos</h1><p class="text-secondary">Razão social e CNPJ vêm da nota fiscal. Aqui você pode alterar apenas o apelido.</p></div>@if (erro()) { <div class="alert alert-danger">{{ erro() }}</div> }<input class="form-control mb-3" placeholder="Pesquisar estabelecimento" [(ngModel)]="busca" (ngModelChange)="carregar()">
<div class="d-grid gap-3">@for (loja of lojas(); track loja.id) { <article class="card p-3"><strong>{{ loja.razao_social }}</strong><small class="text-secondary">CNPJ {{ loja.cnpj }}</small><div class="input-group mt-3"><input class="form-control" placeholder="Apelido opcional" [ngModel]="apelidos[loja.id] ?? loja.apelido" (ngModelChange)="apelidos[loja.id] = $event"><button class="btn btn-outline-primary" (click)="salvar(loja)">Salvar apelido</button></div></article> } @empty { <p class="text-center text-secondary py-5">Nenhum estabelecimento encontrado.</p> }</div></div>` })
export class Estabelecimentos implements OnInit {
  private api = inject(ApiService); readonly lojas = signal<Estabelecimento[]>([]); readonly erro = signal<string | null>(null); busca = ''; apelidos: Record<string, string | null> = {};
  ngOnInit(): void { this.carregar(); }
  carregar(): void { this.api.listarEstabelecimentos(this.busca).subscribe({ next: (x) => this.lojas.set(x), error: (e) => this.erro.set(mensagemErro(e)) }); }
  salvar(loja: Estabelecimento): void { const valor = this.apelidos[loja.id]; this.api.atualizarEstabelecimento(loja.id, valor?.trim() || null).subscribe({ next: () => this.carregar(), error: (e) => this.erro.set(mensagemErro(e)) }); }
}
