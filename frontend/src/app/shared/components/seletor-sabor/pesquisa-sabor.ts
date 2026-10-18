import { Component, inject, input } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../../core/api/api.service';
import { SaborProduto } from '../../../core/models/api.models';
import { PesquisaCadastroBase } from '../../../features/cadastros/pesquisa-cadastro-base';

@Component({
  selector: 'lnf-pesquisa-sabor',
  imports: [ReactiveFormsModule],
  templateUrl: './pesquisa-sabor.html',
})
export class PesquisaSabor extends PesquisaCadastroBase<SaborProduto> {
  private readonly api = inject(ApiService);
  readonly produtoId = input.required<string>();
  private readonly fb = inject(FormBuilder);

  readonly tituloPesquisa = 'Selecionar sabor';
  readonly tituloCadastro = 'Novo sabor';
  readonly placeholderPesquisa = 'Pesquisar sabor';
  readonly mensagemSemResultados = 'Nenhum sabor encontrado.';
  readonly formulario = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.maxLength(100), Validators.pattern(/\S/)]],
  });

  override abrirCadastro(): void {
    if (this.salvando()) return;
    this.prepararCadastro(this.busca().trim());
    if (this.formulario.invalid) {
      this.erro.set('Informe um nome com até 100 caracteres.');
      this.focarPesquisa();
      return;
    }
    super.abrirCadastro();
  }

  criar(): void {
    this.formulario.markAllAsTouched();
    if (!this.cadastroAberto() || this.formulario.invalid || this.salvando()) return;

    this.salvando.set(true);
    this.erro.set(null);
    this.api.criarSabor(this.produtoId(), this.formulario.controls.nome.value.trim()).subscribe({
      next: (sabor) => this.concluirCadastro(sabor),
      error: (erro) => this.tratarErro(erro),
    });
  }

  protected override textoPesquisa(sabor: SaborProduto): string {
    return sabor.nome;
  }

  protected override prepararCadastro(nomeInicial: string): void {
    this.formulario.reset({ nome: nomeInicial });
  }
}
