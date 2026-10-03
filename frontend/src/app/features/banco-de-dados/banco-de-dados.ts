import {
  Component,
  ElementRef,
  Injector,
  OnInit,
  afterNextRender,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { finalize } from 'rxjs';

import { ApiService } from '../../core/api/api.service';
import { mensagemErro } from '../../core/utils/erro-api';

@Component({
  selector: 'lnf-banco-de-dados',
  templateUrl: './banco-de-dados.html',
})
export class BancoDeDados implements OnInit {
  private readonly api = inject(ApiService);
  private readonly injector = inject(Injector);
  private readonly dialogo = viewChild<ElementRef<HTMLElement>>('dialogo');
  private readonly botaoImportar = viewChild<ElementRef<HTMLButtonElement>>('botaoImportar');
  readonly permitirImportacao = signal(false);
  readonly processando = signal(false);
  readonly confirmando = signal(false);
  readonly arquivo = signal<File | null>(null);
  readonly erro = signal<string | null>(null);
  readonly sucesso = signal<string | null>(null);
  readonly limite = 100 * 1024 * 1024;

  ngOnInit(): void {
    this.api.obterConfiguracaoBanco().subscribe({
      next: (configuracao) => this.permitirImportacao.set(configuracao.permitir_importacao),
      error: () => this.permitirImportacao.set(false),
    });
  }

  selecionar(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    const arquivo = input.files?.[0] ?? null;
    this.erro.set(null);
    this.sucesso.set(null);
    this.arquivo.set(null);
    if (!arquivo) return;
    if (!/\.(sqlite3|sqlite|db)$/i.test(arquivo.name)) {
      this.erro.set('Selecione um arquivo .sqlite3, .sqlite ou .db.');
      input.value = '';
      return;
    }
    if (arquivo.size === 0 || arquivo.size > this.limite) {
      this.erro.set('O arquivo deve conter dados e ter no máximo 100 MiB.');
      input.value = '';
      return;
    }
    this.arquivo.set(arquivo);
  }

  tamanhoArquivo(): string {
    return ((this.arquivo()?.size ?? 0) / (1024 * 1024)).toFixed(2) + ' MiB';
  }

  pedirConfirmacao(): void {
    if (this.permitirImportacao() && this.arquivo() && !this.processando()) {
      this.confirmando.set(true);
      afterNextRender(
        () => {
          this.dialogo()
            ?.nativeElement.querySelector<HTMLButtonElement>('[data-cancelar]')
            ?.focus();
        },
        { injector: this.injector },
      );
    }
  }

  cancelar(): void {
    this.confirmando.set(false);
    this.botaoImportar()?.nativeElement.focus();
  }

  tecladoDialogo(evento: KeyboardEvent): void {
    if (evento.key === 'Escape') {
      evento.preventDefault();
      this.cancelar();
    }
    if (evento.key !== 'Tab') return;
    const botoes = this.dialogo()?.nativeElement.querySelectorAll<HTMLButtonElement>('button');
    if (!botoes?.length) return;
    const primeiro = botoes[0];
    const ultimo = botoes[botoes.length - 1];
    if (evento.shiftKey && document.activeElement === primeiro) {
      evento.preventDefault();
      ultimo.focus();
    } else if (!evento.shiftKey && document.activeElement === ultimo) {
      evento.preventDefault();
      primeiro.focus();
    }
  }

  importar(): void {
    const arquivo = this.arquivo();
    if (!this.confirmando() || !this.permitirImportacao() || !arquivo || this.processando()) return;
    this.confirmando.set(false);
    this.processando.set(true);
    this.erro.set(null);
    this.sucesso.set(null);
    this.api
      .importarBanco(arquivo)
      .pipe(finalize(() => this.processando.set(false)))
      .subscribe({
        next: (resposta) => {
          this.sucesso.set(resposta.mensagem);
          this.recarregar();
        },
        error: (erro) => {
          this.erro.set(mensagemErro(erro));
          if (erro.status === 403) this.permitirImportacao.set(false);
        },
      });
  }

  recarregar(): void {
    window.location.assign('/notas');
  }

  exportar(): void {
    if (this.processando()) return;
    this.processando.set(true);
    this.erro.set(null);
    this.sucesso.set(null);
    this.api
      .exportarBanco()
      .pipe(finalize(() => this.processando.set(false)))
      .subscribe({
        next: (resposta) => {
          if (!resposta.body) {
            this.erro.set('Não foi possível baixar o banco.');
            return;
          }
          const nome =
            /filename="?([^";]+)"?/i.exec(resposta.headers.get('Content-Disposition') ?? '')?.[1] ??
            'notas.sqlite3';
          const url = URL.createObjectURL(resposta.body);
          const link = document.createElement('a');
          link.href = url;
          link.download = nome;
          document.body.appendChild(link);
          link.click();
          link.remove();
          URL.revokeObjectURL(url);
          this.sucesso.set('Exportação concluída.');
        },
        error: async (erro) => {
          // Respostas de erro também chegam como Blob neste endpoint.
          if (erro.error instanceof Blob) {
            try {
              const resposta = JSON.parse(await erro.error.text());
              this.erro.set(resposta.mensagem ?? mensagemErro(erro));
              return;
            } catch {
              /* Usa a mensagem padrão abaixo. */
            }
          }
          this.erro.set(mensagemErro(erro));
        },
      });
  }
}
