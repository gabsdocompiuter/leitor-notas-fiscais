import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api/api.service';
import { Categoria, Marca } from '../../../core/models/api.models';
import { mensagemErro } from '../../../core/utils/erro-api';

@Component({
  selector: 'lnf-catalogo-nomes',
  imports: [FormsModule, RouterLink],
  templateUrl: './catalogo-nomes.html',
})
export class CatalogoNomes implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);

  readonly itens = signal<(Categoria | Marca)[]>([]);
  readonly erro = signal<string | null>(null);

  tipo!: 'categorias' | 'marcas';
  titulo = '';
  nomeSingular = '';
  busca = '';

  ngOnInit(): void {
    this.tipo = this.route.snapshot.data['tipo'] as 'categorias' | 'marcas';
    this.titulo = this.tipo === 'categorias' ? 'Categorias' : 'Marcas';
    this.nomeSingular = this.tipo === 'categorias' ? 'Categoria' : 'Marca';
    this.carregar();
  }

  carregar(): void {
    this.erro.set(null);
    const requisicao =
      this.tipo === 'categorias'
        ? this.api.listarCategorias(this.busca)
        : this.api.listarMarcas(this.busca);

    requisicao.subscribe({
      next: (itens) => this.itens.set(itens),
      error: (erro) => this.erro.set(mensagemErro(erro)),
    });
  }
}
