import { CurrencyPipe, DatePipe } from '@angular/common';
import {
  ChangeDetectorRef, Component, ElementRef, Injector, OnDestroy, OnInit, afterNextRender, inject, signal, viewChild, viewChildren,
} from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin, Observable, switchMap } from 'rxjs';

import { ApiService } from '../../../core/api/api.service';
import {
  Categoria,
  Estabelecimento,
  ItemNota,
  Marca,
  Nota,
  Produto,
  RevisaoItem,
  UnidadeMedidaInfo,
  VariacaoProduto,
} from '../../../core/models/api.models';
import { deslocarMes } from '../../../core/utils/mes.utils';
import { capitalizarIniciais } from '../../../core/utils/catalogo.utils';
import { mensagemErro } from '../../../core/utils/erro-api';
import { quantidadeItensPendentes, todosItensRevisados } from '../../../core/utils/nota.utils';
import {
  formatarDecimal,
  formatarVariacao,
  validarDecimal,
} from '../../../core/utils/decimal.utils';
import { valoresItem } from '../../../core/utils/valor-item.utils';
import { DecimalInput } from '../../../shared/directives/decimal-input';
import { sugerirQuantidade } from '../../../core/utils/quantidade.utils';
import { EstadoVazio } from '../../../shared/components/estado-vazio/estado-vazio';
import { PesquisaMarca } from '../../cadastros/marcas/pesquisa-marca/pesquisa-marca';
import { PesquisaProduto } from '../../cadastros/produtos/pesquisa-produto/pesquisa-produto';
import { PesquisaVariacao } from '../../cadastros/produtos/pesquisa-variacao/pesquisa-variacao';

import { SeletorTags } from '../../../shared/components/seletor-tags/seletor-tags';

type TipoModal = 'produto' | 'marca' | 'variacao';

@Component({
  selector: 'lnf-revisao-notas',
  imports: [
    CurrencyPipe,
    DecimalInput,
    DatePipe,
    FormsModule,
    ReactiveFormsModule,
    RouterLink,
    EstadoVazio,
    PesquisaMarca,
    PesquisaProduto,
    PesquisaVariacao,
    SeletorTags,
  ],
  templateUrl: './revisao-notas.html',
})
export class RevisaoNotas implements OnInit, OnDestroy {
  readonly formatarDecimal = formatarDecimal;
  private readonly api = inject(ApiService);
  private readonly injector = inject(Injector);
  private readonly detectorMudancas = inject(ChangeDetectorRef);
  private readonly cartoesItens = viewChildren<ElementRef<HTMLElement>>('cartaoItem');
  private readonly bannerImportacao = viewChild<ElementRef<HTMLElement>>('bannerImportacao');
  private readonly dialogoIgnorar = viewChild<ElementRef<HTMLElement>>('dialogoIgnorar');
  private origemIgnorar: HTMLInputElement | null = null;
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly chave = this.route.snapshot.paramMap.get('chave') ?? '';
  private readonly formularios = new Map<string, FormGroup>();

  readonly salvandoMetadados = signal(false);
  readonly confirmacaoIgnorar = signal<{ item: ItemNota | null } | null>(null);

  readonly nota = signal<Nota | null>(null);
  readonly novoItem = signal<ItemNota | null>(null);
  itensExibidos(): ItemNota[] {
    const itens = this.nota()?.itens ?? [];
    const novo = this.novoItem();
    return novo ? [...itens, novo] : itens;
  }
  readonly produtos = signal<Produto[]>([]);
  readonly categorias = signal<Categoria[]>([]);
  readonly marcas = signal<Marca[]>([]);
  readonly unidades = signal<UnidadeMedidaInfo[]>([]);
  readonly variacoes = signal<VariacaoProduto[]>([]);
  readonly carregando = signal(true);
  readonly erro = signal<string | null>(null);
  readonly sucesso = signal<string | null>(null);
  readonly itemSalvando = signal<string | null>(null);
  readonly itemEditando = signal<string | null>(null);
  readonly importando = signal(false);
  readonly modalAberto = signal(false);
  readonly tipoModal = signal<TipoModal>('produto');
  readonly itemModal = signal<ItemNota | null>(null);
  readonly buscaInicialModal = signal('');
  readonly modalEstabelecimentoAberto = signal(false);
  readonly salvandoEstabelecimento = signal(false);
  readonly erroEstabelecimento = signal<string | null>(null);

  apelidoEstabelecimento = '';

