import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api/api.service';
import { Estabelecimento } from '../../../core/models/api.models';
import { mensagemErro } from '../../../core/utils/erro-api';

@Component({
  selector: 'lnf-estabelecimento-formulario',
  imports: [FormsModule, RouterLink],
  templateUrl: './estabelecimento-formulario.html',
})
export class EstabelecimentoFormulario implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly estabelecimento = signal<Estabelecimento | null>(null);
  readonly erro = signal<string | null>(null);
  readonly carregando = signal(true);
  readonly salvando = signal(false);

  id = '';
  apelido = '';

  ngOnInit(): void {
    this.id = this.route.snapshot.paramMap.get('id') ?? '';
    this.api.obterEstabelecimento(this.id).subscribe({
      next: (estabelecimento) => {
        this.estabelecimento.set(estabelecimento);
        this.apelido = estabelecimento.apelido ?? '';
        this.carregando.set(false);
      },
      error: (erro) => this.tratarErroCarregamento(erro),
    });
  }

  salvar(): void {
    this.erro.set(null);
    this.salvando.set(true);
    this.api.atualizarEstabelecimento(this.id, this.apelido.trim() || null).subscribe({
      next: () => void this.router.navigateByUrl('/cadastros/estabelecimentos'),
      error: (erro) => {
        this.salvando.set(false);
        this.erro.set(mensagemErro(erro));
      },
    });
  }

  private tratarErroCarregamento(erro: unknown): void {
    if (erro instanceof HttpErrorResponse && (erro.status === 404 || erro.status === 422)) {
      void this.router.navigateByUrl('/cadastros/estabelecimentos');
      return;
    }
    this.carregando.set(false);
    this.erro.set(mensagemErro(erro));
  }
}
