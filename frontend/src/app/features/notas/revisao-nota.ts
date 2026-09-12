import { CurrencyPipe, DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
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

  readonly categoriaForm = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.maxLength(100)]],
  });
  readonly marcaForm = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.maxLength(100)]],
  });
  readonly produtoForm = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.maxLength(150)]],
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

  criarCategoria(): void {
    if (this.categoriaForm.invalid || this.cadastroSalvando()) return;
    this.cadastroSalvando.set(true);
    this.api.criarCategoria(this.categoriaForm.getRawValue().nome.trim()).subscribe({
      next: (categoria) => {
        this.categorias.update((atuais) =>
          [...atuais, categoria].sort((a, b) => a.nome.localeCompare(b.nome)),
        );
        this.categoriaForm.reset();
        this.produtoForm.patchValue({ categoria_id: categoria.id });
        this.cadastroSalvando.set(false);
      },
      error: (erro) => this.tratarErroCadastro(erro),
    });
  }

  criarMarca(): void {
    if (this.marcaForm.invalid || this.cadastroSalvando()) return;
    this.cadastroSalvando.set(true);
    this.api.criarMarca(this.marcaForm.getRawValue().nome.trim()).subscribe({
      next: (marca) => {
        this.marcas.update((atuais) =>
          [...atuais, marca].sort((a, b) => a.nome.localeCompare(b.nome)),
        );
        this.marcaForm.reset();
        this.cadastroSalvando.set(false);
      },
      error: (erro) => this.tratarErroCadastro(erro),
    });
  }

  criarProduto(): void {
    this.produtoForm.markAllAsTouched();
    if (this.produtoForm.invalid || this.cadastroSalvando()) return;
    this.cadastroSalvando.set(true);
    const valor = this.produtoForm.getRawValue();
    this.api.criarProduto({ ...valor, nome: valor.nome.trim() }).subscribe({
      next: (produto) => {
        this.produtos.update((atuais) =>
          [...atuais, produto].sort((a, b) => a.nome.localeCompare(b.nome)),
        );
        this.produtoForm.reset({ nome: '', categoria_id: '', unidade_base: 'UN' });
        this.cadastroSalvando.set(false);
      },
      error: (erro) => this.tratarErroCadastro(erro),
    });
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