  ngOnInit(): void {
    this.carregar();
  }

  ngOnDestroy(): void {
    if (this.confirmacaoIgnorar()) document.body.classList.remove('modal-open');
  }

  solicitarIgnorar(evento: Event, item: ItemNota | null = null): void {
    const campo = evento.target as HTMLInputElement;
    const ignorar = campo.checked;
    campo.checked = item ? item.ignorado : (this.nota()?.ignorada ?? false);
    if (this.metadadosOcupados() || this.confirmacaoIgnorar()) return;
    if (item && !this.itemEstaEmEdicao(item)) return;
    this.origemIgnorar = campo;
    if (!ignorar) {
      this.salvarIgnorar(false, item);
      return;
    }
    this.erro.set(null);
    this.confirmacaoIgnorar.set({ item });
    document.body.classList.add('modal-open');
    afterNextRender(() => {
      this.dialogoIgnorar()?.nativeElement.querySelector<HTMLButtonElement>('[data-cancelar]')?.focus();
    }, { injector: this.injector });
  }

  cancelarIgnorar(): void {
    if (this.metadadosOcupados()) return;
    this.confirmacaoIgnorar.set(null);
    document.body.classList.remove('modal-open');
    this.restaurarFocoIgnorar();
    afterNextRender(() => this.restaurarFocoIgnorar(), { injector: this.injector });
  }

  private restaurarFocoIgnorar(): void {
    const origem = this.origemIgnorar;
    if (origem?.disabled) {
      origem.closest('article')?.querySelector<HTMLButtonElement>('[aria-label="Editar item"]')?.focus();
    } else {
      origem?.focus();
    }
  }

  confirmarIgnorar(): void {
    const confirmacao = this.confirmacaoIgnorar();
    if (!confirmacao || this.metadadosOcupados()) return;
    this.salvarIgnorar(true, confirmacao.item);
    if (this.salvandoMetadados()) this.dialogoIgnorar()?.nativeElement.focus();
  }

  tecladoIgnorar(evento: KeyboardEvent): void {
    if (evento.key === 'Escape') {
      evento.preventDefault();
      this.cancelarIgnorar();
    }
    if (evento.key !== 'Tab') return;
    const botoes = this.dialogoIgnorar()?.nativeElement.querySelectorAll<HTMLButtonElement>('button:not(:disabled)');
    if (!botoes?.length) {
      evento.preventDefault();
      return;
    }
    const primeiro = botoes[0];
    const ultimo = botoes[botoes.length - 1];
    if (evento.shiftKey && (document.activeElement === primeiro || document.activeElement === this.dialogoIgnorar()?.nativeElement)) {
      evento.preventDefault();
      ultimo.focus();
    } else if (!evento.shiftKey && (document.activeElement === ultimo || document.activeElement === this.dialogoIgnorar()?.nativeElement)) {
      evento.preventDefault();
      primeiro.focus();
    }
  }

  private salvarIgnorar(ignorar: boolean, item: ItemNota | null): void {
    this.salvarMetadados(
      item
        ? this.api.definirItemIgnorado(this.chave, item.id, ignorar)
        : this.api.definirNotaIgnorada(this.chave, ignorar),
      ignorar ? 'Registro ignorado nos relatórios.' : 'Registro incluído novamente nos relatórios.',
      () => {
        if (ignorar && (!item || this.itemEditando() === item.id)) this.itemEditando.set(null);
        const nota = this.nota();
        if (nota) {
          for (const atual of nota.itens) {
            const form = this.formularios.get(atual.id);
            if (form) this.configurarEdicaoQuantidade(form, this.itemEstaEmEdicao(atual));
          }
        }
        if (this.confirmacaoIgnorar()) this.cancelarIgnorar();
      },
    );
  }

  carregar(): void {
    this.carregando.set(true);
    forkJoin({
      nota: this.api.aplicarClassificacoesAutomaticas(this.chave),
      produtos: this.api.listarProdutos(),
      categorias: this.api.listarCategorias(),
      marcas: this.api.listarMarcas(),
      unidades: this.api.listarUnidadesMedida(),
    }).subscribe({
      next: (dados) => {
        this.produtos.set(dados.produtos);
        this.categorias.set(dados.categorias);
        this.marcas.set(dados.marcas);
        this.unidades.set(dados.unidades);
        this.definirNota(dados.nota);
        this.carregando.set(false);
      },
      error: (e) => {
        this.erro.set(mensagemErro(e));
        this.carregando.set(false);
      },
    });
  }

