import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Subject, of, throwError } from 'rxjs';
import { ApiService } from '../../../../core/api/api.service';
import { PesquisaMarca } from './pesquisa-marca';
import { PesquisaCategoria } from '../../categorias/pesquisa-categoria/pesquisa-categoria';

for (const [componente, tipo, metodo] of [
  [PesquisaMarca, 'marca', 'criarMarca'],
  [PesquisaCategoria, 'categoria', 'criarCategoria'],
] as const) {
  describe(`Confirmação de ${tipo}`, () => {
    const registros = [
      { id: '1', nome: 'Nome Alfa' },
      { id: '2', nome: 'Nome Beta' },
    ];
    const criar = vi.fn();
    beforeEach(async () => {
      criar.mockReset();
      await TestBed.configureTestingModule({
        imports: [componente],
        providers: [{ provide: ApiService, useValue: { [metodo]: criar } }],
      }).compileComponents();
    });
    function montar(busca = 'Nome Novo') {
      const fixture = TestBed.createComponent(componente as typeof PesquisaMarca);
      fixture.componentRef.setInput('registros', registros);
      fixture.componentRef.setInput('buscaInicial', busca);
      fixture.detectChanges();
      return fixture;
    }
    it('filtra enquanto digita', () => {
      const fixture = montar('Beta');
      expect(fixture.nativeElement.querySelectorAll('.list-group-item')).toHaveLength(1);
      expect(fixture.nativeElement.textContent).toContain('Nome Beta');
    });
    it('confirma sem campo adicional e cancela preservando a pesquisa', () => {
      const fixture = montar();
      fixture.nativeElement.querySelector(`button[aria-label="Criar ${tipo}"]`).click();
      fixture.detectChanges();
      expect(fixture.nativeElement.textContent).toContain(`Deseja criar a ${tipo} “Nome Novo”?`);
      expect(fixture.nativeElement.querySelectorAll('.modal')).toHaveLength(1);
      expect(fixture.nativeElement.querySelector('input')).toBeNull();
      expect(criar).not.toHaveBeenCalled();
      fixture.componentInstance.voltarParaPesquisa();
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('input').value).toBe('Nome Novo');
    });
    it('não confirma nome vazio ou acima do limite', () => {
      const fixture = montar('   ');
      fixture.componentInstance.abrirCadastro();
      expect(fixture.componentInstance.cadastroAberto()).toBe(false);
      fixture.componentInstance.busca.set('x'.repeat(101));
      fixture.componentInstance.abrirCadastro();
      expect(fixture.componentInstance.cadastroAberto()).toBe(false);
      expect(criar).not.toHaveBeenCalled();
    });
    it('cria, atualiza e seleciona somente após confirmação', () => {
      const fixture = montar('  Nome Novo  ');
      const registro = { id: '3', nome: 'Nome Novo' };
      criar.mockReturnValue(of(registro));
      const atualizado = vi.fn();
      const selecionado = vi.fn();
      fixture.componentInstance.cadastroCriado.subscribe(atualizado);
      fixture.componentInstance.registroSelecionado.subscribe(selecionado);
      fixture.componentInstance.abrirCadastro();
      expect(criar).not.toHaveBeenCalled();
      fixture.detectChanges();
      fixture.nativeElement
        .querySelector('form')
        .dispatchEvent(new Event('submit', { cancelable: true }));
      expect(criar).toHaveBeenCalledWith('Nome Novo');
      expect(atualizado).toHaveBeenCalledWith(registro);
      expect(selecionado).toHaveBeenCalledWith(registro);
    });
    it('bloqueia duplo envio e mantém confirmação após erro', () => {
      const fixture = montar();
      const pendente = new Subject();
      criar.mockReturnValue(pendente);
      fixture.componentInstance.abrirCadastro();
      fixture.componentInstance.criar();
      fixture.componentInstance.criar();
      fixture.componentInstance.voltarParaPesquisa();
      expect(criar).toHaveBeenCalledTimes(1);
      expect(fixture.componentInstance.cadastroAberto()).toBe(true);
      pendente.error(new Error('Falha'));
      expect(fixture.componentInstance.salvando()).toBe(false);
      expect(fixture.componentInstance.erro()).toBeTruthy();
      expect(fixture.componentInstance.formulario.controls.nome.value).toBe('Nome Novo');
      criar.mockReturnValue(throwError(() => new Error('Falha')));
      fixture.componentInstance.criar();
      expect(criar).toHaveBeenCalledTimes(2);
    });
  });
}
