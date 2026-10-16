import { CurrencyPipe } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  DestroyRef,
  ElementRef,
  Injector,
  OnDestroy,
  OnInit,
  afterNextRender,
  inject,
  signal,
  viewChildren,
} from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { ApiService } from '../../../core/api/api.service';
import {
  Categoria,
  CompraManualRequest,
  Estabelecimento,
  Marca,
  Produto,
  UnidadeMedidaInfo,
  VariacaoProduto,
} from '../../../core/models/api.models';
import { mensagemErro } from '../../../core/utils/erro-api';
import { formatarVariacao, validarDecimal } from '../../../core/utils/decimal.utils';
import { valoresItem } from '../../../core/utils/valor-item.utils';
import { DecimalInput } from '../../../shared/directives/decimal-input';
import { PesquisaProduto } from '../../cadastros/produtos/pesquisa-produto/pesquisa-produto';
import { PesquisaMarca } from '../../cadastros/marcas/pesquisa-marca/pesquisa-marca';
import { PesquisaVariacao } from '../../cadastros/produtos/pesquisa-variacao/pesquisa-variacao';
import { PesquisaEstabelecimento } from '../../cadastros/estabelecimentos/pesquisa-estabelecimento/pesquisa-estabelecimento';

type Seletor = 'estabelecimento' | 'produto' | 'marca' | 'variacao';

export function dataLocalHoje(data = new Date()): string {
  return new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(data);
}