  metadadosOcupados(): boolean {
    return this.salvandoMetadados() || this.importando() || this.itemSalvando() !== null;
  }

  adicionarTag(nome: string, item?: ItemNota): void {
    if (this.metadadosOcupados() || this.nota()?.ignorada || (item?.ignorado && !this.itemEstaEmEdicao(item))) return;
    const operacao = this.api
      .criarTag(nome)
      .pipe(
        switchMap((tag) =>
          item
            ? this.api.definirTagsItem(this.chave, item.id, [
                ...item.tags.map((atual) => atual.id),
                tag.id,
              ])
            : this.api.adicionarTagsEmTodos(this.chave, [tag.id]),
        ),
      );
    this.salvarMetadados(
      operacao,
      item ? 'Tag adicionada ao item.' : 'Tag aplicada a todos os itens.',
    );
  }

  removerTag(item: ItemNota, tagId: string): void {
    if (this.metadadosOcupados() || this.nota()?.ignorada || (item.ignorado && !this.itemEstaEmEdicao(item))) return;
    this.salvarMetadados(
      this.api.definirTagsItem(
        this.chave,
        item.id,
        item.tags.filter((tag) => tag.id !== tagId).map((tag) => tag.id),
      ),
      'Tag removida do item.',
    );
  }

  definirCompetencia(evento: Event): void {
    const campo = evento.target as HTMLInputElement;
    const proximoMes = campo.checked;
    // Exibe o valor salvo até a confirmação e mantém a tela coerente se houver erro.
    campo.checked = this.nota()?.considerar_proximo_mes ?? false;
    if (this.metadadosOcupados() || this.nota()?.ignorada) return;
    this.salvarMetadados(
      this.api.definirCompetencia(this.chave, proximoMes),
      'Mês considerado atualizado.',
    );
  }

  mesConsiderado(): string {
    const nota = this.nota();
    if (!nota) return '';
    const mes = deslocarMes(nota.emissao.slice(0, 7), Number(nota.considerar_proximo_mes));
    const data = new Date(`${mes}-01T12:00:00`);
    return data.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
  }

  private salvarMetadados(operacao: Observable<Nota>, mensagem: string, aoSalvar?: () => void): void {
    this.salvandoMetadados.set(true);
    this.erro.set(null);
    this.sucesso.set(null);
    operacao.subscribe({
      next: (nota) => {
        // Preserva os formulários de classificação que ainda estão em edição.
        this.nota.update((atual) =>
          atual
            ? {
                ...atual,
                considerar_proximo_mes: nota.considerar_proximo_mes,
                ignorada: nota.ignorada,
                situacao: nota.situacao,
                itens: atual.itens.map((item) => ({
                  ...item,
                  ignorado: nota.itens.find((salvo) => salvo.id === item.id)?.ignorado ?? item.ignorado,
                  tags: nota.itens.find((salvo) => salvo.id === item.id)?.tags ?? item.tags,
                })),
              }
            : nota,
        );
        this.salvandoMetadados.set(false);
        this.sucesso.set(mensagem);
        aoSalvar?.();
      },
      error: (erro) => {
        this.erro.set(mensagemErro(erro));
        this.salvandoMetadados.set(false);
      },
    });
  }

  resumoItem(item: ItemNota): {
    descricao: string; quantidade: number | null; unidade: string;
    valor_unitario: number | null; valor_total: number | null;
  } {
    if (this.nota()?.origem !== 'manual') {
      return {
        descricao: item.descricao_original, quantidade: Number(item.quantidade),
        unidade: item.unidade_original, valor_unitario: Number(item.valor_unitario),
        valor_total: Number(item.valor_total),
      };
    }
    const form = this.formularios.get(item.id);
    const editando = this.itemEstaEmEdicao(item) && !!form;
    const produto = editando ? this.produtoSelecionado(item.id) : item.apresentacao?.produto;
    const quantidade = editando
      ? this.usaPacotes(item.id) ? this.totalUnidades(item.id) : this.numero(form.get('quantidade_confirmada')?.value)
      : this.numero(item.quantidade_confirmada ?? item.quantidade);
    const quantidadeValida = quantidade !== null && quantidade > 0 ? quantidade : null;
    const valores = editando
      ? valoresItem(this.numero(form.get('valor_total')?.value), quantidadeValida, form.get('tipo_valor')?.value)
      : {
          total: Number(item.valor_total),
          unitario: Number(item.quantidade) === quantidadeValida
            ? Number(item.valor_unitario)
            : quantidadeValida !== null ? Number(item.valor_total) / quantidadeValida : null,
        };
    return {
      descricao: produto?.nome ?? item.descricao_original,
      quantidade: quantidadeValida,
      unidade: produto
        ? produto.tratar_apenas_como_unidades || produto.contem_variacoes ? 'UN' : produto.unidade_medida ?? ''
        : item.unidade_original,
      valor_total: valores.total,
      valor_unitario: valores.unitario,
    };
  }

