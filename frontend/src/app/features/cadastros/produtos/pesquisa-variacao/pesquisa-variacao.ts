import { Component, inject, input } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../../../core/api/api.service';
import {
  Produto,
  UnidadeMedida,
  UnidadeMedidaInfo,
  VariacaoProduto,
} from '../../../../core/models/api.models';
import { PesquisaCadastroBase } from '../../pesquisa-cadastro-base';

@Component({
  selector: 'lnf-pesquisa-variacao',
  imports: [ReactiveFormsModule],
  templateUrl: './pesquisa-variacao.html',
})
export class PesquisaVariacao extends PesquisaCadastroBase<VariacaoProduto> {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);

  readonly produto = input.required<Produto>();
  readonly unidades = input.required<readonly UnidadeMedidaInfo[]>();

  readonly tituloPesquisa = 'Selecionar variação';
  readonly tituloCadastro = 'Nova variação';
  readonly placeholderPesquisa = 'Pesquisar variação';
  readonly mensagemSemResultados = 'Nenhuma variação encontrada.';
  readonly formulario = this.fb.group({
    descricao: ['', Validators.maxLength(100)],
    quantidade: [null as number | null, [Validators.required, Validators.min(0.000001)]],
    unidade_medida: ['G' as UnidadeMedida, Validators.required],
  });

  criar(): void {
    this.formulario.markAllAsTouched();
    if (this.formulario.invalid || this.salvando()) return;

    const valor = this.formulario.getRawValue();
    this.salvando.set(true);
    this.erro.set(null);
    this.api
      .criarVariacao(this.produto().id, {
        quantidade: Number(valor.quantidade),
        unidade_medida: valor.unidade_medida!,
        descricao: valor.descricao?.trim() || null,
      })
      .subscribe({
        next: (variacao) => this.concluirCadastro(variacao),
        error: (erro) => this.tratarErro(erro),
      });
  }

  protected override textoPesquisa(variacao: VariacaoProduto): string {
    return variacao.nome_exibicao;
  }

  protected override prepararCadastro(nomeInicial: string): void {
    this.formulario.reset({
      descricao: nomeInicial,
      quantidade: null,
      unidade_medida: 'G',
    });
  }
}
