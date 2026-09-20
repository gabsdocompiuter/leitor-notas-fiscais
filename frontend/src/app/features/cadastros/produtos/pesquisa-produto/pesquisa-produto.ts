import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../../../core/api/api.service';
import {
  Categoria,
  Produto,
  UnidadeMedida,
  UnidadeMedidaInfo,
} from '../../../../core/models/api.models';
import { PesquisaCadastroBase } from '../../pesquisa-cadastro-base';
import { PesquisaCategoria } from '../../categorias/pesquisa-categoria/pesquisa-categoria';

@Component({
  selector: 'lnf-pesquisa-produto',
  imports: [ReactiveFormsModule, PesquisaCategoria],
  templateUrl: './pesquisa-produto.html',
})
export class PesquisaProduto extends PesquisaCadastroBase<Produto> implements OnInit {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);

  readonly categorias = input.required<readonly Categoria[]>();
  readonly unidades = input.required<readonly UnidadeMedidaInfo[]>();
  readonly categoriaCriada = output<Categoria>();

  readonly tituloPesquisa = 'Selecionar produto';
  readonly tituloCadastro = 'Novo produto';
  readonly placeholderPesquisa = 'Pesquisar produto';
  readonly mensagemSemResultados = 'Nenhum produto encontrado.';
  readonly seletorCategoriaAberto = signal(false);
  readonly categoriaSelecionada = signal<Categoria | null>(null);
  readonly formulario = this.fb.group({
    nome: ['', [Validators.required, Validators.maxLength(150), Validators.pattern(/\S/)]],
    categoria_id: ['', Validators.required],
    nao_solicitar_marca: [false],
    tratar_apenas_como_unidades: [false],
    contem_variacoes: [false],
    unidade_medida: ['KG' as UnidadeMedida | null, Validators.required],
  });

  override ngOnInit(): void {
    super.ngOnInit();
    this.formulario.controls.tratar_apenas_como_unidades.valueChanges.subscribe((somenteUnidades) =>
      this.configurarUnidadeMedida(!!somenteUnidades),
    );
  }

  abrirPesquisaCategoria(): void {
    this.seletorCategoriaAberto.set(true);
  }

  fecharPesquisaCategoria(): void {
    this.seletorCategoriaAberto.set(false);
  }

  selecionarCategoria(categoria: Categoria): void {
    this.categoriaSelecionada.set(categoria);
    this.formulario.controls.categoria_id.setValue(categoria.id);
    this.fecharPesquisaCategoria();
  }

  registrarCategoriaCriada(categoria: Categoria): void {
    this.categoriaCriada.emit(categoria);
  }

  criar(): void {
    this.formulario.markAllAsTouched();
    if (this.formulario.invalid || this.salvando()) return;

    const valor = this.formulario.getRawValue();
    this.salvando.set(true);
    this.erro.set(null);
    this.api
      .criarProduto({
        nome: valor.nome!.trim(),
        categoria_id: valor.categoria_id!,
        nao_solicitar_marca: !!valor.nao_solicitar_marca,
        tratar_apenas_como_unidades: !!valor.tratar_apenas_como_unidades,
        contem_variacoes: !valor.tratar_apenas_como_unidades && !!valor.contem_variacoes,
        unidade_medida: valor.tratar_apenas_como_unidades ? null : valor.unidade_medida,
      })
      .subscribe({
        next: (produto) => this.concluirCadastro(produto),
        error: (erro) => this.tratarErro(erro),
      });
  }

  protected override textoPesquisa(produto: Produto): string {
    return `${produto.nome} ${produto.categoria.nome}`;
  }

  protected override prepararCadastro(nomeInicial: string): void {
    this.categoriaSelecionada.set(null);
    this.formulario.reset({
      nome: nomeInicial,
      categoria_id: '',
      nao_solicitar_marca: false,
      tratar_apenas_como_unidades: false,
      contem_variacoes: false,
      unidade_medida: 'KG',
    });
  }

  private configurarUnidadeMedida(somenteUnidades: boolean): void {
    const unidade = this.formulario.controls.unidade_medida;
    if (somenteUnidades) {
      this.formulario.patchValue({ contem_variacoes: false, unidade_medida: null });
      unidade.clearValidators();
    } else {
      unidade.setValidators(Validators.required);
      if (!unidade.value) unidade.setValue('KG');
    }
    unidade.updateValueAndValidity();
  }
}
