import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';

import { ApiService } from '../../core/api/api.service';
import { GrupoRelatorio, ItensRelatorio, RelatorioMensal } from '../../core/models/api.models';
import { mensagemErro } from '../../core/utils/erro-api';
import { deslocarMes, formatarMes, mesValido } from '../../core/utils/mes.utils';

type FiltroItens = { tipo: 'categoria' | 'tag'; grupo: GrupoRelatorio };

@Component({
  selector: 'lnf-relatorios',
  imports: [CurrencyPipe, DatePipe, DecimalPipe, RouterLink],
  templateUrl: './relatorios.html',
})
export class Relatorios implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private consulta?: Subscription;
  private consultaItens?: Subscription;

  readonly mes = signal(formatarMes(new Date()));
  readonly relatorio = signal<RelatorioMensal | null>(null);
  readonly carregando = signal(false);
  readonly erro = signal<string | null>(null);
  readonly filtro = signal<FiltroItens | null>(null);
  readonly pagina = signal<ItensRelatorio | null>(null);
  readonly carregandoItens = signal(false);
  readonly erroItens = signal<string | null>(null);
  readonly deslocamento = signal(0);
  readonly limite = 50;

  ngOnInit(): void {
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((parametros) => {
      const valor = parametros.get('mes');
      this.mes.set(valor && mesValido(valor) ? valor : formatarMes(new Date()));
      this.carregar();
    });
    this.destroyRef.onDestroy(() => {
      this.consulta?.unsubscribe();
      this.consultaItens?.unsubscribe();
    });
  }

  selecionarMesCampo(evento: Event): void {
    const campo = evento.target as HTMLInputElement;
    if (!mesValido(campo.value)) {
      campo.value = this.mes();
      return;
    }
    this.selecionarMes(campo.value);
  }

  selecionarMes(mes: string): void {
    if (!mesValido(mes)) return;
    void this.router.navigate([], { relativeTo: this.route, queryParams: { mes } });
  }

  navegarMes(quantidade: number): void {
    this.selecionarMes(deslocarMes(this.mes(), quantidade));
  }

  carregar(): void {
    this.consulta?.unsubscribe();
    this.limparFiltro();
    this.relatorio.set(null);
    this.carregando.set(true);
    this.erro.set(null);
    this.consulta = this.api.obterRelatorioMensal(this.mes()).subscribe({
      next: (relatorio) => {
        this.relatorio.set(relatorio);
        this.carregando.set(false);
      },
      error: (erro) => {
        this.erro.set(mensagemErro(erro));
        this.carregando.set(false);
      },
    });
  }

  selecionarGrupo(tipo: FiltroItens['tipo'], grupo: GrupoRelatorio): void {
    this.filtro.set({ tipo, grupo });
    this.deslocamento.set(0);
    this.carregarItens();
  }

  limparFiltro(): void {
    this.consultaItens?.unsubscribe();
    this.filtro.set(null);
    this.pagina.set(null);
    this.erroItens.set(null);
    this.carregandoItens.set(false);
    this.deslocamento.set(0);
  }

  navegarItens(quantidade: number): void {
    this.deslocamento.update((atual) => Math.max(0, atual + quantidade * this.limite));
    this.carregarItens();
  }

  carregarItens(): void {
    const filtro = this.filtro();
    if (!filtro) return;
    this.consultaItens?.unsubscribe();
    this.pagina.set(null);
    this.erroItens.set(null);
    this.carregandoItens.set(true);
    this.consultaItens = this.api
      .listarItensRelatorio(
        this.mes(),
        filtro.tipo === 'categoria' ? filtro.grupo.id : undefined,
        filtro.tipo === 'tag' ? filtro.grupo.id : undefined,
        this.deslocamento(),
      )
      .subscribe({
        next: (pagina) => {
          this.pagina.set(pagina);
          this.carregandoItens.set(false);
        },
        error: (erro) => {
          this.erroItens.set(mensagemErro(erro));
          this.carregandoItens.set(false);
        },
      });
  }

  percentual(valor: string): number {
    const total = Number(this.relatorio()?.total_pago ?? 0);
    return total > 0 ? (Number(valor) / total) * 100 : 0;
  }

  diferencaMesAnterior(): number {
    const relatorio = this.relatorio();
    return relatorio ? Number(relatorio.total_pago) - Number(relatorio.total_mes_anterior) : 0;
  }
}
