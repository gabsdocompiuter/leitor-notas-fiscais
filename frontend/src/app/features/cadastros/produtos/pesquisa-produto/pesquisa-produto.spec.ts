import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { of } from 'rxjs';
import { ApiService } from '../../../../core/api/api.service';
import { PesquisaProduto } from './pesquisa-produto';

describe('cadastro de produto na importação', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PesquisaProduto],
      providers: [
        {
          provide: ApiService,
          useValue: {
            criarCategoria: (nome: string) => of({ id: 'nova', nome }),
          },
        },
      ],
    }).compileComponents();
  });
  it('foca com o cursor no fim sem selecionar, inclusive ao retornar do cadastro', async () => {
    const fixture = TestBed.createComponent(PesquisaProduto);
    fixture.componentRef.setInput('registros', []);
    fixture.componentRef.setInput('categorias', []);
    fixture.componentRef.setInput('unidades', []);
    fixture.componentRef.setInput('buscaInicial', 'Café');
    fixture.detectChanges();
    await new Promise(resolve => setTimeout(resolve, 10));
    let campo = fixture.nativeElement.querySelector('input[type="search"]') as HTMLInputElement;
    expect(document.activeElement).toBe(campo);
    expect(campo.selectionStart).toBe(4);
    expect(campo.selectionEnd).toBe(4);
    fixture.componentInstance.abrirCadastro();
    fixture.detectChanges();
    fixture.componentInstance.voltarParaPesquisa();
    fixture.detectChanges();
    await new Promise(resolve => setTimeout(resolve, 10));
    campo = fixture.nativeElement.querySelector('input[type="search"]');
    expect(campo.value).toBe('Café');
    expect(campo.selectionStart).toBe(4);
    expect(campo.selectionEnd).toBe(4);
    campo.value = '';
    campo.dispatchEvent(new Event('input'));
    fixture.componentInstance.abrirCadastro();
    fixture.detectChanges();
    fixture.componentInstance.voltarParaPesquisa();
    fixture.detectChanges();
    await new Promise(resolve => setTimeout(resolve, 10));
    campo = fixture.nativeElement.querySelector('input[type="search"]');
    expect(campo.selectionStart).toBe(0);
    expect(campo.selectionEnd).toBe(0);
  });
  it('mantém descrição fiscal no cabeçalho e dados ao criar categoria', () => {
    const fixture = TestBed.createComponent(PesquisaProduto);
    fixture.componentRef.setInput('registros', []);
    fixture.componentRef.setInput('categorias', []);
    fixture.componentRef.setInput('unidades', [{ codigo: 'KG', descricao: 'Quilograma' }]);
    fixture.componentRef.setInput('contexto', 'CAFE PO 3 CORACOES GOURMET 250g SUL DE MINAS');
    fixture.componentRef.setInput('buscaInicial', 'Café');
    fixture.detectChanges();
    fixture.componentInstance.abrirCadastro();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.modal-header').textContent).toContain(
      'CAFE PO 3 CORACOES GOURMET 250g SUL DE MINAS',
    );
    fixture.componentInstance.formulario.controls.nome.setValue('Café gourmet');
    fixture.componentInstance.abrirPesquisaCategoria();
    fixture.detectChanges();
    const busca = fixture.nativeElement.querySelector('input[type="search"]');
    busca.value = 'Alimentação';
    busca.dispatchEvent(new Event('input'));
    fixture.nativeElement.querySelector('button[aria-label="Criar categoria"]').click();
    fixture.detectChanges();
    fixture.nativeElement
      .querySelector('form')
      .dispatchEvent(new Event('submit', { cancelable: true }));
    fixture.detectChanges();
    expect(fixture.componentInstance.formulario.controls.nome.value).toBe('Café gourmet');
    expect(fixture.componentInstance.formulario.controls.categoria_id.value).toBe('nova');
    expect(fixture.componentInstance.seletorCategoriaAberto()).toBe(false);
    expect(fixture.nativeElement.querySelector('.modal-header').textContent).toContain(
      '250g SUL DE MINAS',
    );
  });
});
