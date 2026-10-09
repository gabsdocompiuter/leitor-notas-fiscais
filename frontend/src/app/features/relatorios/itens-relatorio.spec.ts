import { registerLocaleData } from '@angular/common';
import pt from '@angular/common/locales/pt';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { describe, expect, it } from 'vitest';
import { ItensRelatorioLista } from './itens-relatorio';
import { AgrupadorRelatorio, ItemRelatorio } from '../../core/models/api.models';

registerLocaleData(pt);
describe('Detalhes contextuais das compras', () => {
  const item: ItemRelatorio = {
    id: 'item',
    produto: 'Queijo Mussarela',
    produto_id: 'produto',
    categoria: 'Alimentação',
    categoria_id: 'categoria',
    estabelecimento: 'Macromix',
    marca: 'Mandaka',
    variacao: '400 G',
    quantidade_unidades: '2',
    quantidade_comprada: '0.8',
    unidade_quantidade: 'KG',
    emissao: '2026-10-05',
    valor_pago: '31.51',
    valor_bruto: '31.8',
    desconto_rateado: '0.29',
    tags: [{ id: 'tag', nome: 'Casa' }],
    considerar_proximo_mes: true,
    chave_nota: 'chave',
    numero_nota: '235852',
  };
  function criar(agrupador: AgrupadorRelatorio, compra = item, compacto = true) {
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
    const fixture = TestBed.createComponent(ItensRelatorioLista);
    fixture.componentRef.setInput('pagina', { total: 1, itens: [compra] });
    fixture.componentRef.setInput('compacto', compacto);
    fixture.componentRef.setInput('agrupador', agrupador);
    fixture.detectChanges();
    return fixture;
  }
  for (const agrupador of ['marca', 'estabelecimento', 'variacao'] as const) {
    it(`complementa a visão por ${agrupador} sem repetir o atributo do grupo`, () => {
      const fixture = criar(agrupador);
      const texto = fixture.nativeElement.textContent;
      expect(texto).toContain('2 unidades ·');
      expect(texto).toContain('0,8 kg');
      for (const [atributo, valor] of [
        ['marca', 'Mandaka'],
        ['estabelecimento', 'Macromix'],
        ['variacao', '400 G'],
      ]) {
        if (atributo === agrupador) expect(texto).not.toContain(valor);
        else expect(texto).toContain(valor);
      }
      for (const valor of ['05/10/2026', 'Casa', 'mês seguinte', 'Ver nota 235852'])
        expect(texto).toContain(valor);
      for (const valor of ['Queijo Mussarela', 'Alimentação', 'Bruto', 'Desconto'])
        expect(texto).not.toContain(valor);
      expect(fixture.nativeElement.querySelector('a').getAttribute('href')).toBe(
        '/notas/chave/revisao',
      );
    });
  }
  it('mostra atributos ausentes e evita repetir a quantidade para produtos por unidades', () => {
    const fixture = criar('estabelecimento', {
      ...item,
      marca: null,
      variacao: null,
      unidade_quantidade: 'UN',
      quantidade_comprada: '2',
    });
    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('Sem marca');
    expect(texto).toContain('Sem variação');
    expect(texto.match(/2 unidades/g)).toHaveLength(1);
  });
  it('preserva a apresentação completa de Por tag', () => {
    const fixture = criar('marca', item, false);
    const texto = fixture.nativeElement.textContent;
    for (const valor of ['Queijo Mussarela', 'Alimentação', 'Macromix', 'Bruto', 'Desconto'])
      expect(texto).toContain(valor);
    expect(texto).not.toContain('Marca:');
    expect(texto).not.toContain('Variação:');
  });
});
