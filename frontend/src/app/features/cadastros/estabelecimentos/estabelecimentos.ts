import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api/api.service';
import { Estabelecimento } from '../../../core/models/api.models';
import { mensagemErro } from '../../../core/utils/erro-api';

@Component({
  selector: 'lnf-estabelecimentos',
  imports: [FormsModule, RouterLink],
  templateUrl: './estabelecimentos.html',
})
export class Estabelecimentos implements OnInit {
  private readonly api = inject(ApiService);

  readonly lojas = signal<Estabelecimento[]>([]);
  readonly erro = signal<string | null>(null);
  busca = '';

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.erro.set(null);
    this.api.listarEstabelecimentos(this.busca).subscribe({
      next: (lojas) => this.lojas.set(lojas),
      error: (erro) => this.erro.set(mensagemErro(erro)),
    });
  }
}
