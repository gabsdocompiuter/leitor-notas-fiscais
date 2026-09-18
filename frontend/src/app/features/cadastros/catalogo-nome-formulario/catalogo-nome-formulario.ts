import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api/api.service';
import { mensagemErro } from '../../../core/utils/erro-api';

@Component({
  selector: 'lnf-catalogo-nome-formulario',
  imports: [FormsModule, RouterLink],
  templateUrl: './catalogo-nome-formulario.html',
})
export class CatalogoNomeFormulario implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly erro = signal<string | null>(null);
  readonly carregando = signal(true);
  readonly salvando = signal(false);

  tipo!: 'categorias' | 'marcas';
  tituloPlural = '';
  tituloSingular = '';
  rotaListagem = '';
  id: string | null = null;
  novo = false;
  nome = '';

  ngOnInit(): void {
    this.tipo = this.route.snapshot.data['tipo'] as 'categorias' | 'marcas';
    this.tituloPlural = this.tipo === 'categorias' ? 'Categorias' : 'Marcas';
    this.tituloSingular = this.tipo === 'categorias' ? 'Categoria' : 'Marca';
    this.rotaListagem = `/cadastros/${this.tipo}`;
    this.id = this.route.snapshot.paramMap.get('id');
    this.novo = this.id === null;

    if (this.novo) {
      this.carregando.set(false);
      return;
    }

    const requisicao =
      this.tipo === 'categorias'
        ? this.api.obterCategoria(this.id!)
        : this.api.obterMarca(this.id!);

    requisicao.subscribe({
      next: (item) => {
        this.nome = item.nome;
        this.carregando.set(false);
      },
      error: (erro) => this.tratarErroCarregamento(erro),
    });
  }

  salvar(): void {
    const nome = this.nome.trim();
    if (!nome) return;

    this.erro.set(null);
    this.salvando.set(true);
    const requisicao =
      this.tipo === 'categorias'
        ? this.id
          ? this.api.atualizarCategoria(this.id, nome)
          : this.api.criarCategoria(nome)
        : this.id
          ? this.api.atualizarMarca(this.id, nome)
          : this.api.criarMarca(nome);

    requisicao.subscribe({
      next: () => void this.router.navigateByUrl(this.rotaListagem),
      error: (erro) => {
        this.salvando.set(false);
        this.erro.set(mensagemErro(erro));
      },
    });
  }

  private tratarErroCarregamento(erro: unknown): void {
    if (erro instanceof HttpErrorResponse && (erro.status === 404 || erro.status === 422)) {
      void this.router.navigateByUrl(this.rotaListagem);
      return;
    }
    this.carregando.set(false);
    this.erro.set(mensagemErro(erro));
  }
}
