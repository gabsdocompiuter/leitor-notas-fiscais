import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api/api.service';
import { Marca } from '../../../core/models/api.models';
import { mensagemErro } from '../../../core/utils/erro-api';

@Component({
  selector: 'lnf-marcas',
  imports: [FormsModule, RouterLink],
  templateUrl: './marcas.html',
})
export class Marcas implements OnInit {
  private readonly api = inject(ApiService);

  readonly marcas = signal<Marca[]>([]);
  readonly erro = signal<string | null>(null);
  busca = '';

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.erro.set(null);
    this.api.listarMarcas(this.busca).subscribe({
      next: (marcas) => this.marcas.set(marcas),
      error: (erro) => this.erro.set(mensagemErro(erro)),
    });
  }
}
