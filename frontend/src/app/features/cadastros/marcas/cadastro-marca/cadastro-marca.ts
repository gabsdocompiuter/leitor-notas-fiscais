import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ApiService } from '../../../../core/api/api.service';
import { mensagemErro } from '../../../../core/utils/erro-api';

@Component({
  selector: 'lnf-cadastro-marca',
  imports: [FormsModule, RouterLink],
  templateUrl: './cadastro-marca.html',
})
export class CadastroMarca implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly erro = signal<string | null>(null);
  readonly carregando = signal(true);
  readonly salvando = signal(false);

  id: string | null = null;
  novo = false;
  nome = '';

  ngOnInit(): void {
    this.id = this.route.snapshot.paramMap.get('id');
    this.novo = this.id === null;
    if (this.novo) {
      this.carregando.set(false);
      return;
    }

    this.api.obterMarca(this.id!).subscribe({
      next: (marca) => {
        this.nome = marca.nome;
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
    const requisicao = this.id ? this.api.atualizarMarca(this.id, nome) : this.api.criarMarca(nome);
    requisicao.subscribe({
      next: () => void this.router.navigateByUrl('/cadastros/marcas'),
      error: (erro) => {
        this.salvando.set(false);
        this.erro.set(mensagemErro(erro));
      },
    });
  }

  private tratarErroCarregamento(erro: unknown): void {
    if (erro instanceof HttpErrorResponse && (erro.status === 404 || erro.status === 422)) {
      void this.router.navigateByUrl('/cadastros/marcas');
      return;
    }
    this.carregando.set(false);
    this.erro.set(mensagemErro(erro));
  }
}
