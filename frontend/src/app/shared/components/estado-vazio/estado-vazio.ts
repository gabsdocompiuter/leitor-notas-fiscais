import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'lnf-estado-vazio',
  imports: [RouterLink],
  template: `
    <section class="row justify-content-center g-0 py-5 px-3 text-center">
      <div class="col-12 col-md-8 col-lg-6">
        <span
          class="d-inline-flex align-items-center justify-content-center p-3 rounded-4 bg-primary-subtle text-primary-emphasis fs-2 mb-3"
          ><i class="bi" [class]="icone()" aria-hidden="true"></i
        ></span>
        <h2 class="h5">{{ titulo() }}</h2>
        <p class="text-body-secondary mb-4">{{ mensagem() }}</p>
        @if (link()) {
          <a class="btn btn-primary rounded-pill" [routerLink]="link()">{{ acao() }}</a>
        }
      </div>
    </section>
  `,
})
export class EstadoVazio {
  readonly titulo = input.required<string>();
  readonly mensagem = input.required<string>();
  readonly icone = input('bi-receipt');
  readonly link = input<string | null>(null);
  readonly acao = input('Continuar');
}
