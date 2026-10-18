import { Component } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, describe, expect, it } from 'vitest';
import { SeletorSabor } from './seletor-sabor';

afterEach(() => TestBed.inject(HttpTestingController).verify());

function montar() {
  TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
  const fixture = TestBed.createComponent(SeletorSabor);
  const http = TestBed.inject(HttpTestingController);
  fixture.componentRef.setInput('produtoId', 'iogurte');
  fixture.componentRef.setInput('contexto', 'IOGURTE MORANGO 200G');
  fixture.detectChanges();
  http.expectOne(r => r.url.endsWith('/produtos/iogurte/sabores')).flush([
    { id: 'morango', produto_id: 'iogurte', nome: 'Morango' },
  ]);
  fixture.detectChanges();
  const selecionados: (string | null)[] = [];
  fixture.componentInstance.alterado.subscribe(id => selecionados.push(id));
  return { fixture, http, selecionados };
}

@Component({
  imports: [SeletorSabor],
  template: '<form (submit)="envios = envios + 1"><lnf-seletor-sabor produtoId="iogurte" contexto="Morango" /></form>',
})
class FormularioTeste { envios = 0; }

describe('seletor de sabor', () => {
  it('pesquisa e cria sem enviar o formulário da nota', () => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    const fixture = TestBed.createComponent(FormularioTeste);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne(r => r.url.endsWith('/produtos/iogurte/sabores')).flush([]);
    fixture.detectChanges();
    fixture.nativeElement.querySelector('button').click();
    fixture.detectChanges();
    const tecla = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true });
    fixture.nativeElement.querySelector('input[type=search]').dispatchEvent(tecla);
    expect(tecla.defaultPrevented).toBe(true);
    fixture.nativeElement.querySelector('button[aria-label="Criar sabor"]').click();
    fixture.detectChanges();
    fixture.nativeElement.querySelector('.modal form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    http.expectOne(r => r.method === 'POST').flush({ id: 'morango', produto_id: 'iogurte', nome: 'Morango' });
    expect(fixture.componentInstance.envios).toBe(0);
  });
  it('abre com descrição fiscal, cursor no fim, pesquisa e seleciona sabor existente', async () => {
    const { fixture, selecionados } = montar();
    expect(fixture.nativeElement.textContent).toContain('Selecionar sabor');
    fixture.nativeElement.querySelector('button').click();
    fixture.detectChanges();
    await new Promise(resolve => setTimeout(resolve, 10));
    const busca = fixture.nativeElement.querySelector('input[type=search]') as HTMLInputElement;
    expect(busca.value).toBe('Iogurte Morango 200g');
    expect(busca.selectionStart).toBe(busca.value.length);
    expect(busca.selectionEnd).toBe(busca.value.length);
    busca.value = 'morango';
    busca.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    fixture.nativeElement.querySelector('.list-group-item').click();
    fixture.detectChanges();
    expect(selecionados).toEqual(['morango']);
    expect(fixture.nativeElement.querySelector('[role=dialog]')).toBeNull();
    fixture.componentRef.setInput('valor', 'morango');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('button').textContent).toContain('Morango');
  });

  it('confirma criação pelo produto, seleciona e descarta lista ao trocar produto', () => {
    const { fixture, http, selecionados } = montar();
    fixture.componentInstance.abrir();
    fixture.detectChanges();
    const busca = fixture.nativeElement.querySelector('input[type=search]');
    busca.value = 'Baunilha';
    busca.dispatchEvent(new Event('input'));
    fixture.nativeElement.querySelector('button[aria-label="Criar sabor"]').click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Deseja criar o sabor “Baunilha”');
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true }));
    const envio = http.expectOne(r => r.method === 'POST');
    expect(envio.request.url).toContain('/produtos/iogurte/sabores');
    expect(envio.request.body).toEqual({ nome: 'Baunilha' });
    envio.flush({ id: 'baunilha', produto_id: 'iogurte', nome: 'Baunilha' });
    fixture.detectChanges();
    expect(selecionados).toEqual(['baunilha']);
    expect(fixture.componentInstance.sabores()).toHaveLength(2);
    fixture.componentRef.setInput('produtoId', 'suco');
    fixture.detectChanges();
    expect(fixture.componentInstance.sabores()).toEqual([]);
    http.expectOne(r => r.url.endsWith('/produtos/suco/sabores')).flush([]);
  });

  it('não oferece remoção na pesquisa, permite cancelar e respeita campo desabilitado', () => {
    const { fixture, selecionados } = montar();
    fixture.componentInstance.abrir();
    fixture.detectChanges();
    fixture.nativeElement.querySelector('button[aria-label="Fechar"]').click();
    fixture.detectChanges();
    expect(selecionados).toEqual([]);
    fixture.componentInstance.abrir();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('Sem sabor informado');
    fixture.componentRef.setInput('disabled', true);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('button').disabled).toBe(true);
    fixture.componentInstance.abrir();
    expect(fixture.componentInstance.aberto()).toBe(false);
  });

  it('mantém confirmação aberta e exibe erro se a criação falhar', () => {
    const { fixture, http, selecionados } = montar();
    fixture.componentInstance.abrir();
    fixture.detectChanges();
    fixture.nativeElement.querySelector('button[aria-label="Criar sabor"]').click();
    fixture.detectChanges();
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true }));
    http.expectOne(r => r.method === 'POST').flush({ detail: 'Falha ao salvar sabor' }, { status: 500, statusText: 'Erro' });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=alert]')).not.toBeNull();
    expect(fixture.componentInstance.aberto()).toBe(true);
    expect(selecionados).toEqual([]);
  });
});
