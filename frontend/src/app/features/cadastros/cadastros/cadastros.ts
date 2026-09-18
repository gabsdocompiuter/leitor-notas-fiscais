import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'lnf-cadastros',
  imports: [RouterLink],
  templateUrl: './cadastros.html',
})
export class Cadastros {
  readonly itens = [
    {
      nome: 'Categorias',
      descricao: 'Organize os produtos por tipo de gasto.',
      link: '/cadastros/categorias',
    },
    {
      nome: 'Marcas',
      descricao: 'Consulte, inclua e ajuste marcas.',
      link: '/cadastros/marcas',
    },
    {
      nome: 'Produtos',
      descricao: 'Configure unidades, medidas e variações.',
      link: '/cadastros/produtos',
    },
    {
      nome: 'Estabelecimentos',
      descricao: 'Defina apelidos para as lojas.',
      link: '/cadastros/estabelecimentos',
    },
  ];
}
