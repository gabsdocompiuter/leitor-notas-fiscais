import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { ApiService } from '../../../../core/api/api.service';
import {
  Categoria,
  Produto,
  ProdutoRequest,
  UnidadeMedida,
  UnidadeMedidaInfo,
  VariacaoProduto,
} from '../../../../core/models/api.models';
import { mensagemErro } from '../../../../core/utils/erro-api';

@Component({
  selector: 'lnf-cadastro-produto',
  imports: [FormsModule, RouterLink],
  templateUrl: './cadastro-produto.html',
})
export class CadastroProduto implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly produto = signal<Produto | null>(null);
  readonly categorias = signal<Categoria[]>([]);
  readonly unidades = signal<UnidadeMedidaInfo[]>([]);
  readonly variacoes = signal<VariacaoProduto[]>([]);
  readonly erro = signal<string | null>(null);
  readonly carregando = signal(true);
  readonly salvando = signal(false);
  readonly editandoVariacao = signal(false);
  readonly salvandoVariacao = signal(false);

  id: string | null = null;
  novo = false;
  modelo: ProdutoRequest = this.modeloVazio();
  variacaoId: string | null = null;
  variacaoQuantidade: number | null = null;
  variacaoUnidade: UnidadeMedida = 'G';
  variacaoDescricao = '';

  ngOnInit(): void {
    this.id = this.route.snapshot.paramMap.get('id');
    this.novo = this.id === null;

    if (this.novo) {
      forkJoin({
        categorias: this.api.listarCategorias(),
        unidades: this.api.listarUnidadesMedida(),
      }).subscribe({
        next: ({ categorias, unidades }) => {
          this.categorias.set(categorias);
          this.unidades.set(unidades);
          this.carregando.set(false);
        },
        error: (erro) => this.tratarErroCarregamento(erro),
      });
      return;
    }

    forkJoin({
      produto: this.api.obterProduto(this.id!),
      categorias: this.api.listarCategorias(),
      unidades: this.api.listarUnidadesMedida(),
    }).subscribe({
      next: ({ produto, categorias, unidades }) => {
        this.produto.set(produto);
        this.categorias.set(categorias);
        this.unidades.set(unidades);
        this.modelo = {
          nome: produto.nome,
          categoria_id: produto.categoria.id,
          nao_solicitar_marca: produto.nao_solicitar_marca,
          tratar_apenas_como_unidades: produto.tratar_apenas_como_unidades,
          contem_variacoes: produto.contem_variacoes,
          unidade_medida: produto.unidade_medida,
        };
        this.carregando.set(false);
        if (produto.contem_variacoes) this.carregarVariacoes();
      },
      error: (erro) => this.tratarErroCarregamento(erro),
    });
  }

  ajustarTipo(): void {
    if (this.modelo.tratar_apenas_como_unidades) {
      this.modelo.contem_variacoes = false;
      this.modelo.unidade_medida = null;
    } else if (!this.modelo.unidade_medida) {
      this.modelo.unidade_medida = 'KG';
    }
  }

  valido(): boolean {
    return (
      !!this.modelo.nome.trim() &&
      !!this.modelo.categoria_id &&
      (this.modelo.tratar_apenas_como_unidades || !!this.modelo.unidade_medida)
    );
  }

  salvarProduto(): void {
    if (!this.valido()) return;

    this.erro.set(null);
    this.salvando.set(true);
    const requisicao = this.id
      ? this.api.atualizarProduto(this.id, this.modelo)
      : this.api.criarProduto(this.modelo);

    requisicao.subscribe({
      next: () => void this.router.navigateByUrl('/cadastros/produtos'),
      error: (erro) => {
        this.salvando.set(false);
        this.erro.set(mensagemErro(erro));
      },
    });
  }

  novaVariacao(): void {
    this.variacaoId = null;
    this.variacaoQuantidade = null;
    this.variacaoUnidade = 'G';
    this.variacaoDescricao = '';
    this.editandoVariacao.set(true);
  }

  editarVariacao(variacao: VariacaoProduto): void {
    this.variacaoId = variacao.id;
    this.variacaoQuantidade = Number(variacao.quantidade);
    this.variacaoUnidade = variacao.unidade_medida;
    this.variacaoDescricao = variacao.descricao ?? '';
    this.editandoVariacao.set(true);
  }

  cancelarVariacao(): void {
    this.editandoVariacao.set(false);
  }

  variacaoValida(): boolean {
    return this.variacaoQuantidade !== null && this.variacaoQuantidade > 0;
  }

  salvarVariacao(): void {
    if (!this.id || !this.variacaoValida()) return;

    const valor = {
      quantidade: this.variacaoQuantidade!,
      unidade_medida: this.variacaoUnidade,
      descricao: this.variacaoDescricao.trim() || null,
    };
    const requisicao = this.variacaoId
      ? this.api.atualizarVariacao(this.id, this.variacaoId, valor)
      : this.api.criarVariacao(this.id, valor);

    this.erro.set(null);
    this.salvandoVariacao.set(true);
    requisicao.subscribe({
      next: () => {
        this.salvandoVariacao.set(false);
        this.editandoVariacao.set(false);
        this.carregarVariacoes();
      },
      error: (erro) => {
        this.salvandoVariacao.set(false);
        this.erro.set(mensagemErro(erro));
      },
    });
  }

  private carregarVariacoes(): void {
    if (!this.id) return;
    this.api.listarVariacoes(this.id).subscribe({
      next: (variacoes) => this.variacoes.set(variacoes),
      error: (erro) => this.erro.set(mensagemErro(erro)),
    });
  }

  private tratarErroCarregamento(erro: unknown): void {
    if (
      !this.novo &&
      erro instanceof HttpErrorResponse &&
      (erro.status === 404 || erro.status === 422)
    ) {
      void this.router.navigateByUrl('/cadastros/produtos');
      return;
    }
    this.carregando.set(false);
    this.erro.set(mensagemErro(erro));
  }

  private modeloVazio(): ProdutoRequest {
    return {
      nome: '',
      categoria_id: '',
      nao_solicitar_marca: false,
      tratar_apenas_como_unidades: false,
      contem_variacoes: false,
      unidade_medida: 'KG',
    };
  }
}
