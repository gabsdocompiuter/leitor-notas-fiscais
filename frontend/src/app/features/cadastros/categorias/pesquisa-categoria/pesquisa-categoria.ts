import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../../../core/api/api.service';
import { Categoria } from '../../../../core/models/api.models';
import { PesquisaCadastroBase } from '../../pesquisa-cadastro-base';

@Component({
  selector: 'lnf-pesquisa-categoria',
  imports: [ReactiveFormsModule],
  templateUrl: './pesquisa-categoria.html',
})
export class PesquisaCategoria extends PesquisaCadastroBase<Categoria> {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);

  readonly tituloPesquisa = 'Selecionar categoria';
  readonly tituloCadastro = 'Nova categoria';
  readonly placeholderPesquisa = 'Pesquisar categoria';
  readonly mensagemSemResultados = 'Nenhuma categoria encontrada.';
  readonly formulario = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.maxLength(100), Validators.pattern(/\S/)]],
  });

  criar(): void {
    this.formulario.markAllAsTouched();
    if (this.formulario.invalid || this.salvando()) return;

    this.salvando.set(true);
    this.erro.set(null);
    this.api.criarCategoria(this.formulario.controls.nome.value.trim()).subscribe({
      next: (categoria) => this.concluirCadastro(categoria),
      error: (erro) => this.tratarErro(erro),
    });
  }

  protected override textoPesquisa(categoria: Categoria): string {
    return categoria.nome;
  }

  protected override prepararCadastro(nomeInicial: string): void {
    this.formulario.reset({ nome: nomeInicial });
  }
}
