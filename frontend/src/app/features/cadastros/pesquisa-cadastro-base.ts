import {
  AfterViewInit,
  Directive,
  ElementRef,
  OnInit,
  computed,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';

import { filtrarCatalogo } from '../../core/utils/catalogo.utils';
import { mensagemErro } from '../../core/utils/erro-api';

@Directive()
export abstract class PesquisaCadastroBase<T extends { id: string }>
  implements OnInit, AfterViewInit
{
  readonly registros = input.required<readonly T[]>();
  readonly contexto = input('');
  readonly buscaInicial = input('');

  readonly fechar = output<void>();
  readonly registroSelecionado = output<T>();
  readonly cadastroCriado = output<T>();

  readonly busca = signal('');
  readonly cadastroAberto = signal(false);
  readonly salvando = signal(false);
  readonly erro = signal<string | null>(null);
  readonly resultados = computed(() =>
    filtrarCatalogo([...this.registros()], this.busca(), (registro) =>
      this.textoPesquisa(registro),
    ),
  );

  private readonly campoBusca = viewChild<ElementRef<HTMLInputElement>>('campoBusca');

  abstract readonly tituloPesquisa: string;
  abstract readonly tituloCadastro: string;
  abstract readonly placeholderPesquisa: string;
  abstract readonly mensagemSemResultados: string;

  ngOnInit(): void {
    this.busca.set(this.buscaInicial());
  }

  ngAfterViewInit(): void {
    this.focarPesquisa();
  }

  atualizarBusca(evento: Event): void {
    this.busca.set((evento.target as HTMLInputElement).value);
  }

  abrirCadastro(): void {
    this.erro.set(null);
    this.prepararCadastro(this.busca().trim());
    this.cadastroAberto.set(true);
  }

  voltarParaPesquisa(): void {
    if (this.salvando()) return;
    this.erro.set(null);
    this.cadastroAberto.set(false);
    this.focarPesquisa();
  }

  solicitarFechamento(): void {
    if (!this.salvando()) this.fechar.emit();
  }

  selecionar(registro: T): void {
    if (!this.salvando()) this.registroSelecionado.emit(registro);
  }

  protected concluirCadastro(registro: T): void {
    this.salvando.set(false);
    this.cadastroCriado.emit(registro);
    this.registroSelecionado.emit(registro);
  }

  protected tratarErro(erro: unknown): void {
    this.erro.set(mensagemErro(erro));
    this.salvando.set(false);
  }

  protected abstract textoPesquisa(registro: T): string;
  protected abstract prepararCadastro(nomeInicial: string): void;

  private focarPesquisa(): void {
    setTimeout(() => {
      const campo = this.campoBusca()?.nativeElement;
      campo?.focus();
      campo?.select();
    });
  }
}
