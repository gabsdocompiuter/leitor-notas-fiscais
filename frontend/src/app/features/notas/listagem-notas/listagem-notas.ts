import { CurrencyPipe, DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../../core/api/api.service';
import { Nota, SituacaoNota } from '../../../core/models/api.models';
import { mensagemErro } from '../../../core/utils/erro-api';
import { quantidadeItensPendentes, rotuloSituacao } from '../../../core/utils/nota.utils';
import { EstadoVazio } from '../../../shared/components/estado-vazio/estado-vazio';

type FiltroSituacao = SituacaoNota | 'todas';

@Component({
  selector: 'lnf-listagem-notas',
  imports: [CurrencyPipe, DatePipe, RouterLink, EstadoVazio],
  templateUrl: './listagem-notas.html',
})
export class ListagemNotas implements OnInit {
  private readonly api = inject(ApiService);

  readonly notas = signal<Nota[]>([]);
  readonly carregando = signal(true);
  readonly erro = signal<string | null>(null);
  readonly filtro = signal<FiltroSituacao>('todas');
  ngOnInit(): void {
    this.carregar();
  }

  selecionarFiltro(filtro: FiltroSituacao): void {
    if (this.filtro() === filtro) return;
    this.filtro.set(filtro);
    this.carregar();
  }

  carregar(): void {
    this.carregando.set(true);
    this.erro.set(null);
    const filtroAtual = this.filtro();
    const situacao: SituacaoNota | undefined = filtroAtual === 'todas' ? undefined : filtroAtual;
    this.api.listarNotas(situacao).subscribe({
      next: (notas) => {
        this.notas.set(notas);
        this.carregando.set(false);
      },
      error: (erro) => {
        this.erro.set(mensagemErro(erro));
        this.carregando.set(false);
      },
    });
  }

  readonly rotuloSituacao = rotuloSituacao;
  readonly quantidadeItensPendentes = quantidadeItensPendentes;
}
