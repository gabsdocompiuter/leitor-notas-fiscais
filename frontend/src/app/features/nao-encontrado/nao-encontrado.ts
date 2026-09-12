import { Component } from '@angular/core';
import { EstadoVazio } from '../../shared/components/estado-vazio/estado-vazio';

@Component({
  selector: 'lnf-nao-encontrado',
  imports: [EstadoVazio],
  template: `
    <div class="container page-section">
      <lnf-estado-vazio
        titulo="Página não encontrada"
        mensagem="O endereço informado não existe nesta aplicação."
        icone="bi-signpost-split"
        link="/notas"
        acao="Voltar para notas"
      />
    </div>
  `,
})
export class NaoEncontrado {}
