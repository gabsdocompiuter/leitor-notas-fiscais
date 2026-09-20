import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api/api.service';
import { Produto } from '../../../core/models/api.models';
import { mensagemErro } from '../../../core/utils/erro-api';

@Component({
  selector: 'lnf-produtos',
  imports: [FormsModule, RouterLink],
  templateUrl: './produtos.html',
})
export class Produtos implements OnInit {
  private readonly api = inject(ApiService);

  readonly produtos = signal<Produto[]>([]);
  readonly erro = signal<string | null>(null);
  busca = '';

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.erro.set(null);
    this.api.listarProdutos(this.busca).subscribe({
      next: (produtos) => this.produtos.set(produtos),
      error: (erro) => this.erro.set(mensagemErro(erro)),
    });
  }
}
