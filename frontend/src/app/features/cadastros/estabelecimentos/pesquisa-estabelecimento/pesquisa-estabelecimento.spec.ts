import { TestBed } from '@angular/core/testing';
import { of, Subject } from 'rxjs';
import { describe, expect, it, vi } from 'vitest';

import { ApiService } from '../../../../core/api/api.service';
import { Estabelecimento } from '../../../../core/models/api.models';
import { PesquisaEstabelecimento } from './pesquisa-estabelecimento';

describe('pesquisa de estabelecimento', () => {
  const loja: Estabelecimento = {
    id: 'loja',
    apelido: 'Feira',
    nome_exibicao: 'Feira',
    cnpj: null,
    razao_social: null,
  };
  function criar() {
    const resposta = new Subject<Estabelecimento>();
    const api = { criarEstabelecimento: vi.fn((_apelido: string) => resposta) };
    TestBed.configureTestingModule({ providers: [{ provide: ApiService, useValue: api }] });
    const fixture = TestBed.createComponent(PesquisaEstabelecimento);
    fixture.componentRef.setInput('registros', [loja]);
    fixture.detectChanges();
    return { fixture, componente: fixture.componentInstance, api, resposta };
  }

  it('encontra estabelecimentos sem dados fiscais e permite selecionar', () => {
    const { componente } = criar();
    componente.busca.set('feira');
    expect(componente.resultados()).toEqual([loja]);
    const selecionar = vi.fn();
    componente.registroSelecionado.subscribe(selecionar);
    componente.selecionar(loja);
    expect(selecionar).toHaveBeenCalledWith(loja);
  });

  it('cria somente com apelido e bloqueia duplicação durante o envio', () => {
    const { componente, api, resposta } = criar();
    componente.abrirCadastro();
    componente.formulario.controls.apelido.setValue('   ');
    componente.criar();
    expect(api.criarEstabelecimento).not.toHaveBeenCalled();
    componente.formulario.controls.apelido.setValue(' Feira ');
    const selecionar = vi.fn();
    componente.registroSelecionado.subscribe(selecionar);
    componente.criar();
    componente.criar();
    expect(api.criarEstabelecimento).toHaveBeenCalledExactlyOnceWith('Feira');
    resposta.next(loja);
    expect(selecionar).toHaveBeenCalledWith(loja);
  });
});
