import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from './app';

describe('menu de navegação responsivo', () => {
  let fixture: ComponentFixture<App>;

  afterEach(() => {
    fixture?.destroy();
    fixture?.nativeElement.remove();
    TestBed.resetTestingModule();
    vi.useRealTimers();
    document.documentElement.removeAttribute('data-bs-theme');
  });

  it('o X fecha o painel responsivo e libera o fundo e a rolagem', () => {
    vi.useFakeTimers();
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
    fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    document.body.append(fixture.nativeElement);

    const botao = fixture.nativeElement.querySelector('.navbar-toggler') as HTMLButtonElement;
    const painel = fixture.nativeElement.querySelector('#menu-principal') as HTMLElement;
    const fechar = fixture.nativeElement.querySelector(
      '[aria-label="Fechar menu"]',
    ) as HTMLButtonElement;

    botao.click();
    vi.runAllTimers();
    fixture.detectChanges();
    expect(painel.getAttribute('aria-modal')).toBe('true');
    expect(document.body.style.overflow).toBe('hidden');
    expect(botao.getAttribute('aria-expanded')).toBe('true');

    fechar.click();
    vi.runAllTimers();
    fixture.detectChanges();
    expect(painel.hasAttribute('aria-modal')).toBe(false);
    expect(painel.classList.contains('show')).toBe(false);
    expect(document.querySelector('.offcanvas-backdrop')).toBeNull();
    expect(document.body.style.overflow).toBe('');
    expect(botao.getAttribute('aria-expanded')).toBe('false');
  });
});
