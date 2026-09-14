import { CurrencyPipe, DatePipe } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { ApiService } from '../../core/api/api.service';
import {
  Categoria, ItemNota, Marca, Nota, Produto, RevisaoItem, UnidadeMedida,
  UnidadeMedidaInfo, VariacaoProduto,
} from '../../core/models/api.models';
import { capitalizarIniciais, filtrarCatalogo } from '../../core/utils/catalogo.utils';
import { mensagemErro } from '../../core/utils/erro-api';
import { quantidadeItensPendentes, todosItensRevisados } from '../../core/utils/nota.utils';
import { sugerirQuantidade } from '../../core/utils/quantidade.utils';
import { EstadoVazio } from '../../shared/components/estado-vazio/estado-vazio';

type TipoModal = 'produto' | 'marca' | 'variacao';

@Component({
  selector: 'lnf-revisao-nota',
  imports: [CurrencyPipe, DatePipe, ReactiveFormsModule, RouterLink, EstadoVazio],
  templateUrl: './revisao-nota.html',
  styleUrl: './revisao-nota.scss',
})
export class RevisaoNota implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly chave = this.route.snapshot.paramMap.get('chave') ?? '';
  private readonly formularios = new Map<string, FormGroup>();

  @ViewChild('buscaModal') private buscaModal?: ElementRef<HTMLInputElement>;
  @ViewChild('buscaCategoriaModal') private buscaCategoriaModal?: ElementRef<HTMLInputElement>;

  readonly nota = signal<Nota | null>(null);
  readonly produtos = signal<Produto[]>([]);
  readonly categorias = signal<Categoria[]>([]);
  readonly marcas = signal<Marca[]>([]);
  readonly unidades = signal<UnidadeMedidaInfo[]>([]);
  readonly variacoes = signal<VariacaoProduto[]>([]);
  readonly carregando = signal(true);
  readonly erro = signal<string | null>(null);
  readonly sucesso = signal<string | null>(null);
  readonly itemSalvando = signal<string | null>(null);
  readonly importando = signal(false);
  readonly cadastroSalvando = signal(false);
  readonly modalAberto = signal(false);
  readonly tipoModal = signal<TipoModal>('produto');
  readonly itemModal = signal<ItemNota | null>(null);
  readonly buscaCatalogo = signal('');
  readonly modalCategoriaAberto = signal(false);
  readonly buscaCategoria = signal('');

  readonly produtosFiltrados = computed(() => filtrarCatalogo(
    this.produtos(), this.buscaCatalogo(), (p) => `${p.nome} ${p.categoria.nome}`,
  ));
  readonly marcasFiltradas = computed(() => filtrarCatalogo(
    this.marcas(), this.buscaCatalogo(), (m) => m.nome,
  ));
  readonly variacoesFiltradas = computed(() => filtrarCatalogo(
    this.variacoes(), this.buscaCatalogo(), (v) => v.nome_exibicao,
  ));
  readonly categoriasFiltradas = computed(() => filtrarCatalogo(
    this.categorias(), this.buscaCategoria(), (c) => c.nome,
  ));

  readonly novoProdutoForm = this.fb.group({
    categoria_id: ['', Validators.required],
    nao_solicitar_marca: [false],
    tratar_apenas_como_unidades: [false],
    contem_variacoes: [false],
    unidade_medida: ['KG' as UnidadeMedida | null, Validators.required],
  });
  readonly novaVariacaoForm = this.fb.group({
    quantidade: [null as number | null, [Validators.required, Validators.min(0.000001)]],
    unidade_medida: ['G' as UnidadeMedida, Validators.required],
  });

  ngOnInit(): void {
    this.novoProdutoForm.controls.tratar_apenas_como_unidades.valueChanges.subscribe(
      (somenteUnidades) => {
        if (somenteUnidades) {
          this.novoProdutoForm.patchValue({ contem_variacoes: false, unidade_medida: null });
          this.novoProdutoForm.controls.unidade_medida.clearValidators();
        } else {
          this.novoProdutoForm.controls.unidade_medida.setValidators(Validators.required);
          if (!this.novoProdutoForm.controls.unidade_medida.value) {
            this.novoProdutoForm.controls.unidade_medida.setValue('KG');
          }
        }
        this.novoProdutoForm.controls.unidade_medida.updateValueAndValidity();
      },
    );
    this.carregar();
  }

  carregar(): void {
    this.carregando.set(true);
    forkJoin({
      nota: this.api.obterNota(this.chave), produtos: this.api.listarProdutos(),
      categorias: this.api.listarCategorias(), marcas: this.api.listarMarcas(),
      unidades: this.api.listarUnidadesMedida(),
    }).subscribe({
      next: (dados) => {
        this.produtos.set(dados.produtos); this.categorias.set(dados.categorias);
        this.marcas.set(dados.marcas); this.unidades.set(dados.unidades);
        this.definirNota(dados.nota); this.carregando.set(false);
      },
      error: (e) => { this.erro.set(mensagemErro(e)); this.carregando.set(false); },
    });
  }

  formularioItem(id: string): FormGroup | undefined { return this.formularios.get(id); }
  produtoSelecionado(id: string): Produto | null {
    const produtoId = this.formularios.get(id)?.get('produto_id')?.value;
    return this.produtos().find((p) => p.id === produtoId) ?? null;
  }
  nomeProdutoSelecionado(id: string): string | null { return this.produtoSelecionado(id)?.nome ?? null; }
  deveSolicitarMarca(id: string): boolean {
    const produto = this.produtoSelecionado(id);
    return !!produto && !produto.nao_solicitar_marca;
  }
  deveSelecionarVariacao(id: string): boolean { return !!this.produtoSelecionado(id)?.contem_variacoes; }
  unidadeQuantidade(id: string): string {
    const produto = this.produtoSelecionado(id);
    return produto?.tratar_apenas_como_unidades || produto?.contem_variacoes
      ? 'unidades' : (produto?.unidade_medida ?? '');
  }
  passoQuantidade(id: string): string {
    const produto = this.produtoSelecionado(id);
    return produto?.tratar_apenas_como_unidades || produto?.contem_variacoes ? '1' : 'any';
  }
  nomeMarcaSelecionada(id: string): string {
    const marcaId = this.formularios.get(id)?.get('marca_id')?.value;
    return this.marcas().find((m) => m.id === marcaId)?.nome ?? 'Selecionar marca';
  }
  nomeVariacaoSelecionada(id: string): string {
    const variacaoId = this.formularios.get(id)?.get('variacao_id')?.value;
    const item = this.nota()?.itens.find((i) => i.id === id);
    const variacaoSalva = item?.variacao;
    const nomeSalvo = variacaoSalva && variacaoSalva.id === variacaoId
      ? variacaoSalva.nome_exibicao : undefined;
    return this.variacoes().find((v) => v.id === variacaoId)?.nome_exibicao
      ?? nomeSalvo ?? 'Selecionar variação';
  }
  nomeCategoriaSelecionada(): string | null {
    const id = this.novoProdutoForm.controls.categoria_id.value;
    return this.categorias().find((c) => c.id === id)?.nome ?? null;
  }

  salvarItem(item: ItemNota): void {
    const form = this.formularios.get(item.id);
    if (!form || this.nota()?.situacao === 'importada') return;
    form.markAllAsTouched();
    if (form.invalid) { this.erro.set('Revise os campos destacados antes de salvar o item.'); return; }
    const valor = form.getRawValue();
    const revisao: RevisaoItem = {
      produto_id: valor.produto_id,
      quantidade_confirmada: Number(valor.quantidade_confirmada),
      variacao_id: valor.variacao_id || null,
    };
    if (this.deveSolicitarMarca(item.id)) revisao.marca_id = valor.marca_id;
    this.itemSalvando.set(item.id); this.erro.set(null); this.sucesso.set(null);
    this.api.revisarItem(this.chave, item.id, revisao).subscribe({
      next: (nota) => { this.definirNota(nota); this.itemSalvando.set(null); this.sucesso.set(`Item ${item.numero} revisado.`); },
      error: (e) => { this.erro.set(mensagemErro(e)); this.itemSalvando.set(null); },
    });
  }

  concluirImportacao(): void {
    const nota = this.nota();
    if (!nota || !todosItensRevisados(nota) || this.importando()) return;
    this.importando.set(true); this.erro.set(null);
    this.api.concluirImportacao(this.chave).subscribe({
      next: (n) => { this.definirNota(n); this.importando.set(false); this.sucesso.set('Nota importada com sucesso.'); window.scrollTo({ top: 0, behavior: 'smooth' }); },
      error: (e) => { this.erro.set(mensagemErro(e)); this.importando.set(false); },
    });
  }

  abrirSeletor(tipo: TipoModal, item: ItemNota): void {
    const form = this.formularios.get(item.id);
    if (!form || this.nota()?.situacao === 'importada') return;
    this.tipoModal.set(tipo); this.itemModal.set(item);
    this.buscaCatalogo.set(tipo === 'produto' ? capitalizarIniciais(item.descricao_original) : '');
    if (tipo === 'produto') {
      const atual = this.produtoSelecionado(item.id);
      this.novoProdutoForm.reset({
        categoria_id: atual?.categoria.id ?? '', nao_solicitar_marca: atual?.nao_solicitar_marca ?? false,
        tratar_apenas_como_unidades: atual?.tratar_apenas_como_unidades ?? false,
        contem_variacoes: atual?.contem_variacoes ?? false, unidade_medida: atual?.unidade_medida ?? 'KG',
      });
    } else if (tipo === 'variacao') {
      const produto = this.produtoSelecionado(item.id);
      if (!produto) return;
      this.variacoes.set([]);
      this.novaVariacaoForm.reset({ quantidade: null, unidade_medida: 'G' });
      this.api.listarVariacoes(produto.id).subscribe({
        next: (v) => this.variacoes.set(v), error: (e) => this.erro.set(mensagemErro(e)),
      });
    }
    this.modalAberto.set(true); document.body.classList.add('modal-open');
    setTimeout(() => { this.buscaModal?.nativeElement.focus(); this.buscaModal?.nativeElement.select(); });
  }
  fecharSeletor(): void {
    if (this.cadastroSalvando()) return;
    this.modalCategoriaAberto.set(false); this.modalAberto.set(false); this.itemModal.set(null);
    document.body.classList.remove('modal-open');
  }
  atualizarBusca(e: Event): void { this.buscaCatalogo.set((e.target as HTMLInputElement).value); }
  selecionarProduto(produto: Produto): void {
    const item = this.itemModal(); if (!item) return;
    const form = this.formularios.get(item.id); if (!form) return;
    const mudou = form.get('produto_id')?.value !== produto.id;
    form.patchValue({ produto_id: produto.id, variacao_id: mudou ? null : form.get('variacao_id')?.value });
    this.configurarCamposProduto(form, produto, mudou ? null : form.get('marca_id')?.value);
    this.preencherQuantidade(item, form, produto);
    this.fecharSeletor();
  }
  selecionarMarca(marca: Marca): void { const item = this.itemModal(); if (item) this.formularios.get(item.id)?.patchValue({ marca_id: marca.id }); this.fecharSeletor(); }
  selecionarVariacao(v: VariacaoProduto): void { const item = this.itemModal(); if (item) this.formularios.get(item.id)?.patchValue({ variacao_id: v.id }); this.fecharSeletor(); }

  criarVariacaoNoModal(): void {
    const item = this.itemModal();
    if (!item || this.cadastroSalvando()) return;
    const produto = this.produtoSelecionado(item.id);
    this.novaVariacaoForm.markAllAsTouched();
    if (!produto || this.novaVariacaoForm.invalid) return;
    const valor = this.novaVariacaoForm.getRawValue();
    this.cadastroSalvando.set(true);
    this.api.criarVariacao(produto.id, {
      quantidade: Number(valor.quantidade),
      unidade_medida: valor.unidade_medida!,
      descricao: this.buscaCatalogo().trim() || null,
    }).subscribe({
      next: (variacao) => {
        this.variacoes.update((atuais) => {
          const semDuplicada = atuais.filter((itemAtual) => itemAtual.id !== variacao.id);
          return [...semDuplicada, variacao].sort((a, b) =>
            a.nome_exibicao.localeCompare(b.nome_exibicao),
          );
        });
        this.cadastroSalvando.set(false);
        this.selecionarVariacao(variacao);
      },
      error: (e) => this.tratarErroCadastro(e),
    });
  }

  abrirSeletorCategoria(): void {
    this.buscaCategoria.set(this.nomeCategoriaSelecionada() ?? ''); this.modalCategoriaAberto.set(true);
    setTimeout(() => { this.buscaCategoriaModal?.nativeElement.focus(); this.buscaCategoriaModal?.nativeElement.select(); });
  }
  fecharSeletorCategoria(): void { if (!this.cadastroSalvando()) this.modalCategoriaAberto.set(false); }
  atualizarBuscaCategoria(e: Event): void { this.buscaCategoria.set((e.target as HTMLInputElement).value); }
  selecionarCategoria(c: Categoria): void { this.novoProdutoForm.patchValue({ categoria_id: c.id }); this.modalCategoriaAberto.set(false); }
  criarCategoriaNoModal(): void {
    const nome = this.buscaCategoria().trim(); if (!nome || nome.length > 100 || this.cadastroSalvando()) return;
    this.cadastroSalvando.set(true); this.api.criarCategoria(nome).subscribe({
      next: (c) => { this.categorias.update((x) => [...x, c].sort((a, b) => a.nome.localeCompare(b.nome))); this.cadastroSalvando.set(false); this.selecionarCategoria(c); },
      error: (e) => this.tratarErroCadastro(e),
    });
  }
  criarMarcaNoModal(): void {
    const nome = this.buscaCatalogo().trim(); if (!nome || nome.length > 100 || this.cadastroSalvando()) return;
    this.cadastroSalvando.set(true); this.api.criarMarca(nome).subscribe({
      next: (m) => { this.marcas.update((x) => [...x, m].sort((a, b) => a.nome.localeCompare(b.nome))); this.cadastroSalvando.set(false); this.selecionarMarca(m); },
      error: (e) => this.tratarErroCadastro(e),
    });
  }
  criarProdutoNoModal(): void {
    const nome = this.buscaCatalogo().trim(); this.novoProdutoForm.markAllAsTouched();
    if (!nome || nome.length > 150 || this.novoProdutoForm.invalid || this.cadastroSalvando()) return;
    const valor = this.novoProdutoForm.getRawValue();
    this.cadastroSalvando.set(true); this.api.criarProduto({
      nome, categoria_id: valor.categoria_id!, nao_solicitar_marca: !!valor.nao_solicitar_marca,
      tratar_apenas_como_unidades: !!valor.tratar_apenas_como_unidades,
      contem_variacoes: !valor.tratar_apenas_como_unidades && !!valor.contem_variacoes,
      unidade_medida: valor.tratar_apenas_como_unidades ? null : valor.unidade_medida,
    }).subscribe({
      next: (p) => { this.produtos.update((x) => [...x, p].sort((a, b) => a.nome.localeCompare(b.nome))); this.cadastroSalvando.set(false); this.selecionarProduto(p); },
      error: (e) => this.tratarErroCadastro(e),
    });
  }

  itensPendentes(n: Nota): number { return quantidadeItensPendentes(n); }
  podeImportar(n: Nota): boolean { return todosItensRevisados(n); }

  private definirNota(nota: Nota): void {
    this.nota.set(nota); this.formularios.clear();
    nota.itens.forEach((item) => {
      const produto = item.apresentacao?.produto ?? null;
      const form = this.fb.group({
        produto_id: [produto?.id ?? '', Validators.required],
        marca_id: [item.apresentacao?.marca?.id ?? null as string | null],
        variacao_id: [item.variacao?.id ?? null as string | null],
        quantidade_confirmada: [this.numero(item.quantidade_confirmada), [Validators.required, Validators.min(0.000001)]],
      });
      this.configurarCamposProduto(form, produto, item.apresentacao?.marca?.id ?? null);
      if (item.quantidade_confirmada === null && produto) this.preencherQuantidade(item, form, produto);
      this.formularios.set(item.id, form);
    });
  }
  private preencherQuantidade(item: ItemNota, form: FormGroup, produto: Produto): void {
    form.patchValue({
      quantidade_confirmada: sugerirQuantidade(
        item.quantidade, item.unidade_original, produto,
      ),
    });
  }
  private configurarCamposProduto(form: FormGroup, produto: Produto | null, marcaId: string | null): void {
    const marca = form.get('marca_id');
    if (produto?.nao_solicitar_marca) { marca?.clearValidators(); marca?.setValue(null); }
    else { marca?.setValidators(Validators.required); marca?.setValue(marcaId); }
    marca?.updateValueAndValidity({ emitEvent: false });
    const variacao = form.get('variacao_id');
    if (produto?.contem_variacoes) variacao?.setValidators(Validators.required);
    else { variacao?.clearValidators(); variacao?.setValue(null); }
    variacao?.updateValueAndValidity({ emitEvent: false });
    const quantidade = form.get('quantidade_confirmada');
    const validadores = [Validators.required, Validators.min(0.000001)];
    if (produto?.tratar_apenas_como_unidades || produto?.contem_variacoes) validadores.push(Validators.pattern(/^\d+$/));
    quantidade?.setValidators(validadores); quantidade?.updateValueAndValidity({ emitEvent: false });
  }
  private numero(valor: string | null): number | null { const n = valor === null ? NaN : Number(valor); return Number.isFinite(n) ? n : null; }
  private tratarErroCadastro(e: unknown): void { this.erro.set(mensagemErro(e)); this.cadastroSalvando.set(false); }
}
