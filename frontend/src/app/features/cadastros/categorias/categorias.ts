import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api/api.service';
import { Categoria } from '../../../core/models/api.models';
import { mensagemErro } from '../../../core/utils/erro-api';

@Component({
  selector: 'lnf-categorias',
  imports: [FormsModule, RouterLink],
  templateUrl: './categorias.html',
})
export class Categorias implements OnInit {
  private readonly api = inject(ApiService);

  readonly categorias = signal<Categoria[]>([]);
  readonly erro = signal<string | null>(null);
  busca = '';

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.erro.set(null);
    this.api.listarCategorias(this.busca).subscribe({
      next: (categorias) => this.categorias.set(categorias),
      error: (erro) => this.erro.set(mensagemErro(erro)),
    });
  }
}