@Component({
  selector: 'lnf-compra-manual',
  imports: [
    CurrencyPipe,
    ReactiveFormsModule,
    RouterLink,
    DecimalInput,
    PesquisaProduto,
    PesquisaMarca,
    PesquisaVariacao,
    PesquisaEstabelecimento,
  ],
  templateUrl: './compra-manual.html',
})
export class CompraManual implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly injector = inject(Injector);
  private readonly detectorMudancas = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);
  private readonly cartoes = viewChildren<ElementRef<HTMLElement>>('cartaoItem');
  private origemFoco: HTMLElement | null = null;
  private indiceModal = 0;

  readonly estabelecimentos = signal<Estabelecimento[]>([]);
  readonly estabelecimento = signal<Estabelecimento | null>(null);
  readonly produtos = signal<Produto[]>([]);
  readonly categorias = signal<Categoria[]>([]);
  readonly marcas = signal<Marca[]>([]);
  readonly unidades = signal<UnidadeMedidaInfo[]>([]);
  readonly variacoes = signal<VariacaoProduto[]>([]);
  readonly carregando = signal(true);
  readonly carregandoVariacoes = signal(false);
  readonly salvando = signal(false);
  readonly erro = signal<string | null>(null);
  readonly modal = signal<Seletor | null>(null);

  readonly itens = this.fb.array<FormGroup>([]);
  readonly formulario = this.fb.group({
    estabelecimento_id: ['', Validators.required],
    data: [dataLocalHoje(), Validators.required],
    itens: this.itens,
  });

  constructor() {
    this.adicionarItem(false);
  }

  ngOnInit(): void {
    this.carregar();
  }

  ngOnDestroy(): void {
    if (this.modal()) document.body.classList.remove('modal-open');
  }

  carregar(): void {
    this.carregando.set(true);
    this.erro.set(null);
    forkJoin({
      estabelecimentos: this.api.listarEstabelecimentos(),
      produtos: this.api.listarProdutos(),
      categorias: this.api.listarCategorias(),
      marcas: this.api.listarMarcas(),
      unidades: this.api.listarUnidadesMedida(),
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (dados) => {
          this.estabelecimentos.set(dados.estabelecimentos);
          this.produtos.set(dados.produtos);
          this.categorias.set(dados.categorias);
          this.marcas.set(dados.marcas);
          this.unidades.set(dados.unidades);
          this.carregando.set(false);
        },
        error: (erro) => {
          this.erro.set(mensagemErro(erro));
          this.carregando.set(false);
        },
      });
  }

  ocupado(): boolean {
    return this.salvando() || this.carregando() || this.carregandoVariacoes();
  }

  adicionarItem(focar = true): void {
    if (this.salvando()) return;
    const form = this.fb.group({
      produto_id: ['', Validators.required],
      marca_id: [null as string | null],
      variacao_id: [null as string | null],
      quantidade_confirmada: [1, [Validators.required, Validators.min(0.001), validarDecimal]],
      tipo_quantidade: ['unidades'],
      tipo_valor: ['total'],
      unidades_por_pacote: [null as number | null],
      valor_total: [
        null as number | null,
        [
          Validators.required,
          Validators.min(0),
          Validators.max(9999999999999.99),
          Validators.pattern(/^\d+(?:\.\d{1,2})?$/),
          validarDecimal,
        ],
      ],
    });
    form.controls.tipo_quantidade.valueChanges.subscribe(() => this.configurarQuantidade(form));
    form.valueChanges.subscribe(() => this.detectorMudancas.markForCheck());
    this.itens.push(form);
    if (focar) {
      afterNextRender(
        () => {
          const cartao = this.cartoes().at(-1)?.nativeElement;
          cartao?.scrollIntoView({ block: 'nearest' });
          cartao?.querySelector<HTMLButtonElement>('[data-produto]')?.focus();
        },
        { injector: this.injector },
      );
    }
  }

  removerItem(indice: number): void {
    if (this.ocupado() || this.itens.length <= 1) return;
    this.itens.removeAt(indice);
    afterNextRender(
      () => {
        this.cartoes()
          [Math.min(indice, this.itens.length - 1)]?.nativeElement.querySelector<HTMLButtonElement>(
            '[data-produto]',
          )
          ?.focus();
      },
      { injector: this.injector },
    );
  }

  produto(form: FormGroup): Produto | null {
    return this.produtos().find((produto) => produto.id === form.get('produto_id')?.value) ?? null;
  }

  produtoModal(): Produto | null {
    return this.produto(this.itens.at(this.indiceModal));
  }

  nomeMarca(form: FormGroup): string {
    return (
      this.marcas().find((marca) => marca.id === form.get('marca_id')?.value)?.nome ??
      'Pesquisar marca'
    );
  }

  nomeVariacao(form: FormGroup): string {
    const variacao = this.variacoes().find((v) => v.id === form.get('variacao_id')?.value);
    return variacao ? formatarVariacao(variacao) : 'Pesquisar variação';
  }

  unidade(form: FormGroup): string {
    const produto = this.produto(form);
    return produto?.tratar_apenas_como_unidades || produto?.contem_variacoes
      ? 'unidades'
      : (produto?.unidade_medida ?? '');
  }

  usaPacotes(form: FormGroup): boolean {
    return (
      !!this.produto(form)?.tratar_apenas_como_unidades &&
      form.get('tipo_quantidade')?.value === 'pacotes'
    );
  }

  quantidade(form: FormGroup): number {
    const quantidade = Number(form.get('quantidade_confirmada')?.value);
    return this.usaPacotes(form)
      ? quantidade * Number(form.get('unidades_por_pacote')?.value)
      : quantidade;
  }

  valorItem(form: FormGroup): ReturnType<typeof valoresItem> {
    return valoresItem(form.get('valor_total')?.value ?? null, this.quantidade(form), form.get('tipo_valor')?.value);
  }

  precoUnitario(form: FormGroup): number {
    return this.valorItem(form).unitario ?? 0;
  }

  total(): number {
    // Soma em centavos; o servidor também valida e calcula com Decimal.
    return (
      this.itens.controls.reduce((total, form) => {
        const valor = this.valorItem(form).total ?? 0;
        return total + (Number.isFinite(valor) ? Math.round(valor * 100) : 0);
      }, 0) / 100
    );
  }

  invalido(form: FormGroup, campo: string): boolean {
    const controle = form.get(campo);
    return !!controle?.invalid && !!controle.touched;
  }

  abrirSeletor(tipo: Seletor, indice = 0): void {
    if (this.ocupado()) return;
    this.indiceModal = indice;
    this.origemFoco = document.activeElement as HTMLElement | null;
    if (tipo === 'variacao') {
      const produto = this.produtoModal();
      if (!produto) return;
      this.carregandoVariacoes.set(true);
      this.api
        .listarVariacoes(produto.id)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (registros) => {
            this.variacoes.update((atuais) => [
              ...atuais.filter((v) => v.produto_id !== produto.id),
              ...registros,
            ]);
            this.carregandoVariacoes.set(false);
            this.mostrarModal(tipo);
          },
          error: (erro) => {
            this.erro.set(mensagemErro(erro));
            this.carregandoVariacoes.set(false);
          },
        });
      return;
    }
    this.mostrarModal(tipo);
  }

  private mostrarModal(tipo: Seletor): void {
    this.modal.set(tipo);
    document.body.classList.add('modal-open');
  }

  fecharSeletor(): void {
    this.modal.set(null);
    document.body.classList.remove('modal-open');
    afterNextRender(() => this.origemFoco?.focus(), { injector: this.injector });
  }

  tecladoModal(evento: KeyboardEvent): void {
    if (!this.modal() || evento.key !== 'Tab') return;
    const dialogo = (evento.target as HTMLElement).closest('.modal');
    const campos = Array.from(
      dialogo?.querySelectorAll<HTMLElement>(
        'button:not(:disabled), input:not(:disabled), select:not(:disabled), a[href]',
      ) ?? [],
    ).filter((campo) => campo.getClientRects().length > 0);
    const primeiro = campos[0];
    const ultimo = campos.at(-1);
    if (evento.shiftKey && document.activeElement === primeiro) {
      evento.preventDefault();
      ultimo?.focus();
    } else if (!evento.shiftKey && document.activeElement === ultimo) {
      evento.preventDefault();
      primeiro?.focus();
    }
  }

  selecionarEstabelecimento(registro: Estabelecimento): void {
    this.estabelecimento.set(registro);
    this.formulario.controls.estabelecimento_id.setValue(registro.id);
    this.fecharSeletor();
  }

  selecionarProduto(produto: Produto): void {
    const form = this.itens.at(this.indiceModal);
    const mudou = this.produto(form)?.id !== produto.id;
    form.patchValue({
      produto_id: produto.id,
      marca_id: mudou || produto.nao_solicitar_marca ? null : form.get('marca_id')?.value,
      variacao_id: mudou ? null : form.get('variacao_id')?.value,
      tipo_quantidade: mudou ? 'unidades' : form.get('tipo_quantidade')?.value,
      unidades_por_pacote: mudou ? null : form.get('unidades_por_pacote')?.value,
    });
    form.get('marca_id')?.setValidators(produto.nao_solicitar_marca ? [] : [Validators.required]);
    form.get('variacao_id')?.setValidators(produto.contem_variacoes ? [Validators.required] : []);
    form.get('marca_id')?.updateValueAndValidity();
    form.get('variacao_id')?.updateValueAndValidity();
    this.configurarQuantidade(form);
    this.fecharSeletor();
  }

  selecionarMarca(marca: Marca): void {
    this.itens.at(this.indiceModal).patchValue({ marca_id: marca.id });
    this.fecharSeletor();
  }

  selecionarVariacao(variacao: VariacaoProduto): void {
    this.itens.at(this.indiceModal).patchValue({ variacao_id: variacao.id });
    this.fecharSeletor();
  }

  registrarProduto(produto: Produto): void {
    this.produtos.update((atuais) => [...atuais, produto]);
  }
  registrarMarca(marca: Marca): void {
    this.marcas.update((atuais) => [...atuais, marca]);
  }
  registrarCategoria(categoria: Categoria): void {
    this.categorias.update((atuais) => [...atuais, categoria]);
  }
  registrarVariacao(variacao: VariacaoProduto): void {
    this.variacoes.update((atuais) => [...atuais, variacao]);
  }
  registrarEstabelecimento(registro: Estabelecimento): void {
    this.estabelecimentos.update((atuais) => [...atuais, registro]);
  }

  private configurarQuantidade(form: FormGroup): void {
    const produto = this.produto(form);
    const inteiras = produto?.tratar_apenas_como_unidades || produto?.contem_variacoes;
    const validadores = [Validators.required, Validators.min(0.001), validarDecimal];
    if (inteiras)
      validadores.push(Validators.pattern(/^\d+$/), Validators.max(Number.MAX_SAFE_INTEGER));
    form.get('quantidade_confirmada')?.setValidators(validadores);
    form.get('quantidade_confirmada')?.updateValueAndValidity({ emitEvent: false });
    form
      .get('unidades_por_pacote')
      ?.setValidators(
        this.usaPacotes(form)
          ? [
              Validators.required,
              Validators.min(1),
              Validators.max(Number.MAX_SAFE_INTEGER),
              Validators.pattern(/^\d+$/),
              validarDecimal,
            ]
          : [],
      );
    form.get('unidades_por_pacote')?.updateValueAndValidity({ emitEvent: false });
  }

  concluir(): void {
    if (this.ocupado()) return;
    this.formulario.markAllAsTouched();
    const pacotesInvalidos = this.itens.controls.some(
      (form) => this.usaPacotes(form) && !Number.isSafeInteger(this.quantidade(form)),
    );
    const valoresInvalidos = this.itens.controls.some((form) => {
      const valor = this.valorItem(form).total;
      return valor === null || !Number.isFinite(valor) || valor > 9999999999999.99;
    });
    if (this.formulario.invalid || pacotesInvalidos || valoresInvalidos) {
      this.erro.set(
        'Revise os campos destacados. Informe valores com até duas casas decimais e quantidades válidas.',
      );
      return;
    }
    const compra: CompraManualRequest = {
      estabelecimento_id: this.formulario.controls.estabelecimento_id.value!,
      data: this.formulario.controls.data.value!,
      itens: this.itens.controls.map((form) => ({
        produto_id: form.get('produto_id')!.value,
        marca_id: form.get('marca_id')!.value,
        variacao_id: form.get('variacao_id')!.value,
        quantidade_confirmada: this.quantidade(form),
        quantidade_pacotes: this.usaPacotes(form)
          ? Number(form.get('quantidade_confirmada')!.value)
          : null,
        unidades_por_pacote: this.usaPacotes(form)
          ? Number(form.get('unidades_por_pacote')!.value)
          : null,
        ...(form.get('tipo_valor')?.value === 'unitario'
          ? { valor_unitario: Number(form.get('valor_total')!.value).toFixed(2) }
          : { valor_total: Number(form.get('valor_total')!.value).toFixed(2) }),
      })),
    };
    this.salvando.set(true);
    this.erro.set(null);
    this.api
      .criarCompraManual(compra)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (nota) => {
          void this.router.navigate(['/notas', nota.id, 'revisao']);
        },
        error: (erro) => {
          this.salvando.set(false);
          this.erro.set(mensagemErro(erro));
        },
      });
  }
}
