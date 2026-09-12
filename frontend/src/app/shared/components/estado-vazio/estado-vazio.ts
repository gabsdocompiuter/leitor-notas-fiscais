import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'lnf-estado-vazio',
  imports: [RouterLink],
  template: `
    <section class="empty-state text-center mx-auto py-5">
      <span class="empty-icon mb-3"><i class="bi" [class]="icone()"></i></span>
      <h2 class="h5">{{ titulo() }}</h2>
      <p class="text-secondary mb-4">{{ mensagem() }}</p>
      @if (link()) {
        <a class="btn btn-primary rounded-pill" [routerLink]="link()">{{ acao() }}</a>
      }
    </section>
  `,
  styles: `
    .empty-state {
      max-width: 28rem;
    }
    .empty-icon {
      display: grid;
      width: 4rem;
      height: 4rem;
      place-items: center;
      margin-inline: auto;
      color: var(--lnf-primary);
      background: var(--lnf-primary-soft);
      border-radius: 1.25rem;
      font-size: 1.6rem;
    }
  `,
})
export class EstadoVazio {
  readonly titulo = input.required<string>();
  readonly mensagem = input.required<string>();
  readonly icone = input('bi-receipt');
  readonly link = input<string | null>(null);
  readonly acao = input('Continuar');
}
