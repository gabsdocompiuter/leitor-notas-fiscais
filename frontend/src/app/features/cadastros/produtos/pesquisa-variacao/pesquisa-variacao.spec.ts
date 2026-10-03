import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Subject, of } from 'rxjs';
import { ApiService } from '../../../../core/api/api.service';
import { Produto, UnidadeMedida, VariacaoProduto } from '../../../../core/models/api.models';
import { PesquisaVariacao } from './pesquisa-variacao';

const produto: Produto = {
  id: 'p',
  nome: 'Café',
  categoria: { id: 'c', nome: 'Alimentação' },
  nao_solicitar_marca: false,
  tratar_apenas_como_unidades: false,
  contem_variacoes: true,
  unidade_medida: 'G',
};
const variacoes: VariacaoProduto[] = [
  { id: '1', produto_id: 'p', quantidade: '25.000', unidade_medida: 'G', nome_exibicao: '25 G' },
  { id: '2', produto_id: 'p', quantidade: '250', unidade_medida: 'G', nome_exibicao: '250 G' },
  { id: '3', produto_id: 'p', quantidade: '2500', unidade_medida: 'ML', nome_exibicao: '2500 ML' },
  { id: '4', produto_id: 'p', quantidade: '1.500', unidade_medida: 'L', nome_exibicao: '1,5 L' },
];

describe('PesquisaVariacao', () => {
  const criarVariacao = vi.fn();
  beforeEach(async () => {
    criarVariacao.mockReset();
    await TestBed.configureTestingModule({
      imports: [PesquisaVariacao],
      providers: [{ provide: ApiService, useValue: { criarVariacao } }],
    }).compileComponents();
  });
  function montar(contexto = '') {
    const fixture = TestBed.createComponent(PesquisaVariacao);
    fixture.componentRef.setInput('registros', variacoes);
    fixture.componentRef.setInput('contexto', contexto);
    fixture.componentRef.setInput('produto', produto);
    fixture.componentRef.setInput(
      'unidades',
      ['G', 'KG', 'ML', 'L'].map((codigo) => ({
        codigo: codigo as UnidadeMedida,
        descricao: codigo,
      })),
    );
    fixture.detectChanges();
    return fixture;
  }
  it('extrai o filtro fiscal e reage ao carregamento sem sobrescrever edição', async () => {
    const fixture = montar('CAFE 3 CORACOES 250g');
    expect(fixture.componentInstance.quantidade()).toBe('250');
    expect(fixture.componentInstance.unidade()).toBe('G');
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('select').value).toBe('G');
    expect(fixture.componentInstance.resultados().map((v) => v.id)).toEqual(['2']);
    fixture.componentRef.setInput('registros', []);
    fixture.componentInstance.quantidade.set('25');
    fixture.componentRef.setInput('registros', variacoes);
    fixture.detectChanges();
    expect(fixture.componentInstance.quantidade()).toBe('25');
    expect(fixture.componentInstance.resultados().map((v) => v.id)).toEqual(['1', '2']);
  });
  it('deixa filtros vazios com medidas diferentes', () => {
    const fixture = montar('KIT 500ml + 200ml');
    expect(fixture.componentInstance.quantidade()).toBe('');
    expect(fixture.componentInstance.unidade()).toBe('');
    expect(fixture.componentInstance.resultados()).toHaveLength(4);
  });
  it('filtra por prefixo, por unidade e pela combinação com os dois campos opcionais', () => {
    const fixture = montar();
    const quantidade = fixture.nativeElement.querySelector('input');
    const unidade = fixture.nativeElement.querySelector('select');
    quantidade.value = '25';
    quantidade.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(fixture.componentInstance.resultados().map((v) => v.id)).toEqual(['1', '2', '3']);
    unidade.value = 'G';
    unidade.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    expect(fixture.componentInstance.resultados().map((v) => v.id)).toEqual(['1', '2']);
    quantidade.value = '';
    quantidade.dispatchEvent(new Event('input'));
    expect(fixture.componentInstance.resultados().map((v) => v.id)).toEqual(['1', '2']);
    fixture.componentInstance.quantidade.set('1,5');
    fixture.componentInstance.unidade.set('');
    expect(fixture.componentInstance.resultados().map((v) => v.id)).toEqual(['4']);
  });
  it('habilita + somente com quantidade válida e unidade', () => {
    const fixture = montar();
    const componente = fixture.componentInstance;
    expect(componente.podeCriar()).toBe(false);
    componente.quantidade.set('25');
    expect(componente.podeCriar()).toBe(false);
    componente.unidade.set('G');
    expect(componente.podeCriar()).toBe(true);
    for (const valor of ['0', '-1', 'abc', '0,0000001', 'Infinity']) {
      componente.quantidade.set(valor);
      expect(componente.podeCriar()).toBe(false);
    }
    componente.quantidade.set('0,001');
    expect(componente.podeCriar()).toBe(true);
  });
  it('confirma, cancela preservando filtros e cria os valores informados', () => {
    const fixture = montar('LEITE 1,5 L');
    fixture.nativeElement.querySelector('button[aria-label="Criar variação"]').click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain(
      'Deseja criar a variação “1,5 L” para “Café”?',
    );
    expect(criarVariacao).not.toHaveBeenCalled();
    fixture.componentInstance.voltarParaPesquisa();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('input').value).toBe('1,5');
    const selecionado = vi.fn();
    const atualizado = vi.fn();
    fixture.componentInstance.registroSelecionado.subscribe(selecionado);
    fixture.componentInstance.cadastroCriado.subscribe(atualizado);
    criarVariacao.mockReturnValue(of(variacoes[3]));
    fixture.componentInstance.abrirCadastro();
    fixture.detectChanges();
    fixture.nativeElement.querySelector('.modal-footer .btn-primary').click();
    expect(criarVariacao).toHaveBeenCalledWith('p', { quantidade: 1.5, unidade_medida: 'L' });
    expect(selecionado).toHaveBeenCalledWith(variacoes[3]);
    expect(atualizado).toHaveBeenCalledWith(variacoes[3]);
  });
  it('bloqueia duplo envio e preserva valores após erro', () => {
    const fixture = montar('CAFE 250 G');
    const pendente = new Subject<VariacaoProduto>();
    criarVariacao.mockReturnValue(pendente);
    fixture.componentInstance.abrirCadastro();
    fixture.componentInstance.criar();
    fixture.componentInstance.criar();
    fixture.componentInstance.solicitarFechamento();
    expect(criarVariacao).toHaveBeenCalledTimes(1);
    pendente.error(new Error('Falha'));
    expect(fixture.componentInstance.erro()).toBeTruthy();
    expect(fixture.componentInstance.quantidade()).toBe('250');
    expect(fixture.componentInstance.unidade()).toBe('G');
    expect(fixture.componentInstance.salvando()).toBe(false);
    expect(fixture.componentInstance.cadastroAberto()).toBe(true);
  });
});