  formularioItem(id: string): FormGroup | undefined {
    return this.formularios.get(id);
  }
  produtoSelecionado(id: string): Produto | null {
    const produtoId = this.formularios.get(id)?.get('produto_id')?.value;
    return this.produtos().find((p) => p.id === produtoId) ?? null;
  }
  nomeProdutoSelecionado(id: string): string | null {
    return this.produtoSelecionado(id)?.nome ?? null;
  }
  deveSolicitarMarca(id: string): boolean {
    const produto = this.produtoSelecionado(id);
    return !!produto && !produto.nao_solicitar_marca;
  }
  deveSelecionarVariacao(id: string): boolean {
    return !!this.produtoSelecionado(id)?.contem_variacoes;
  }
  unidadeQuantidade(id: string): string {
    const produto = this.produtoSelecionado(id);
    return produto?.tratar_apenas_como_unidades || produto?.contem_variacoes
      ? 'unidades'
      : (produto?.unidade_medida ?? '');
  }
  passoQuantidade(id: string): string {
    const produto = this.produtoSelecionado(id);
    return produto?.tratar_apenas_como_unidades || produto?.contem_variacoes ? '1' : 'any';
  }
  permitePacotes(id: string): boolean {
    return !!this.produtoSelecionado(id)?.tratar_apenas_como_unidades;
  }
  usaPacotes(id: string): boolean {
    return this.permitePacotes(id) && this.formularios.get(id)?.get('tipo_quantidade')?.value === 'pacotes';
  }
  totalUnidades(id: string): number | null {
    const form = this.formularios.get(id);
    const quantidade = Number(form?.get('quantidade_confirmada')?.value);
    const unidades = Number(form?.get('unidades_por_pacote')?.value);
    const total = quantidade * unidades;
    return Number.isSafeInteger(quantidade) && quantidade > 0 &&
      Number.isSafeInteger(unidades) && unidades > 0 && Number.isSafeInteger(total)
      ? total : null;
  }
  private configurarPacotes(form: FormGroup, produto: Produto | null): void {
    const unidades = form.get('unidades_por_pacote');
    if (produto?.tratar_apenas_como_unidades && form.get('tipo_quantidade')?.value === 'pacotes') {
      unidades?.setValidators([
        Validators.required, Validators.min(1), Validators.max(Number.MAX_SAFE_INTEGER),
        Validators.pattern(/^\d+$/), validarDecimal,
      ]);
    } else {
      unidades?.clearValidators();
    }
    unidades?.updateValueAndValidity({ emitEvent: false });
  }
  nomeMarcaSelecionada(id: string): string {
    const marcaId = this.formularios.get(id)?.get('marca_id')?.value;
    return this.marcas().find((m) => m.id === marcaId)?.nome ?? 'Selecionar marca';
  }
  nomeVariacaoSelecionada(id: string): string {
    const variacaoId = this.formularios.get(id)?.get('variacao_id')?.value;
    const item = this.nota()?.itens.find((i) => i.id === id);
    const variacaoSalva = item?.variacao;
    const nomeSalvo =
      variacaoSalva && variacaoSalva.id === variacaoId
        ? formatarVariacao(variacaoSalva)
        : undefined;
    return (
      this.variacoes()
        .filter((v) => v.id === variacaoId)
        .map(formatarVariacao)[0] ??
      nomeSalvo ??
      'Selecionar variação'
    );
  }
  itemEstaEmEdicao(item: ItemNota): boolean {
    return !this.nota()?.ignorada && (!this.itemConcluido(item) || this.itemEditando() === item.id);
  }
  itemConcluido(item: ItemNota): boolean {
    return item.revisado || item.ignorado;
  }
  requerConfirmacaoUnidades(item: ItemNota): boolean {
    return !item.revisado && item.quantidade_confirmada === null &&
      !!item.apresentacao?.produto.tratar_apenas_como_unidades &&
      ['KG', 'G'].includes(item.unidade_original.trim().toUpperCase()) &&
      this.produtoSelecionado(item.id)?.id === item.apresentacao.produto.id;
  }
  editarItem(item: ItemNota): void {
    if (this.novoItem()) return;
    if (!this.itemConcluido(item) || this.metadadosOcupados() || this.nota()?.ignorada) return;
    const itemAnterior = this.nota()?.itens.find((atual) => atual.id === this.itemEditando());
    if (itemAnterior && itemAnterior.id !== item.id) {
      const formularioAnterior = this.formularios.get(itemAnterior.id);
      if (formularioAnterior) {
        this.restaurarFormulario(itemAnterior, formularioAnterior);
        this.configurarEdicaoQuantidade(formularioAnterior, false);
      }
    }
    this.itemEditando.set(item.id);
    const form = this.formularios.get(item.id);
    if (form) this.configurarEdicaoQuantidade(form, true);
  }
  adicionarItem(): void {
    const nota = this.nota();
    if (!nota || nota.origem !== 'manual' || nota.situacao !== 'importada' ||
        nota.ignorada || this.metadadosOcupados() || this.novoItem() || this.itemEditando()) return;
    const item: ItemNota = {
      id: 'novo-item-manual',
      numero: Math.max(0, ...nota.itens.map((atual) => atual.numero)) + 1,
      codigo: '', descricao_original: 'Novo item',
      quantidade: '1', unidade_original: 'UN', valor_unitario: '', valor_total: '',
      quantidade_confirmada: '1', quantidade_pacotes: null, unidades_por_pacote: null,
      apresentacao: null, variacao: null, revisado: false, ignorado: false,
      alertas: [], tags: [],
    };
    this.novoItem.set(item);
    this.criarFormularioItem(item);
    this.formularios.get(item.id)?.get('valor_total')?.reset(null);
    this.erro.set(null);
    this.sucesso.set(null);
    afterNextRender(() => {
      const cartao = this.cartoesItens().find(
        (atual) => atual.nativeElement.dataset['itemId'] === item.id,
      )?.nativeElement;
      cartao?.querySelector<HTMLButtonElement>('form button')?.focus();
    }, { injector: this.injector });
  }

