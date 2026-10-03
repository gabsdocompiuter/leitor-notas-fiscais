import { Component, computed, inject, input, signal } from '@angular/core';
import {
  decimalValido,
  formatarDecimal,
  formatarVariacao,
  limitarEntradaDecimal,
} from '../../../../core/utils/decimal.utils';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../core/api/api.service';
import {
  Produto,
  UnidadeMedida,
  UnidadeMedidaInfo,
  VariacaoProduto,
} from '../../../../core/models/api.models';
import { extrairMedida, normalizarQuantidade } from '../../../../core/utils/variacao.utils';
import { PesquisaCadastroBase } from '../../pesquisa-cadastro-base';

@Component({
  selector: 'lnf-pesquisa-variacao',
  imports: [FormsModule],
  templateUrl: './pesquisa-variacao.html',
})
export class PesquisaVariacao extends PesquisaCadastroBase<VariacaoProduto> {
  private readonly api = inject(ApiService);
  readonly produto = input.required<Produto>();
  readonly unidades = input.required<readonly UnidadeMedidaInfo[]>();
  readonly tituloPesquisa = 'Selecionar variação';
  readonly tituloCadastro = 'Confirmar criação';
  readonly placeholderPesquisa = 'Quantidade';
  readonly mensagemSemResultados = 'Nenhuma variação encontrada.';
  readonly formatarDecimal = formatarDecimal;
  readonly formatarVariacao = formatarVariacao;
  readonly quantidade = signal('');
  readonly unidade = signal<UnidadeMedida | ''>('');
  readonly podeCriar = computed(() => {
    const texto = this.quantidade().trim().replace(',', '.');
    const valor = Number(texto);
    return (
      decimalValido(texto) &&
      Number.isFinite(valor) &&
      valor >= 0.001 &&
      this.unidades().some((unidade) => unidade.codigo === this.unidade())
    );
  });
  override readonly resultados = computed(() => {
    const quantidade = normalizarQuantidade(this.quantidade());
    return this.registros()
      .filter(
        (variacao) =>
          (!quantidade || normalizarQuantidade(variacao.quantidade).startsWith(quantidade)) &&
          (!this.unidade() || variacao.unidade_medida === this.unidade()),
      )
      .slice(0, 30);
  });

  override ngOnInit(): void {
    super.ngOnInit();
    const medida = extrairMedida(this.contexto());
    if (medida && this.unidades().some((unidade) => unidade.codigo === medida.unidade)) {
      this.quantidade.set(medida.quantidade.replace('.', ','));
      this.unidade.set(medida.unidade);
    }
  }

  atualizarQuantidade(evento: Event): void {
    const campo = evento.target as HTMLInputElement;
    campo.value = limitarEntradaDecimal(campo.value);
    this.quantidade.set(campo.value);
  }

  override abrirCadastro(): void {
    if (this.podeCriar()) super.abrirCadastro();
  }

  criar(): void {
    if (!this.cadastroAberto() || !this.podeCriar() || this.salvando()) return;
    this.salvando.set(true);
    this.erro.set(null);
    this.api
      .criarVariacao(this.produto().id, {
        quantidade: Number(this.quantidade().replace(',', '.')),
        unidade_medida: this.unidade() as UnidadeMedida,
      })
      .subscribe({
        next: (variacao) => this.concluirCadastro(variacao),
        error: (erro) => this.tratarErro(erro),
      });
  }

  protected override textoPesquisa(variacao: VariacaoProduto): string {
    return variacao.nome_exibicao;
  }

  protected override prepararCadastro(_nomeInicial: string): void {}
}
