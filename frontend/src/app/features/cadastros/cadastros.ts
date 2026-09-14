import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'lnf-cadastros', imports: [RouterLink],
  template: `<div class="container page-section"><span class="eyebrow">Organização</span><h1 class="h2 mb-4">Cadastros</h1><div class="row g-3">
    @for (item of itens; track item.link) { <div class="col-12 col-md-6"><a class="card h-100 p-4 text-decoration-none text-body shadow-sm" [routerLink]="item.link"><i class="bi fs-2 text-primary" [class]="item.icone"></i><h2 class="h5 mt-3">{{ item.nome }}</h2><p class="text-secondary mb-0">{{ item.descricao }}</p></a></div> }
  </div></div>`,
})
export class Cadastros {
  readonly itens = [
    { nome: 'Categorias', descricao: 'Organize os produtos por tipo de gasto.', icone: 'bi-folder', link: '/cadastros/categorias' },
    { nome: 'Marcas', descricao: 'Consulte, inclua e ajuste marcas.', icone: 'bi-tag', link: '/cadastros/marcas' },
    { nome: 'Produtos', descricao: 'Configure unidades, medidas e variações.', icone: 'bi-basket', link: '/cadastros/produtos' },
    { nome: 'Estabelecimentos', descricao: 'Defina apelidos para as lojas.', icone: 'bi-shop', link: '/cadastros/estabelecimentos' },
  ];
}