  cancelarEdicao(item: ItemNota): void {
    if (this.metadadosOcupados()) return;
    if (this.novoItem()?.id === item.id) {
      this.novoItem.set(null);
      this.formularios.delete(item.id);
      this.erro.set(null);
      return;
    }
    this.itemEditando.set(null);
    const form = this.formularios.get(item.id);
    if (form) this.restaurarFormulario(item, form);
  }
  salvarItem(item: ItemNota): void {
    const form = this.formularios.get(item.id);
    if (!form || !this.itemEstaEmEdicao(item) || this.metadadosOcupados()) return;
    form.markAllAsTouched();
    if (form.invalid) {
      this.erro.set('Revise os campos destacados antes de salvar o item.');
      return;
    }
    const pacotes = this.usaPacotes(item.id);
    const total = pacotes ? this.totalUnidades(item.id) : Number(form.get('quantidade_confirmada')?.value);
    if (total === null) {
      this.erro.set('Informe uma quantidade válida de pacotes e unidades por pacote.');
      return;
    }
    if (this.nota()?.origem === 'manual') {
      const valorTotal = this.resumoItem(item).valor_total;
      if (valorTotal === null || valorTotal > 9999999999999.99) {
        this.erro.set('Revise o valor e a quantidade: o total calculado excede o limite permitido.');
        return;
      }
    }
    const valor = form.getRawValue();
    const revisao: RevisaoItem = {
      produto_id: valor.produto_id,
      quantidade_confirmada: total,
      quantidade_pacotes: pacotes ? Number(valor.quantidade_confirmada) : null,
      unidades_por_pacote: pacotes ? Number(valor.unidades_por_pacote) : null,
      variacao_id: valor.variacao_id || null,
    };
    if (this.nota()?.origem === 'manual') {
      if (valor.tipo_valor === 'unitario') revisao.valor_unitario = Number(valor.valor_total).toFixed(2);
      else revisao.valor_total = Number(valor.valor_total).toFixed(2);
    }
    if (this.deveSolicitarMarca(item.id)) revisao.marca_id = valor.marca_id;
    this.itemSalvando.set(item.id);
    this.erro.set(null);
    this.sucesso.set(null);
    const pendentesAntes = new Set(
      this.nota()
        ?.itens.filter((atual) => !atual.revisado && atual.id !== item.id)
        .map((atual) => atual.id),
    );
    const avancarAposSalvar = this.nota()?.situacao !== 'importada';
    const novo = this.novoItem()?.id === item.id;
    const operacao = novo
      ? this.api.adicionarItemManual(this.chave, revisao)
      : this.api.revisarItem(this.chave, item.id, revisao);
    operacao.subscribe({
      next: (nota) => {
        const automaticos = nota.itens.filter(
          (atual) => atual.revisado && pendentesAntes.has(atual.id),
        ).length;
        if (novo) this.novoItem.set(null);
        this.definirNota(nota);
        this.itemSalvando.set(null);
        this.sucesso.set(
          (novo ? `Item ${item.numero} adicionado à compra.` : `Item ${item.numero} revisado.`) +
            (automaticos
              ? ` Mais ${automaticos} ${automaticos === 1 ? 'item igual revisado automaticamente' : 'itens iguais revisados automaticamente'} nesta nota.`
              : ''),
        );
        if (avancarAposSalvar && nota.situacao !== 'importada' && !nota.ignorada) {
          this.rolarParaPendencia(item.id);
        }
      },
      error: (e) => {
        this.erro.set(mensagemErro(e));
        this.itemSalvando.set(null);
      },
    });
  }

