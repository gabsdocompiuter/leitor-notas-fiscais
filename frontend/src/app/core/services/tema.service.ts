import { DOCUMENT } from '@angular/common';
import { DestroyRef, Injectable, inject, signal } from '@angular/core';

export type PreferenciaTema = 'sistema' | 'claro' | 'escuro';
const CHAVE_TEMA = 'lnf-tema';

function preferenciaValida(valor: string | null): valor is PreferenciaTema {
  return valor === 'sistema' || valor === 'claro' || valor === 'escuro';
}

@Injectable({ providedIn: 'root' })
export class TemaService {
  private readonly documento = inject(DOCUMENT);
  private readonly janela = this.documento.defaultView;
  private readonly sistema = this.janela?.matchMedia?.('(prefers-color-scheme: dark)');
  private readonly escolha = signal<PreferenciaTema>('sistema');
  readonly preferencia = this.escolha.asReadonly();

  constructor() {
    try {
      const salva = this.janela?.localStorage.getItem(CHAVE_TEMA) ?? null;
      if (preferenciaValida(salva)) this.escolha.set(salva);
    } catch {
      // O tema continua funcionando quando o navegador bloqueia o armazenamento.
    }
    this.aplicar();
    const atualizarSistema = () => {
      if (this.preferencia() === 'sistema') this.aplicar();
    };
    this.sistema?.addEventListener('change', atualizarSistema);
    inject(DestroyRef).onDestroy(() =>
      this.sistema?.removeEventListener('change', atualizarSistema),
    );
  }

  definirPreferencia(valor: string) {
    if (!preferenciaValida(valor)) return;
    this.escolha.set(valor);
    this.aplicar();
    try {
      this.janela?.localStorage.setItem(CHAVE_TEMA, valor);
    } catch {
      // A escolha permanece válida nesta sessão, mesmo sem persistência.
    }
  }

  private aplicar() {
    const escuro =
      this.preferencia() === 'escuro' ||
      (this.preferencia() === 'sistema' && this.sistema?.matches === true);
    this.documento.documentElement.setAttribute('data-bs-theme', escuro ? 'dark' : 'light');
    this.documento
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute('content', escuro ? '#212529' : '#ffffff');
  }
}
