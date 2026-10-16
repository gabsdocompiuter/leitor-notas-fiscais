import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../../../core/api/api.service';
import { Estabelecimento } from '../../../../core/models/api.models';
import { PesquisaCadastroBase } from '../../pesquisa-cadastro-base';

@Component({
  selector: 'lnf-pesquisa-estabelecimento',
  imports: [ReactiveFormsModule],
  templateUrl: './pesquisa-estabelecimento.html',
})
export class PesquisaEstabelecimento extends PesquisaCadastroBase<Estabelecimento> {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);

  readonly tituloPesquisa = 'Selecionar estabelecimento';
  readonly tituloCadastro = 'Criar estabelecimento';
  readonly placeholderPesquisa = 'Pesquisar estabelecimento';
  readonly mensagemSemResultados = 'Nenhum estabelecimento encontrado.';
  readonly formulario = this.fb.group({
    apelido: ['', [Validators.required, Validators.maxLength(100), Validators.pattern(/\S/)]],
  });

  override abrirCadastro(): void {
    super.abrirCadastro();
    setTimeout(() => document.getElementById('novo-apelido')?.focus());
  }

  criar(): void {
    this.formulario.markAllAsTouched();
    if (this.formulario.invalid || this.salvando()) return;
    this.salvando.set(true);
    this.erro.set(null);
    this.api.criarEstabelecimento(this.formulario.controls.apelido.value!.trim()).subscribe({
      next: (registro) => this.concluirCadastro(registro),
      error: (erro) => this.tratarErro(erro),
    });
  }

  protected override textoPesquisa(registro: Estabelecimento): string {
    return [registro.nome_exibicao, registro.razao_social, registro.cnpj].filter(Boolean).join(' ');
  }

  protected override prepararCadastro(apelido: string): void {
    this.formulario.reset({ apelido });
  }
}
