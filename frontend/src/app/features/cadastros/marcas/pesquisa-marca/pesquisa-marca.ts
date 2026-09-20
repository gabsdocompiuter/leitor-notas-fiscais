import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../../../core/api/api.service';
import { Marca } from '../../../../core/models/api.models';
import { PesquisaCadastroBase } from '../../pesquisa-cadastro-base';

@Component({
  selector: 'lnf-pesquisa-marca',
  imports: [ReactiveFormsModule],
  templateUrl: './pesquisa-marca.html',
})
export class PesquisaMarca extends PesquisaCadastroBase<Marca> {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);

  readonly tituloPesquisa = 'Selecionar marca';
  readonly tituloCadastro = 'Nova marca';
  readonly placeholderPesquisa = 'Pesquisar marca';
  readonly mensagemSemResultados = 'Nenhuma marca encontrada.';
  readonly formulario = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.maxLength(100), Validators.pattern(/\S/)]],
  });

  criar(): void {
    this.formulario.markAllAsTouched();
    if (this.formulario.invalid || this.salvando()) return;

    this.salvando.set(true);
    this.erro.set(null);
    this.api.criarMarca(this.formulario.controls.nome.value.trim()).subscribe({
      next: (marca) => this.concluirCadastro(marca),
      error: (erro) => this.tratarErro(erro),
    });
  }

  protected override textoPesquisa(marca: Marca): string {
    return marca.nome;
  }

  protected override prepararCadastro(nomeInicial: string): void {
    this.formulario.reset({ nome: nomeInicial });
  }
}
