import { CurrencyPipe, DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { ApiService } from '../../../core/api/api.service';
import {
  Categoria,
  ItemNota,
  Marca,
  Nota,
  Produto,
  RevisaoItem,
  UnidadeMedidaInfo,
  VariacaoProduto,
} from '../../../core/models/api.models';
import { capitalizarIniciais } from '../../../core/utils/catalogo.utils';
import { mensagemErro } from '../../../core/utils/erro-api';
import { quantidadeItensPendentes, todosItensRevisados } from '../../../core/utils/nota.utils';
import { sugerirQuantidade } from '../../../core/utils/quantidade.utils';
import { EstadoVazio } from '../../../shared/components/estado-vazio/estado-vazio';
import { PesquisaMarca } from '../../cadastros/marcas/pesquisa-marca/pesquisa-marca';
import { PesquisaProduto } from '../../cadastros/produtos/pesquisa-produto/pesquisa-produto';
import { PesquisaVariacao } from '../../cadastros/produtos/pesquisa-variacao/pesquisa-variacao';

type TipoModal = 'produto' | 'marca' | 'variacao';

@Component({
  selector: 'lnf-revisao-notas',
  imports: [
    CurrencyPipe,
    DatePipe,
    ReactiveFormsModule,
    RouterLink,
    EstadoVazio,
    PesquisaMarca,
    PesquisaProduto,
    PesquisaVariacao,
  ],
  templateUrl: './revisao-notas.html',
})
export class RevisaoNotas implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly chave = this.route.snapshot.paramMap.get('chave') ?? '';
  private readonly formularios = new Map<string, FormGroup>();

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
  readonly modalAberto = signal(false);
  readonly tipoModal = signal<TipoModal>('produto');
  readonly itemModal = signal<ItemNota | null>(null);
  readonly buscaInicialModal = signal('');

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando.set(true);
    forkJoin({
      nota: this.api.obterNota(this.chave),
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
  nomeMarcaSelecionada(id: string): string {
    const marcaId = this.formularios.get(id)?.get('marca_id')?.value;
    return this.marcas().find((m) => m.id === marcaId)?.nome ?? 'Selecionar marca';
  }
  nomeVariacaoSelecionada(id: string): string {
    const variacaoId = this.formularios.get(id)?.get('variacao_id')?.value;
    const item = this.nota()?.itens.find((i) => i.id === id);
    const variacaoSalva = item?.variacao;
    const nomeSalvo =
      variacaoSalva && variacaoSalva.id === variacaoId ? variacaoSalva.nome_exibicao : undefined;
    return (
      this.variacoes().find((v) => v.id === variacaoId)?.nome_exibicao ??
      nomeSalvo ??
      'Selecionar variação'
    );
  }
  salvarItem(item: ItemNota): void {
    const form = this.formularios.get(item.id);
    if (!form || this.nota()?.situacao === 'importada') return;
    form.markAllAsTouched();
    if (form.invalid) {
      this.erro.set('Revise os campos destacados antes de salvar o item.');
      return;
    }
    const valor = form.getRawValue();
    const revisao: RevisaoItem = {
      produto_id: valor.produto_id,
      quantidade_confirmada: Number(valor.quantidade_confirmada),
      variacao_id: valor.variacao_id || null,
    };
    if (this.deveSolicitarMarca(item.id)) revisao.marca_id = valor.marca_id;
    this.itemSalvando.set(item.id);
    this.erro.set(null);
    this.sucesso.set(null);
    this.api.revisarItem(this.chave, item.id, revisao).subscribe({
      next: (nota) => {
        this.definirNota(nota);
        this.itemSalvando.set(null);
        this.sucesso.set(`Item ${item.numero} revisado.`);
      },
      error: (e) => {
        this.erro.set(mensagemErro(e));
        this.itemSalvando.set(null);
      },
    });
  }

  concluirImportacao(): void {
    const nota = this.nota();
    if (!nota || !todosItensRevisados(nota) || this.importando()) return;
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
    if (!form || this.nota()?.situacao === 'importada') return;
    this.tipoModal.set(tipo);
    this.itemModal.set(item);
    this.buscaInicialModal.set(
      tipo === 'produto' ? capitalizarIniciais(item.descricao_original) : '',
    );
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
  selecionarProduto(produto: Produto): void {
    const item = this.itemModal();
    if (!item) return;
    const form = this.formularios.get(item.id);
    if (!form) return;
    const mudou = form.get('produto_id')?.value !== produto.id;
    form.patchValue({
      produto_id: produto.id,
      variacao_id: mudou ? null : form.get('variacao_id')?.value,
    });
    this.configurarCamposProduto(form, produto, mudou ? null : form.get('marca_id')?.value);
    this.preencherQuantidade(item, form, produto);
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
  podeImportar(n: Nota): boolean {
    return todosItensRevisados(n);
  }

  private definirNota(nota: Nota): void {
    this.nota.set(nota);
    this.formularios.clear();
    nota.itens.forEach((item) => {
      const produto = item.apresentacao?.produto ?? null;
      const form = this.fb.group({
        produto_id: [produto?.id ?? '', Validators.required],
        marca_id: [item.apresentacao?.marca?.id ?? (null as string | null)],
        variacao_id: [item.variacao?.id ?? (null as string | null)],
        quantidade_confirmada: [
          this.numero(item.quantidade_confirmada),
          [Validators.required, Validators.min(0.000001)],
        ],
      });
      this.configurarCamposProduto(form, produto, item.apresentacao?.marca?.id ?? null);
      if (item.quantidade_confirmada === null && produto)
        this.preencherQuantidade(item, form, produto);
      this.formularios.set(item.id, form);
    });
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
    const validadores = [Validators.required, Validators.min(0.000001)];
    if (produto?.tratar_apenas_como_unidades || produto?.contem_variacoes)
      validadores.push(Validators.pattern(/^\d+$/));
    quantidade?.setValidators(validadores);
    quantidade?.updateValueAndValidity({ emitEvent: false });
  }
  private numero(valor: string | null): number | null {
    const n = valor === null ? NaN : Number(valor);
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
