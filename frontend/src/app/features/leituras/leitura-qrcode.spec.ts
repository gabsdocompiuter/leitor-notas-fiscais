import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { LeituraQrcode } from './leitura-qrcode';

const URL_NOTA = 'https://dfe-portal.svrs.rs.gov.br/Dfe/QrCodeNFce?p=123|3|1';

describe('leitura manual de nota', () => {
  afterEach(() => {
    TestBed.inject(HttpTestingController).verify();
  });

  function criar() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    const fixture = TestBed.createComponent(LeituraQrcode);
    const navegar = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const campo = fixture.nativeElement.querySelector('textarea') as HTMLTextAreaElement;
    const formulario = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    const botao = fixture.nativeElement.querySelector('button[type=submit]') as HTMLButtonElement;

    function preencher(valor: string) {
      campo.value = valor;
      campo.dispatchEvent(new Event('input', { bubbles: true }));
      fixture.detectChanges();
    }

    return { fixture, http, navegar, formulario, botao, preencher };
  }

  it('o botão consulta a URL digitada, impede o envio nativo e abre a revisão', () => {
    const { fixture, http, navegar, formulario, botao, preencher } = criar();
    preencher('  ' + URL_NOTA + '  ');
    let evento: Event | undefined;
    formulario.addEventListener('submit', (atual) => {
      evento = atual;
    });
    botao.click();

    expect(evento?.defaultPrevented).toBe(true);
    const consulta = http.expectOne((request) => request.url.endsWith('/leituras'));
    expect(consulta.request.method).toBe('POST');
    expect(consulta.request.body).toEqual({ url: URL_NOTA });
    consulta.flush({ nota: { chave: 'chave-da-nota' }, erro_consulta: null });
    expect(navegar).toHaveBeenCalledWith(['/notas', 'chave-da-nota', 'revisao']);
    expect(fixture.componentInstance.enviando()).toBe(false);
  });

  it('não consulta um campo vazio ou preenchido apenas com espaços', () => {
    const { fixture, http, botao, preencher } = criar();
    preencher('   ');
    botao.click();
    fixture.detectChanges();
    http.expectNone((request) => request.url.endsWith('/leituras'));
    expect(fixture.componentInstance.url.hasError('required')).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Informe o link lido no QR Code.');
  });

  it('bloqueia envios repetidos e permite tentar novamente depois de um erro', () => {
    const { fixture, http, navegar, formulario, botao, preencher } = criar();
    preencher(URL_NOTA);
    botao.click();
    fixture.detectChanges();
    expect(botao.disabled).toBe(true);
    const consulta = http.expectOne((request) => request.url.endsWith('/leituras'));
    formulario.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    http.expectNone((request) => request.url.endsWith('/leituras'));

    consulta.flush(
      { mensagem: 'Não foi possível consultar a nota.' },
      { status: 502, statusText: 'Bad Gateway' },
    );
    fixture.detectChanges();
    expect(navegar).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('Não foi possível consultar a nota.');
    expect(botao.disabled).toBe(false);
    expect(fixture.componentInstance.url.value).toBe(URL_NOTA);

    botao.click();
    http
      .expectOne((request) => request.url.endsWith('/leituras'))
      .flush({ nota: { chave: 'segunda-tentativa' } });
    expect(navegar).toHaveBeenCalledWith(['/notas', 'segunda-tentativa', 'revisao']);
  });

  it('mantém a tela de leitura quando a consulta não retorna uma nota', () => {
    const { fixture, http, navegar, botao, preencher } = criar();
    preencher(URL_NOTA);
    botao.click();
    http
      .expectOne((request) => request.url.endsWith('/leituras'))
      .flush({
        nota: null,
        erro_consulta: 'Nota não encontrada.',
      });
    fixture.detectChanges();
    expect(navegar).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('Nota não encontrada.');
    expect(fixture.componentInstance.enviando()).toBe(false);
  });
});
