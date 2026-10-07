import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { TemaService } from './tema.service';

describe('preferência de tema', () => {
  let escuro: boolean;
  let consulta: MediaQueryList;
  let meta: HTMLMetaElement;

  beforeEach(() => {
    escuro = false;
    consulta = Object.assign(new EventTarget(), {
      get matches() {
        return escuro;
      },
    }) as MediaQueryList;
    // Object.assign avalia getters; manter a leitura dinâmica da preferência do sistema.
    Object.defineProperty(consulta, 'matches', { get: () => escuro });
    vi.stubGlobal(
      'matchMedia',
      vi.fn(() => consulta),
    );
    localStorage.clear();
    meta = document.createElement('meta');
    meta.name = 'theme-color';
    document.head.append(meta);
  });

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    localStorage.clear();
    document.documentElement.removeAttribute('data-bs-theme');
    meta.remove();
  });

  function mudarSistema(valor: boolean) {
    escuro = valor;
    consulta.dispatchEvent(new Event('change'));
  }

  it('usa Sistema inicialmente e acompanha suas mudanças', () => {
    const servico = TestBed.inject(TemaService);
    expect(servico.preferencia()).toBe('sistema');
    expect(document.documentElement.dataset['bsTheme']).toBe('light');
    mudarSistema(true);
    expect(document.documentElement.dataset['bsTheme']).toBe('dark');
    expect(meta.content).toBe('#212529');
    mudarSistema(false);
    expect(document.documentElement.dataset['bsTheme']).toBe('light');
    expect(meta.content).toBe('#ffffff');
  });

  it('salva a escolha explícita, ignora o sistema e permite voltar a segui-lo', () => {
    const servico = TestBed.inject(TemaService);
    servico.definirPreferencia('escuro');
    mudarSistema(false);
    expect(document.documentElement.dataset['bsTheme']).toBe('dark');
    expect(localStorage.getItem('lnf-tema')).toBe('escuro');
    servico.definirPreferencia('claro');
    mudarSistema(true);
    expect(document.documentElement.dataset['bsTheme']).toBe('light');
    servico.definirPreferencia('sistema');
    expect(document.documentElement.dataset['bsTheme']).toBe('dark');
    expect(localStorage.getItem('lnf-tema')).toBe('sistema');
  });

});
