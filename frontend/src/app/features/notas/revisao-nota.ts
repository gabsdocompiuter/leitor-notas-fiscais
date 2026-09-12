import { CurrencyPipe, DatePipe } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { ApiService } from '../../core/api/api.service';
import {
  Categoria,
  ItemNota,
  Marca,
  Nota,
  Produto,
  RevisaoItem,
  UnidadeMedida,
} from '../../core/models/api.models';
import { mensagemErro } from '../../core/utils/erro-api';
import { capitalizarIniciais, filtrarCatalogo } from '../../core/utils/catalogo.utils';
import { quantidadeItensPendentes, todosItensRevisados } from '../../core/utils/nota.utils';
import { EstadoVazio } from '../../shared/components/estado-vazio/estado-vazio';

const UNIDADES: { valor: UnidadeMedida; rotulo: string }[] = [
  { valor: 'UN', rotulo: 'Unidade (UN)' },
  { valor: 'KG', rotulo: 'Quilograma (KG)' },
  { valor: 'G', rotulo: 'Grama (G)' },
  { valor: 'L', rotulo: 'Litro (L)' },
  { valor: 'ML', rotulo: 'Mililitro (ML)' },
];

const embalagemCompleta: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const conteudo = control.get('conteudo_embalagem')?.value;
  const unidade = control.get('unidade_embalagem')?.value;
  return Boolean(conteudo) === Boolean(unidade) ? null : { embalagemIncompleta: true };
};

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
  @ViewChild('buscaCategoriaModal')
  private buscaCategoriaModal?: ElementRef<HTMLInputElement>;

  readonly unidades = UNIDADES;
  readonly nota = signal<Nota | null>(null);
  readonly produtos = signal<Produto[]>([]);
  readonly categorias = signal<Categoria[]>([]);
  readonly marcas = signal<Marca[]>([]);
  readonly carregando = signal(true);
  readonly erro = signal<string | null>(null);
  readonly sucesso = signal<string | null>(null);
  readonly itemSalvando = signal<string | null>(null);
  readonly importando = signal(false);
  readonly cadastroSalvando = signal(false);
  readonly modalAberto = signal(false);
  readonly tipoModal = signal<'produto' | 'marca'>('produto');
  readonly itemModal = signal<ItemNota | null>(null);
  readonly buscaCatalogo = signal('');
  readonly modalCategoriaAberto = signal(false);
  readonly buscaCategoria = signal('');
  readonly produtosFiltrados = computed(() =>
    filtrarCatalogo(
      this.produtos(),
      this.buscaCatalogo(),
      (produto) => `${produto.nome} ${produto.categoria.nome}`,
    ),
  );
  readonly marcasFiltradas = computed(() =>
    filtrarCatalogo(this.marcas(), this.buscaCatalogo(), (marca) => marca.nome),
  );
  readonly categoriasFiltradas = computed(() =>
    filtrarCatalogo(this.categorias(), this.buscaCategoria(), (categoria) => categoria.nome),
  );
  readonly novoProdutoForm = this.fb.nonNullable.group({
    categoria_id: ['', Validators.required],
    unidade_base: ['UN' as UnidadeMedida, Validators.required],
  });

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando.set(true);
    this.erro.set(null);
    forkJoin({
      nota: this.api.obterNota(this.chave),
      produtos: this.api.listarProdutos(),
      categorias: this.api.listarCategorias(),
      marcas: this.api.listarMarcas(),
    }).subscribe({
      next: ({ nota, produtos, categorias, marcas }) => {
        this.produtos.set(produtos);
        this.categorias.set(categorias);
        this.marcas.set(marcas);
        this.definirNota(nota);
        this.carregando.set(false);
      },
      error: (erro) => {
        this.erro.set(mensagemErro(erro));
        this.carregando.set(false);
      },
    });
  }

  formularioItem(itemId: string): FormGroup | undefined {
    return this.formularios.get(itemId);
  }

  salvarItem(item: ItemNota): void {
    const formulario = this.formularios.get(item.id);
    if (!formulario || this.nota()?.situacao === 'importada') return;
    formulario.markAllAsTouched();
    if (formulario.invalid) {
      this.erro.set('Revise os campos destacados antes de salvar o item.');
      return;
    }

    const valor = formulario.getRawValue();
    const revisao: RevisaoItem = {
      produto_id: valor.produto_id,
      marca_id: valor.marca_id || null,
      marca_confirmada: valor.marca_confirmada,
      conteudo_embalagem: valor.conteudo_embalagem || null,
      unidade_embalagem: valor.unidade_embalagem || null,
      unidade_corrigida: valor.unidade_corrigida,
      quantidade_normalizada: valor.quantidade_normalizada,
    };

    this.itemSalvando.set(item.id);
    this.erro.set(null);
    this.sucesso.set(null);
    this.api.revisarItem(this.chave, item.id, revisao).subscribe({
      next: (nota) => {
        this.definirNota(nota);
        this.itemSalvando.set(null);
        this.sucesso.set(`Item ${item.numero} revisado.`);
      },
      error: (erro) => {
        this.erro.set(mensagemErro(erro));
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
      next: (notaImportada) => {
        this.definirNota(notaImportada);
        this.importando.set(false);
        this.sucesso.set('Nota importada com sucesso.');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      },
      error: (erro) => {
        this.erro.set(mensagemErro(erro));
        this.importando.set(false);
      },
    });
  }

  abrirSeletor(tipo: 'produto' | 'marca', item: ItemNota): void {
    const formulario = this.formularios.get(item.id);
    if (!formulario || this.nota()?.situacao === 'importada') return;

    this.tipoModal.set(tipo);
    this.itemModal.set(item);
    this.buscaCatalogo.set(tipo === 'produto' ? capitalizarIniciais(item.descricao_original) : '');

    if (tipo === 'produto') {
      const produtoAtual = this.produtos().find(
        (produto) => produto.id === formulario.get('produto_id')?.value,
      );
      this.novoProdutoForm.reset({
        categoria_id: produtoAtual?.categoria.id ?? '',
        unidade_base: produtoAtual?.unidade_base ?? 'UN',
      });
    }

    this.modalAberto.set(true);
    document.body.classList.add('modal-open');
    setTimeout(() => {
      this.buscaModal?.nativeElement.focus();
      this.buscaModal?.nativeElement.select();
    });
  }

  fecharSeletor(): void {
    if (this.cadastroSalvando()) return;
    this.modalCategoriaAberto.set(false);
    this.modalAberto.set(false);
    this.itemModal.set(null);
    document.body.classList.remove('modal-open');
  }

  atualizarBusca(evento: Event): void {
    this.buscaCatalogo.set((evento.target as HTMLInputElement).value);
  }

  abrirSeletorCategoria(): void {
    const categoriaAtual = this.categorias().find(
      (categoria) => categoria.id === this.novoProdutoForm.controls.categoria_id.value,
    );
    this.buscaCategoria.set(categoriaAtual?.nome ?? '');
    this.modalCategoriaAberto.set(true);
    setTimeout(() => {
      this.buscaCategoriaModal?.nativeElement.focus();
      this.buscaCategoriaModal?.nativeElement.select();
    });
  }

  fecharSeletorCategoria(): void {
    if (this.cadastroSalvando()) return;
    this.modalCategoriaAberto.set(false);
  }

  atualizarBuscaCategoria(evento: Event): void {
    this.buscaCategoria.set((evento.target as HTMLInputElement).value);
  }

  selecionarCategoria(categoria: Categoria): void {
    this.novoProdutoForm.patchValue({ categoria_id: categoria.id });
    this.modalCategoriaAberto.set(false);
  }

  criarCategoriaNoModal(): void {
    const nome = this.buscaCategoria().trim();
    if (!nome || nome.length > 100 || this.cadastroSalvando()) return;
    this.cadastroSalvando.set(true);
    this.api.criarCategoria(nome).subscribe({
      next: (categoria) => {
        this.categorias.update((atuais) =>
          [...atuais, categoria].sort((a, b) => a.nome.localeCompare(b.nome)),
        );
        this.cadastroSalvando.set(false);
        this.selecionarCategoria(categoria);
      },
      error: (erro) => this.tratarErroCadastro(erro),
    });
  }

  selecionarProduto(produto: Produto): void {
    const item = this.itemModal();
    if (!item) return;
    this.formularios.get(item.id)?.patchValue({ produto_id: produto.id });
    this.fecharSeletor();
  }

  selecionarMarca(marca: Marca | null): void {
    const item = this.itemModal();
    if (!item) return;
    this.formularios.get(item.id)?.patchValue({
      marca_id: marca?.id ?? null,
      marca_confirmada: true,
    });
    this.fecharSeletor();
  }

  criarMarcaNoModal(): void {
    const nome = this.buscaCatalogo().trim();
    if (!nome || nome.length > 100 || this.cadastroSalvando()) return;
    this.cadastroSalvando.set(true);
    this.api.criarMarca(nome).subscribe({
      next: (marca) => {
        this.marcas.update((atuais) =>
          [...atuais, marca].sort((a, b) => a.nome.localeCompare(b.nome)),
        );
        this.cadastroSalvando.set(false);
        this.selecionarMarca(marca);
      },
      error: (erro) => this.tratarErroCadastro(erro),
    });
  }

  criarProdutoNoModal(): void {
    const nome = this.buscaCatalogo().trim();
    this.novoProdutoForm.markAllAsTouched();
    if (!nome || nome.length > 150 || this.novoProdutoForm.invalid || this.cadastroSalvando()) {
      return;
    }

    this.cadastroSalvando.set(true);
    this.api.criarProduto({ nome, ...this.novoProdutoForm.getRawValue() }).subscribe({
      next: (produto) => {
        this.produtos.update((atuais) =>
          [...atuais, produto].sort((a, b) => a.nome.localeCompare(b.nome)),
        );
        this.cadastroSalvando.set(false);
        this.selecionarProduto(produto);
      },
      error: (erro) => this.tratarErroCadastro(erro),
    });
  }

  nomeProdutoSelecionado(itemId: string): string | null {
    const id = this.formularios.get(itemId)?.get('produto_id')?.value;
    return this.produtos().find((produto) => produto.id === id)?.nome ?? null;
  }

  nomeMarcaSelecionada(itemId: string): string {
    const formulario = this.formularios.get(itemId);
    const id = formulario?.get('marca_id')?.value;
    const marca = this.marcas().find((item) => item.id === id);
    if (marca) return marca.nome;
    return formulario?.get('marca_confirmada')?.value ? 'Sem marca' : 'Selecionar marca';
  }

  nomeCategoriaSelecionada(): string | null {
    const id = this.novoProdutoForm.controls.categoria_id.value;
    return this.categorias().find((categoria) => categoria.id === id)?.nome ?? null;
  }

  itensPendentes(nota: Nota): number {
    return quantidadeItensPendentes(nota);
  }
  podeImportar(nota: Nota): boolean {
    return todosItensRevisados(nota);
  }

  private definirNota(nota: Nota): void {
    this.nota.set(nota);
    this.formularios.clear();
    nota.itens.forEach((item) => {
      const unidadeOriginal = this.unidadeValida(item.unidade_original);
      this.formularios.set(
        item.id,
        this.fb.group(
          {
            produto_id: [item.apresentacao?.produto.id ?? '', Validators.required],
            marca_id: [item.apresentacao?.marca?.id ?? (null as string | null)],
            marca_confirmada: [
              item.apresentacao?.marca_confirmada ?? false,
              Validators.requiredTrue,
            ],
            conteudo_embalagem: [
              this.numeroOuNulo(item.apresentacao?.conteudo_embalagem),
              Validators.min(0.0001),
            ],
            unidade_embalagem: [
              item.apresentacao?.unidade_embalagem ?? (null as UnidadeMedida | null),
            ],
            unidade_corrigida: [
              item.unidade_corrigida ?? unidadeOriginal ?? ('UN' as UnidadeMedida),
              Validators.required,
            ],
            quantidade_normalizada: [
              this.numeroOuNulo(item.quantidade_normalizada) ?? Number(item.quantidade),
              [Validators.required, Validators.min(0.0001)],
            ],
          },
          { validators: embalagemCompleta },
        ),
      );
    });
  }

  private unidadeValida(unidade: string): UnidadeMedida | null {
    const valor = unidade.toUpperCase() as UnidadeMedida;
    return UNIDADES.some((item) => item.valor === valor) ? valor : null;
  }

  private numeroOuNulo(valor: string | null | undefined): number | null {
    if (valor === null || valor === undefined || valor === '') return null;
    const numero = Number(valor);
    return Number.isFinite(numero) ? numero : null;
  }

  private tratarErroCadastro(erro: unknown): void {
    this.erro.set(mensagemErro(erro));
    this.cadastroSalvando.set(false);
  }
}
