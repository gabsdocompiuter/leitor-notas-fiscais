import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { ApiService } from '../../../../core/api/api.service';
import { Marca } from '../../../../core/models/api.models';
import { PesquisaMarca } from './pesquisa-marca';

describe('PesquisaMarca', () => {
  const marcas: Marca[] = [
    { id: '1', nome: 'Marca Alfa' },
    { id: '2', nome: 'Marca Beta' },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PesquisaMarca],
      providers: [{ provide: ApiService, useValue: {} }],
    }).compileComponents();
  });

  it('filtra os resultados enquanto o usuário digita', () => {
    const fixture = TestBed.createComponent(PesquisaMarca);
    fixture.componentRef.setInput('registros', marcas);
    fixture.detectChanges();

    const pesquisa = fixture.nativeElement.querySelector(
      'input[type="search"]',
    ) as HTMLInputElement;
    pesquisa.value = 'Beta';
    pesquisa.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const resultados = fixture.nativeElement.querySelectorAll('.list-group-item');
    expect(resultados).toHaveLength(1);
    expect(resultados[0].textContent).toContain('Marca Beta');
  });

  it('abre o cadastro em um segundo modal e reaproveita o conteúdo pesquisado', () => {
    const fixture = TestBed.createComponent(PesquisaMarca);
    fixture.componentRef.setInput('registros', marcas);
    fixture.detectChanges();

    const pesquisa = fixture.nativeElement.querySelector(
      'input[type="search"]',
    ) as HTMLInputElement;
    pesquisa.value = 'Marca Nova';
    pesquisa.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const criar = fixture.nativeElement.querySelector(
      'button[aria-label="Criar marca"]',
    ) as HTMLButtonElement;
    criar.click();
    fixture.detectChanges();

    const nome = fixture.nativeElement.querySelector('#nome-nova-marca') as HTMLInputElement;
    expect(fixture.nativeElement.textContent).toContain('Nova marca');
    expect(nome.value).toBe('Marca Nova');
  });
});