  rolarParaPrimeiroPendente(): void {
    this.rolarParaPendencia();
  }

  private rolarParaPendencia(aposItemId?: string): void {
    afterNextRender(() => {
      const nota = this.nota();
      if (!nota || nota.situacao === 'importada' || nota.ignorada) return;
      const indice = nota.itens.findIndex((item) => item.id === aposItemId);
      const pendente = (item: ItemNota) => !this.itemConcluido(item);
      const proximo = nota.itens.slice(indice + 1).find(pendente) ?? nota.itens.find(pendente);
      const destino = proximo
        ? this.cartoesItens().find((cartao) => cartao.nativeElement.dataset['itemId'] === proximo.id)?.nativeElement
        : this.podeImportar(nota) ? this.bannerImportacao()?.nativeElement : undefined;
      if (!destino) return;
      const cabecalho = document.querySelector<HTMLElement>('header.sticky-top');
      const margem = (cabecalho?.getBoundingClientRect().height ?? 0) + 16;
      const movimentoReduzido = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({
        top: Math.max(0, window.scrollY + destino.getBoundingClientRect().top - margem),
        behavior: movimentoReduzido ? 'instant' : 'smooth',
      });
    }, { injector: this.injector });
  }

  concluirImportacao(): void {
    const nota = this.nota();
    if (!nota || !todosItensRevisados(nota) || this.metadadosOcupados()) return;
    this.importando.set(true);
    this.erro.set(null);
    this.api.concluirImportacao(this.chave).subscribe({
      next: (n) => {
        this.definirNota(n);
        this.importando.set(false);
        this.sucesso.set('Nota importada com sucesso.');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      },
      error: (e) => {
        this.erro.set(mensagemErro(e));
        this.importando.set(false);
      },
    });
  }

