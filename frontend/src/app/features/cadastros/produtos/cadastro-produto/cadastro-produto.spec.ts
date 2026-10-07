import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, provideRouter } from '@angular/router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { CadastroProduto } from './cadastro-produto';
import { RestricoesProduto } from '../../../../core/models/api.models';

const produto = {
  id: 'produto',
  nome: 'Café',
  categoria: { id: 'categoria', nome: 'Alimentos' },
  nao_solicitar_marca: true,
  tratar_apenas_como_unidades: false,
  contem_variacoes: false,
  unidade_medida: 'KG',
};
const livre = {
  pode_alterar_estrutura: true,
  pode_excluir: true,
  motivo_alteracao_estrutura: null,
  motivo_exclusao: null,
};
const bloqueado = {
  pode_alterar_estrutura: false,
  pode_excluir: false,
  motivo_alteracao_estrutura: 'O produto possui itens em notas.',
  motivo_exclusao: 'O produto está em uso.',
};

async function criar(restricoes: RestricoesProduto = livre, id: string | null = 'produto') {
  TestBed.configureTestingModule({
    imports: [CadastroProduto],
    providers: [
      provideRouter([]),
      provideHttpClient(),
      provideHttpClientTesting(),
      { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => id } } } },
    ],
  });
  const fixture = TestBed.createComponent(CadastroProduto);
  const http = TestBed.inject(HttpTestingController);
  const navegar = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
  fixture.detectChanges();
  if (id) {
    http.expectOne((r) => r.url.endsWith('/produtos/produto')).flush(produto);
    http.expectOne((r) => r.url.endsWith('/produtos/produto/restricoes')).flush(restricoes);
  }
  http.expectOne((r) => r.url.endsWith('/categorias')).flush([produto.categoria]);
  http
    .expectOne((r) => r.url.endsWith('/unidades-medida'))
    .flush([
      { codigo: 'KG', descricao: 'Quilograma' },
      { codigo: 'G', descricao: 'Grama' },
    ]);
  fixture.detectChanges();
  await fixture.whenStable();
  fixture.detectChanges();
  return { fixture, componente: fixture.componentInstance, http, navegar };
}

afterEach(() => {
  TestBed.inject(HttpTestingController).verify();
  vi.restoreAllMocks();
});

describe('edição e exclusão de produtos', () => {
  it('bloqueia somente a estrutura e mantém nome, categoria e marca editáveis', async () => {
    const { fixture, componente, http, navegar } = await criar(bloqueado);
    for (const id of ['tratar-unidades', 'unidade-medida', 'contem-variacoes']) {
      expect(fixture.nativeElement.querySelector(`#${id}`).disabled).toBe(true);
    }
    for (const id of ['nome-produto', 'categoria-produto', 'nao-solicitar-marca']) {
      expect(fixture.nativeElement.querySelector(`#${id}`).disabled).toBe(false);
    }
    expect(fixture.nativeElement.textContent).toContain(bloqueado.motivo_alteracao_estrutura);
    componente.modelo.nome = 'Café corrigido';
    componente.modelo.nao_solicitar_marca = false;
    componente.salvarProduto();
    const envio = http.expectOne((r) => r.method === 'PATCH');
    expect(envio.request.body).toMatchObject({
      nome: 'Café corrigido',
      nao_solicitar_marca: false,
      unidade_medida: 'KG',
    });
    envio.flush(produto);
    expect(navegar).toHaveBeenCalledWith('/cadastros/produtos');
  });

  it('deixa a estrutura livre para produto sem uso e para novo cadastro', async () => {
    const { fixture } = await criar();
    expect(fixture.nativeElement.querySelector('#unidade-medida').disabled).toBe(false);
    TestBed.resetTestingModule();
    const novo = await criar(livre, null);
    expect(novo.fixture.nativeElement.querySelector('#tratar-unidades').disabled).toBe(false);
    expect(novo.fixture.nativeElement.textContent).not.toContain('Excluir produto');
  });

  it('cancela a exclusão sem enviar requisição', async () => {
    const { componente, http } = await criar();
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(false);
    componente.excluirProduto();
    expect(confirmar.mock.calls[0][0]).toContain('variações, apresentações');
    expect(confirmar.mock.calls[0][0]).toContain('associações de classificação automática');
    http.expectNone((r) => r.method === 'DELETE');
    expect(componente.excluindo()).toBe(false);
  });

  it('exclui após confirmação, impede repetição e retorna à listagem', async () => {
    const { componente, http, navegar } = await criar();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    componente.excluirProduto();
    componente.excluirProduto();
    const envio = http.expectOne(
      (r) => r.method === 'DELETE' && r.url.endsWith('/produtos/produto'),
    );
    expect(componente.excluindo()).toBe(true);
    envio.flush(null, { status: 204, statusText: 'No Content' });
    expect(navegar).toHaveBeenCalledWith('/cadastros/produtos');
  });

  it('atualiza restrições e exibe o motivo quando a exclusão entra em conflito', async () => {
    const { fixture, componente, http, navegar } = await criar();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    componente.excluirProduto();
    http
      .expectOne((r) => r.method === 'DELETE')
      .flush(
        { mensagem: 'Produto passou a ser utilizado.' },
        { status: 409, statusText: 'Conflict' },
      );
    http.expectOne((r) => r.url.endsWith('/restricoes')).flush(bloqueado);
    http.expectOne((r) => r.url.endsWith('/produtos/produto')).flush(produto);
    fixture.detectChanges();
    expect(componente.erro()).toBe('Produto passou a ser utilizado.');
    expect(componente.excluindo()).toBe(false);
    expect(navegar).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('.btn-outline-danger').disabled).toBe(true);
    expect(fixture.nativeElement.textContent).toContain(bloqueado.motivo_exclusao);
  });

  it('reavalia restrições depois de conflito ao salvar, preservando a edição', async () => {
    const { componente, http } = await criar();
    componente.modelo.nome = 'Correção em andamento';
    componente.modelo.unidade_medida = 'G';
    componente.salvarProduto();
    http
      .expectOne((r) => r.method === 'PATCH')
      .flush({ mensagem: 'Estrutura bloqueada.' }, { status: 409, statusText: 'Conflict' });
    http.expectOne((r) => r.url.endsWith('/restricoes')).flush(bloqueado);
    http.expectOne((r) => r.url.endsWith('/produtos/produto')).flush(produto);
    expect(componente.estruturaBloqueada()).toBe(true);
    expect(componente.modelo.nome).toBe('Correção em andamento');
    expect(componente.modelo.unidade_medida).toBe('KG');
    expect(componente.salvando()).toBe(false);
  });
});
