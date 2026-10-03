import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SeletorTags } from './seletor-tags';

const populares = [
  { id: '1', nome: 'Festa' },
  { id: '2', nome: 'Crianças' },
];

describe('seleção de tags', () => {
  function criar() {
    vi.useFakeTimers();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    const fixture = TestBed.createComponent(SeletorTags);
    fixture.componentRef.setInput('selecionadas', [populares[0]]);
    fixture.detectChanges();
    const http = TestBed.inject(HttpTestingController);
    const input = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    return { fixture, http, input };
  }

  afterEach(() => {
    TestBed.inject(HttpTestingController).verify();
    vi.useRealTimers();
  });

  it('consulta as tags populares no foco e mostra sugestões cinzas antes das selecionadas', async () => {
    const { fixture, http, input } = criar();
    input.dispatchEvent(new FocusEvent('focus'));
    await vi.advanceTimersByTimeAsync(0);
    const consulta = http.expectOne((req) => req.url.endsWith('/tags'));
    expect(consulta.request.params.has('busca')).toBe(false);
    consulta.flush(populares);
    fixture.detectChanges();
    expect(fixture.componentInstance.sugestoes().map((tag) => tag.id)).toEqual(['2']);
    const sugestoes = fixture.nativeElement.querySelector('[aria-label="Tags disponíveis"]');
    const selecionadas = fixture.nativeElement.querySelector('[aria-label="Tags selecionadas"]');
    expect(
      sugestoes.compareDocumentPosition(selecionadas) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    for (const badge of fixture.nativeElement.querySelectorAll('button')) {
      expect(badge.classList.contains('badge')).toBe(true);
      expect(badge.classList.contains('rounded-pill')).toBe(true);
    }
    expect(sugestoes.querySelector('button').classList.contains('text-bg-secondary')).toBe(true);
    expect(selecionadas.querySelector('button').classList.contains('text-bg-primary')).toBe(true);
    expect(fixture.nativeElement.textContent).not.toContain('Fechar sugestões');
  });

  it('só filtra a partir de três caracteres e volta às populares ao apagar', async () => {
    const { fixture, http } = criar();
    const seletor = fixture.componentInstance;
    seletor.abrirSugestoes();
    await vi.advanceTimersByTimeAsync(0);
    http.expectOne((req) => req.url.endsWith('/tags')).flush(populares);
    seletor.atualizarBusca('c');
    seletor.atualizarBusca('cr');
    await vi.advanceTimersByTimeAsync(300);
    http.expectNone((req) => req.url.endsWith('/tags'));
    expect(seletor.sugestoes()).toEqual([populares[1]]);
    seletor.atualizarBusca(' CRI ');
    await vi.advanceTimersByTimeAsync(249);
    http.expectNone((req) => req.url.endsWith('/tags'));
    await vi.advanceTimersByTimeAsync(1);
    const filtrada = http.expectOne((req) => req.params.get('busca') === 'CRI');
    filtrada.flush([populares[1]]);
    seletor.atualizarBusca('cr');
    await vi.advanceTimersByTimeAsync(0);
    const geral = http.expectOne((req) => req.url.endsWith('/tags'));
    expect(geral.request.params.has('busca')).toBe(false);
    geral.flush(populares);
  });

  it('cancela a consulta anterior para não exibir respostas de outro filtro', async () => {
    const { fixture, http } = criar();
    const seletor = fixture.componentInstance;
    seletor.abrirSugestoes();
    await vi.advanceTimersByTimeAsync(0);
    const anterior = http.expectOne((req) => req.url.endsWith('/tags'));
    seletor.atualizarBusca('cria');
    expect(anterior.cancelled).toBe(true);
    seletor.atualizarBusca('crian');
    await vi.advanceTimersByTimeAsync(250);
    http.expectOne((req) => req.params.get('busca') === 'crian').flush([populares[1]]);
    expect(seletor.sugestoes()).toEqual([populares[1]]);
  });

  it('coloca Criar primeiro e impede criar uma tag selecionada ou sugerida', async () => {
    const { fixture, http } = criar();
    const seletor = fixture.componentInstance;
    seletor.abrirSugestoes();
    await vi.advanceTimersByTimeAsync(0);
    http.expectOne((req) => req.url.endsWith('/tags')).flush(populares);
    seletor.atualizarBusca('ab');
    fixture.detectChanges();
    expect(
      fixture.nativeElement.querySelector('[aria-label="Tags disponíveis"] button').textContent,
    ).toContain('Criar');
    seletor.atualizarBusca(' crianças ');
    await vi.advanceTimersByTimeAsync(250);
    http.expectOne((req) => req.params.get('busca') === 'crianças').flush([populares[1]]);
    expect(seletor.podeCriar()).toBe(false);
    seletor.atualizarBusca('Festa');
    expect(seletor.podeCriar()).toBe(false);
    seletor.fecharSugestoes();
  });

  it('Enter seleciona a tag existente e não envia o formulário do item', async () => {
    const { fixture, http } = criar();
    const seletor = fixture.componentInstance;
    const emitir = vi.spyOn(seletor.adicionar, 'emit');
    seletor.atualizarBusca(' crianças ');
    seletor.abrirSugestoes();
    await vi.advanceTimersByTimeAsync(250);
    http.expectOne((req) => req.params.get('busca') === 'crianças').flush([populares[1]]);
    const evento = new KeyboardEvent('keydown', { key: 'Enter', cancelable: true });
    seletor.confirmarBusca(evento);
    expect(evento.defaultPrevented).toBe(true);
    expect(emitir).toHaveBeenCalledWith('Crianças');
    expect(seletor.busca()).toBe('');
    expect(seletor.aberto()).toBe(true);
  });

  it('mantém as sugestões abertas e retira somente a tag selecionada', async () => {
    const { fixture, http, input } = criar();
    const extra = { id: '3', nome: 'Viagem' };
    const emitir = vi.spyOn(fixture.componentInstance.adicionar, 'emit');
    input.dispatchEvent(new FocusEvent('focus'));
    await vi.advanceTimersByTimeAsync(0);
    http.expectOne((req) => req.url.endsWith('/tags')).flush([...populares, extra]);
    fixture.detectChanges();
    const botoes = fixture.nativeElement.querySelectorAll('[aria-label="Tags disponíveis"] button');
    botoes[0].click();
    expect(emitir).toHaveBeenCalledWith('Crianças');
    fixture.componentRef.setInput('selecionadas', populares);
    fixture.detectChanges();
    const sugestoes = fixture.nativeElement.querySelector('[aria-label="Tags disponíveis"]');
    expect(sugestoes).not.toBeNull();
    expect(sugestoes.textContent).toContain('Viagem');
    expect(sugestoes.textContent).not.toContain('Crianças');
    expect(fixture.componentInstance.sugestoes()).toEqual([extra]);
    sugestoes.querySelector('button').click();
    expect(emitir).toHaveBeenLastCalledWith('Viagem');
    http.expectNone((req) => req.url.endsWith('/tags'));
  });

  it('preserva tags selecionadas e bloqueia ações enquanto salva', () => {
    const { fixture } = criar();
    const seletor = fixture.componentInstance;
    const emitir = vi.spyOn(seletor.adicionar, 'emit');
    seletor.atualizarBusca('Festa');
    seletor.confirmarBusca(new Event('keydown'));
    fixture.componentRef.setInput('ocupado', true);
    seletor.selecionar('Crianças');
    expect(emitir).not.toHaveBeenCalled();
  });

  it('permite buscar novamente depois de uma falha no backend', async () => {
    const { fixture, http } = criar();
    const seletor = fixture.componentInstance;
    seletor.abrirSugestoes();
    await vi.advanceTimersByTimeAsync(0);
    http
      .expectOne((req) => req.url.endsWith('/tags'))
      .flush({}, { status: 500, statusText: 'Erro' });
    expect(seletor.erro()).toBe(true);
    seletor.abrirSugestoes();
    await vi.advanceTimersByTimeAsync(0);
    http.expectOne((req) => req.url.endsWith('/tags')).flush(populares);
    expect(seletor.erro()).toBe(false);
    expect(seletor.sugestoes()).toEqual([populares[1]]);
  });
});
