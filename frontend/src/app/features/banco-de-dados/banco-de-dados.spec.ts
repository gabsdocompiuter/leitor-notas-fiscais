import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { BancoDeDados } from './banco-de-dados';

describe('Banco de dados', () => {
  afterEach(() => {
    TestBed.inject(HttpTestingController).verify();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  function criar(permitir: boolean | null = true) {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    const fixture = TestBed.createComponent(BancoDeDados);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    const configuracao = http.expectOne((r) => r.url.endsWith('/banco/configuracao'));
    if (permitir === null) configuracao.flush({}, { status: 500, statusText: 'Erro' });
    else configuracao.flush({ permitir_importacao: permitir });
    fixture.detectChanges();
    const componente = fixture.componentInstance;
    function selecionar(arquivo = new File(['SQLite'], 'copia.sqlite3')) {
      componente.selecionar({ target: { files: [arquivo], value: '' } } as unknown as Event);
      fixture.detectChanges();
      return arquivo;
    }
    return { fixture, http, componente, selecionar };
  }

  it.each([false, null])('omite toda a importação quando configuração é %s', (permitir) => {
    const { fixture } = criar(permitir);
    expect(fixture.nativeElement.textContent).toContain('Exportar banco');
    expect(fixture.nativeElement.textContent).not.toContain('Importar');
    expect(fixture.nativeElement.textContent).not.toContain('indisponível');
    expect(fixture.nativeElement.querySelector('input[type=file]')).toBeNull();
  });

  it('seleciona, mostra confirmação e cancela sem chamar a API', () => {
    const { fixture, http, componente, selecionar } = criar();
    selecionar();
    componente.pedirConfirmacao();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=dialog]')).not.toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Todos os dados atuais serão substituídos');
    componente.cancelar();
    componente.importar();
    http.expectNone((r) => r.url.endsWith('/banco/importacao'));
  });

  it('envia apenas arquivo após confirmar, impede duplicação e recarrega após sucesso', () => {
    const { http, componente, selecionar } = criar();
    const arquivo = selecionar();
    const recarregar = vi.spyOn(componente, 'recarregar').mockImplementation(() => {});
    componente.pedirConfirmacao();
    componente.importar();
    const envio = http.expectOne((r) => r.url.endsWith('/banco/importacao'));
    expect(envio.request.method).toBe('POST');
    expect(envio.request.body).toBeInstanceOf(FormData);
    expect(Array.from((envio.request.body as FormData).keys())).toEqual(['arquivo']);
    expect((envio.request.body as FormData).get('arquivo')).toBe(arquivo);
    componente.pedirConfirmacao();
    componente.importar();
    http.expectNone((r) => r.url.endsWith('/banco/importacao'));
    envio.flush({ mensagem: 'Banco importado.' });
    expect(recarregar).toHaveBeenCalledOnce();
    expect(componente.processando()).toBe(false);
  });

  it('preserva a seleção após erro e permite tentar novamente', () => {
    const { http, componente, selecionar } = criar();
    const arquivo = selecionar();
    componente.pedirConfirmacao();
    componente.importar();
    http
      .expectOne((r) => r.url.endsWith('/banco/importacao'))
      .flush({ mensagem: 'Arquivo inválido.' }, { status: 422, statusText: 'Erro' });
    expect(componente.erro()).toBe('Arquivo inválido.');
    expect(componente.arquivo()).toBe(arquivo);
    expect(componente.processando()).toBe(false);
    componente.pedirConfirmacao();
    expect(componente.confirmando()).toBe(true);
  });

  it('oculta importação se a API passar a negar permissão', () => {
    const { fixture, http, componente, selecionar } = criar();
    selecionar();
    componente.pedirConfirmacao();
    componente.importar();
    http
      .expectOne((r) => r.url.endsWith('/banco/importacao'))
      .flush({ mensagem: 'Importação desabilitada.' }, { status: 403, statusText: 'Forbidden' });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('input[type=file]')).toBeNull();
  });

  it('rejeita extensão incorreta, arquivo vazio e arquivo acima do limite', () => {
    const { componente, selecionar } = criar();
    for (const arquivo of [new File(['abc'], 'copia.txt'), new File([], 'copia.db')]) {
      selecionar(arquivo);
      expect(componente.arquivo()).toBeNull();
      expect(componente.erro()).not.toBeNull();
    }
    const grande = new File(['abc'], 'copia.db');
    Object.defineProperty(grande, 'size', { value: componente.limite + 1 });
    selecionar(grande);
    expect(componente.arquivo()).toBeNull();
  });

  it('baixa o blob com o nome informado pela API e libera o recurso', () => {
    const { http, componente } = criar(false);
    const criarUrl = vi.fn().mockReturnValue('blob:teste');
    const revogar = vi.fn();
    vi.stubGlobal(
      'URL',
      class extends URL {
        static override createObjectURL = criarUrl;
        static override revokeObjectURL = revogar;
      },
    );
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    componente.exportar();
    const pedido = http.expectOne((r) => r.url.endsWith('/banco/exportacao'));
    expect(pedido.request.responseType).toBe('blob');
    pedido.flush(new Blob(['SQLite']), {
      headers: { 'Content-Disposition': 'attachment; filename="notas-2026.sqlite3"' },
    });
    expect(criarUrl).toHaveBeenCalledOnce();
    expect(click).toHaveBeenCalledOnce();
    expect(revogar).toHaveBeenCalledWith('blob:teste');
    expect(componente.processando()).toBe(false);
  });
  it('mantém foco no modal, permite Escape e devolve foco ao botão de importação', async () => {
    const { fixture, componente, selecionar } = criar();
    selecionar();
    componente.pedirConfirmacao();
    fixture.detectChanges();
    await fixture.whenStable();
    const dialogo = fixture.nativeElement.querySelector('[role=dialog]') as HTMLElement;
    const botoes = dialogo.querySelectorAll<HTMLButtonElement>('button');
    expect(document.activeElement).toBe(dialogo.querySelector('[data-cancelar]'));
    botoes[botoes.length - 1].focus();
    botoes[botoes.length - 1].dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }),
    );
    expect(document.activeElement).toBe(botoes[0]);
    botoes[0].dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true, cancelable: true }),
    );
    expect(document.activeElement).toBe(botoes[botoes.length - 1]);
    dialogo.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=dialog]')).toBeNull();
    expect(document.activeElement?.textContent).toContain('Importar banco');
  });
});