  abrirSeletor(tipo: TipoModal, item: ItemNota): void {
    const form = this.formularios.get(item.id);
    if (!form || !this.itemEstaEmEdicao(item)) return;
    this.tipoModal.set(tipo);
    this.itemModal.set(item);
    this.buscaInicialModal.set(this.novoItem()?.id === item.id ? '' : capitalizarIniciais(item.descricao_original));
    if (tipo === 'variacao') {
      const produto = this.produtoSelecionado(item.id);
      if (!produto) return;
      this.variacoes.set([]);
      this.api.listarVariacoes(produto.id).subscribe({
        next: (v) => this.variacoes.set(v),
        error: (e) => this.erro.set(mensagemErro(e)),
      });
    }
    this.modalAberto.set(true);
    document.body.classList.add('modal-open');
  }
  fecharSeletor(): void {
    this.modalAberto.set(false);
    this.itemModal.set(null);
    document.body.classList.remove('modal-open');
  }
  abrirEdicaoEstabelecimento(): void {
    if (this.nota()?.ignorada || this.metadadosOcupados()) return;
    const estabelecimento = this.nota()?.estabelecimento;
    if (!estabelecimento) return;
    this.apelidoEstabelecimento = estabelecimento.apelido ?? '';
    this.erroEstabelecimento.set(null);
    this.modalEstabelecimentoAberto.set(true);
    document.body.classList.add('modal-open');
  }
  fecharEdicaoEstabelecimento(): void {
    if (this.salvandoEstabelecimento()) return;
    this.modalEstabelecimentoAberto.set(false);
    document.body.classList.remove('modal-open');
  }
  salvarEstabelecimento(): void {
    const estabelecimento = this.nota()?.estabelecimento;
    if (!estabelecimento || this.salvandoEstabelecimento() || this.nota()?.ignorada) return;
    this.salvandoEstabelecimento.set(true);
    this.erroEstabelecimento.set(null);
    this.api
      .atualizarEstabelecimento(estabelecimento.id, this.apelidoEstabelecimento.trim() || null)
      .subscribe({
        next: (atualizado) => {
          this.atualizarEstabelecimentoNaNota(atualizado);
          this.salvandoEstabelecimento.set(false);
          this.fecharEdicaoEstabelecimento();
          this.sucesso.set('Apelido do estabelecimento atualizado.');
        },
        error: (erro) => {
          this.salvandoEstabelecimento.set(false);
          this.erroEstabelecimento.set(mensagemErro(erro));
        },
      });
  }
  selecionarProduto(produto: Produto): void {
    const item = this.itemModal();
    if (!item) return;
    const form = this.formularios.get(item.id);
    if (!form) return;
    const mudou = form.get('produto_id')?.value !== produto.id;
    const quantidadeManual = this.usaPacotes(item.id)
      ? this.totalUnidades(item.id) : form.get('quantidade_confirmada')?.value;
    form.patchValue({
      produto_id: produto.id,
      variacao_id: mudou ? null : form.get('variacao_id')?.value,
    });
    if (mudou) form.patchValue({ tipo_quantidade: 'unidades', unidades_por_pacote: null });
    this.configurarCamposProduto(form, produto, mudou ? null : form.get('marca_id')?.value);
    if (mudou) {
      if (this.nota()?.origem === 'manual') form.patchValue({ quantidade_confirmada: quantidadeManual });
      else this.preencherQuantidade(item, form, produto);
    }
    this.fecharSeletor();
  }
  selecionarMarca(marca: Marca): void {
    const item = this.itemModal();
    if (item) this.formularios.get(item.id)?.patchValue({ marca_id: marca.id });
    this.fecharSeletor();
  }
  selecionarVariacao(v: VariacaoProduto): void {
    const item = this.itemModal();
    if (item) this.formularios.get(item.id)?.patchValue({ variacao_id: v.id });
    this.fecharSeletor();
  }

  registrarProduto(produto: Produto): void {
    this.adicionarOrdenado(this.produtos, produto, (p) => p.nome);
  }
  registrarMarca(marca: Marca): void {
    this.adicionarOrdenado(this.marcas, marca, (m) => m.nome);
  }
  registrarCategoria(categoria: Categoria): void {
    this.adicionarOrdenado(this.categorias, categoria, (c) => c.nome);
  }
  registrarVariacao(variacao: VariacaoProduto): void {
    this.adicionarOrdenado(this.variacoes, variacao, (v) => v.nome_exibicao);
  }

  itensPendentes(n: Nota): number {
    return quantidadeItensPendentes(n);
  }
  itensIgnorados(n: Nota): number {
    return n.itens.filter((item) => item.ignorado).length;
  }
  itensRevisados(n: Nota): number {
    return n.itens.filter((item) => !item.ignorado && item.revisado).length;
  }
  podeImportar(n: Nota): boolean {
    return todosItensRevisados(n);
  }

  private definirNota(nota: Nota): void {
    this.nota.set(nota);
    this.itemEditando.set(null);
    const novo = this.novoItem();
    const formularioNovo = novo ? this.formularios.get(novo.id) : null;
    this.formularios.clear();
    nota.itens.forEach((item) => this.criarFormularioItem(item));
    if (novo && formularioNovo) this.formularios.set(novo.id, formularioNovo);
  }

