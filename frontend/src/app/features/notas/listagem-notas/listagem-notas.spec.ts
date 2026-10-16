import { registerLocaleData } from '@angular/common';
import localePt from '@angular/common/locales/pt';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { describe, expect, it, vi } from 'vitest';

import { ApiService } from '../../../core/api/api.service';
import { Nota } from '../../../core/models/api.models';
import { ListagemNotas } from './listagem-notas';

registerLocaleData(localePt);

describe('notas ignoradas na listagem', () => {
  it('oferece filtro próprio e exibe a nota como Ignorada com acesso à visualização', () => {
    const nota: Nota = {
      id: 'nota', chave: '1'.repeat(44), numero: '1', serie: '1',
      estabelecimento: {
        id: 'loja', cnpj: '1', razao_social: 'Mercado', apelido: null, nome_exibicao: 'Mercado',
      },
      emissao: '2026-10-01T12:00:00', quantidade_itens: 0,
      valor_total: '0.00', desconto: '0.00', valor_a_pagar: '0.00', itens: [],
      url_origem: '', situacao: 'ignorada', importada_em: null,
      considerar_proximo_mes: false, ignorada: true,
    };
    const api = { listarNotas: vi.fn(() => of([nota])) };
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: ApiService, useValue: api }],
    });
    const fixture = TestBed.createComponent(ListagemNotas);
    fixture.detectChanges();
    expect(api.listarNotas).toHaveBeenCalledWith(undefined);
    const botoes = Array.from(fixture.nativeElement.querySelectorAll('.btn-group button')) as HTMLButtonElement[];
    const filtro = botoes.find((botao) => botao.textContent?.trim() === 'Ignoradas')!;
    filtro.click();
    fixture.detectChanges();
    expect(api.listarNotas).toHaveBeenLastCalledWith('ignorada');
    expect(filtro.classList.contains('btn-primary')).toBe(true);
    const cartao = fixture.nativeElement.querySelector('article') as HTMLElement;
    expect(cartao.querySelector('.badge.rounded-pill')?.textContent?.trim()).toBe('Ignorada');
    expect(cartao.querySelector('.badge.rounded-pill')?.classList.contains('text-bg-secondary')).toBe(true);
    expect(cartao.textContent).not.toContain('Pendentes');
    expect(cartao.textContent).toContain('Visualizar');
    expect(cartao.textContent).not.toContain('Continuar');
  });
});