  private criarFormularioItem(item: ItemNota): void {
    const form = this.fb.group({
      produto_id: ['', Validators.required],
      marca_id: [null as string | null],
      variacao_id: [null as string | null],
      quantidade_confirmada: [null as number | null],
      tipo_quantidade: ['unidades'],
      tipo_valor: ['total'],
      unidades_por_pacote: [null as number | null],
      valor_total: [null as number | null],
    });
    this.restaurarFormulario(item, form);
    this.formularios.set(item.id, form);
    form.valueChanges.subscribe(() => this.detectorMudancas.markForCheck());
    form.get('tipo_quantidade')?.valueChanges.subscribe(() =>
      this.configurarPacotes(form, this.produtoSelecionado(item.id)),
    );
  }

  private restaurarFormulario(item: ItemNota, form: FormGroup): void {
    const produto = item.apresentacao?.produto ?? null;
    form.reset({
      produto_id: produto?.id ?? '',
      valor_total: this.numero(item.valor_total),
      tipo_valor: 'total',
      marca_id: item.apresentacao?.marca?.id ?? null,
      variacao_id: item.variacao?.id ?? null,
      quantidade_confirmada: this.numero(item.quantidade_pacotes ?? item.quantidade_confirmada),
      tipo_quantidade: item.quantidade_pacotes != null && item.unidades_por_pacote != null
        ? 'pacotes' : 'unidades',
      unidades_por_pacote: this.numero(item.unidades_por_pacote),
    });
    const valorTotal = form.get('valor_total');
    valorTotal?.setValidators(this.nota()?.origem === 'manual'
      ? [Validators.required, Validators.min(0), Validators.max(9999999999999.99),
          Validators.pattern(/^\d+(?:\.\d{1,2})?$/), validarDecimal]
      : []);
    valorTotal?.updateValueAndValidity({ emitEvent: false });
    this.configurarCamposProduto(form, produto, item.apresentacao?.marca?.id ?? null);
    if (item.quantidade_confirmada === null && produto)
      this.preencherQuantidade(item, form, produto);
    this.configurarEdicaoQuantidade(form, this.itemEstaEmEdicao(item));
  }
  private configurarEdicaoQuantidade(form: FormGroup, editando: boolean): void {
    for (const nome of ['quantidade_confirmada', 'tipo_quantidade', 'unidades_por_pacote', 'valor_total', 'tipo_valor']) {
      const controle = form.get(nome);
      if (editando && (!['valor_total', 'tipo_valor'].includes(nome) || this.nota()?.origem === 'manual')) controle?.enable({ emitEvent: false });
      else controle?.disable({ emitEvent: false });
    }
  }
  private atualizarEstabelecimentoNaNota(estabelecimento: Estabelecimento): void {
    this.nota.update((nota) => (nota ? { ...nota, estabelecimento } : nota));
  }
  private preencherQuantidade(item: ItemNota, form: FormGroup, produto: Produto): void {
    form.patchValue({
      quantidade_confirmada: sugerirQuantidade(item.quantidade, item.unidade_original, produto),
    });
  }
  private configurarCamposProduto(
    form: FormGroup,
    produto: Produto | null,
    marcaId: string | null,
  ): void {
    const marca = form.get('marca_id');
    if (produto?.nao_solicitar_marca) {
      marca?.clearValidators();
      marca?.setValue(null);
    } else {
      marca?.setValidators(Validators.required);
      marca?.setValue(marcaId);
    }
    marca?.updateValueAndValidity({ emitEvent: false });
    const variacao = form.get('variacao_id');
    if (produto?.contem_variacoes) variacao?.setValidators(Validators.required);
    else {
      variacao?.clearValidators();
      variacao?.setValue(null);
    }
    variacao?.updateValueAndValidity({ emitEvent: false });
    const quantidade = form.get('quantidade_confirmada');
    const validadores = [Validators.required, Validators.min(0.001), validarDecimal];
    if (produto?.tratar_apenas_como_unidades || produto?.contem_variacoes)
      validadores.push(Validators.pattern(/^\d+$/));
    quantidade?.setValidators(validadores);
    quantidade?.updateValueAndValidity({ emitEvent: false });
    this.configurarPacotes(form, produto);
  }
  private numero(valor: string | null | undefined): number | null {
    const n = valor == null ? NaN : Number(valor);
    return Number.isFinite(n) ? n : null;
  }
  private adicionarOrdenado<T extends { id: string }>(
    destino: { update: (atualizador: (valor: T[]) => T[]) => void },
    registro: T,
    nome: (valor: T) => string,
  ): void {
    destino.update((atuais) =>
      [...atuais.filter((atual) => atual.id !== registro.id), registro].sort((a, b) =>
        nome(a).localeCompare(nome(b)),
      ),
    );
  }
}
