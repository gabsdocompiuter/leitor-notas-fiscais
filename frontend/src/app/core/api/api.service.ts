import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  ConfiguracaoBanco,
  ImportacaoBancoResponse,
  Categoria,
  Tag,
  RelatorioMensal,
  ItensRelatorio,
  Estabelecimento,
  Leitura,
  Marca,
  Nota,
  Produto,
  ProdutoRequest,
  RestricoesProduto,
  RevisaoItem,
  SituacaoNota,
  UnidadeMedidaInfo,
  VariacaoProduto,
  VariacaoProdutoRequest,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  obterConfiguracaoBanco(): Observable<ConfiguracaoBanco> {
    return this.http.get<ConfiguracaoBanco>(`${this.baseUrl}/banco/configuracao`);
  }

  exportarBanco(): Observable<HttpResponse<Blob>> {
    return this.http.get(`${this.baseUrl}/banco/exportacao`, {
      responseType: 'blob',
      observe: 'response',
    });
  }

  importarBanco(arquivo: File): Observable<ImportacaoBancoResponse> {
    const formulario = new FormData();
    formulario.append('arquivo', arquivo);
    return this.http.post<ImportacaoBancoResponse>(`${this.baseUrl}/banco/importacao`, formulario);
  }

  listarNotas(situacao?: SituacaoNota): Observable<Nota[]> {
    const params = situacao ? new HttpParams().set('situacao', situacao) : undefined;
    return this.http.get<Nota[]>(`${this.baseUrl}/notas`, { params });
  }

  obterNota(chave: string): Observable<Nota> {
    return this.http.get<Nota>(`${this.baseUrl}/notas/${chave}`);
  }

  criarLeitura(url: string): Observable<Leitura> {
    return this.http.post<Leitura>(`${this.baseUrl}/leituras`, { url });
  }

  revisarItem(chave: string, itemId: string, revisao: RevisaoItem): Observable<Nota> {
    return this.http.patch<Nota>(`${this.baseUrl}/notas/${chave}/itens/${itemId}`, revisao);
  }

  concluirImportacao(chave: string): Observable<Nota> {
    return this.http.post<Nota>(`${this.baseUrl}/notas/${chave}/importacao`, {});
  }

  listarTags(busca?: string): Observable<Tag[]> {
    const params = busca ? new HttpParams().set('busca', busca) : undefined;
    return this.http.get<Tag[]>(`${this.baseUrl}/tags`, { params });
  }

  criarTag(nome: string): Observable<Tag> {
    return this.http.post<Tag>(`${this.baseUrl}/tags`, { nome });
  }

  definirTagsItem(chave: string, itemId: string, tagIds: string[]): Observable<Nota> {
    return this.http.put<Nota>(`${this.baseUrl}/notas/${chave}/itens/${itemId}/tags`, {
      tag_ids: tagIds,
    });
  }

  adicionarTagsEmTodos(chave: string, tagIds: string[]): Observable<Nota> {
    return this.http.post<Nota>(`${this.baseUrl}/notas/${chave}/itens/tags`, {
      tag_ids: tagIds,
    });
  }

  definirCompetencia(chave: string, considerarProximoMes: boolean): Observable<Nota> {
    return this.http.patch<Nota>(`${this.baseUrl}/notas/${chave}`, {
      considerar_proximo_mes: considerarProximoMes,
    });
  }

  obterRelatorioMensal(mes: string): Observable<RelatorioMensal> {
    return this.http.get<RelatorioMensal>(`${this.baseUrl}/relatorios/mensal`, {
      params: { mes },
    });
  }

  listarItensRelatorio(
    mes: string,
    categoriaId?: string,
    tagId?: string,
    deslocamento = 0,
  ): Observable<ItensRelatorio> {
    let params = new HttpParams().set('mes', mes).set('deslocamento', deslocamento);
    if (categoriaId) params = params.set('categoria_id', categoriaId);
    if (tagId) params = params.set('tag_id', tagId);
    return this.http.get<ItensRelatorio>(`${this.baseUrl}/relatorios/mensal/itens`, { params });
  }

  listarCategorias(busca?: string): Observable<Categoria[]> {
    const params = busca ? new HttpParams().set('busca', busca) : undefined;
    return this.http.get<Categoria[]>(`${this.baseUrl}/categorias`, { params });
  }

  obterCategoria(id: string): Observable<Categoria> {
    return this.http.get<Categoria>(`${this.baseUrl}/categorias/${id}`);
  }

  criarCategoria(nome: string): Observable<Categoria> {
    return this.http.post<Categoria>(`${this.baseUrl}/categorias`, { nome });
  }

  atualizarCategoria(id: string, nome: string): Observable<Categoria> {
    return this.http.patch<Categoria>(`${this.baseUrl}/categorias/${id}`, { nome });
  }

  listarMarcas(busca?: string): Observable<Marca[]> {
    const params = busca ? new HttpParams().set('busca', busca) : undefined;
    return this.http.get<Marca[]>(`${this.baseUrl}/marcas`, { params });
  }

  obterMarca(id: string): Observable<Marca> {
    return this.http.get<Marca>(`${this.baseUrl}/marcas/${id}`);
  }

  criarMarca(nome: string): Observable<Marca> {
    return this.http.post<Marca>(`${this.baseUrl}/marcas`, { nome });
  }

  atualizarMarca(id: string, nome: string): Observable<Marca> {
    return this.http.patch<Marca>(`${this.baseUrl}/marcas/${id}`, { nome });
  }

  listarProdutos(busca?: string): Observable<Produto[]> {
    const params = busca ? new HttpParams().set('busca', busca) : undefined;
    return this.http.get<Produto[]>(`${this.baseUrl}/produtos`, { params });
  }

  obterProduto(id: string): Observable<Produto> {
    return this.http.get<Produto>(`${this.baseUrl}/produtos/${id}`);
  }

  obterRestricoesProduto(id: string): Observable<RestricoesProduto> {
    return this.http.get<RestricoesProduto>(`${this.baseUrl}/produtos/${id}/restricoes`);
  }

  excluirProduto(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/produtos/${id}`);
  }

  criarProduto(produto: ProdutoRequest): Observable<Produto> {
    return this.http.post<Produto>(`${this.baseUrl}/produtos`, produto);
  }

  atualizarProduto(id: string, produto: ProdutoRequest): Observable<Produto> {
    return this.http.patch<Produto>(`${this.baseUrl}/produtos/${id}`, produto);
  }

  listarUnidadesMedida(): Observable<UnidadeMedidaInfo[]> {
    return this.http.get<UnidadeMedidaInfo[]>(`${this.baseUrl}/unidades-medida`);
  }

  listarVariacoes(produtoId: string): Observable<VariacaoProduto[]> {
    return this.http.get<VariacaoProduto[]>(`${this.baseUrl}/produtos/${produtoId}/variacoes`);
  }

  criarVariacao(produtoId: string, valor: VariacaoProdutoRequest): Observable<VariacaoProduto> {
    return this.http.post<VariacaoProduto>(
      `${this.baseUrl}/produtos/${produtoId}/variacoes`,
      valor,
    );
  }

  atualizarVariacao(
    _produtoId: string,
    variacaoId: string,
    valor: VariacaoProdutoRequest,
  ): Observable<VariacaoProduto> {
    return this.http.patch<VariacaoProduto>(`${this.baseUrl}/variacoes/${variacaoId}`, valor);
  }

  listarEstabelecimentos(busca?: string): Observable<Estabelecimento[]> {
    const params = busca ? new HttpParams().set('busca', busca) : undefined;
    return this.http.get<Estabelecimento[]>(`${this.baseUrl}/estabelecimentos`, { params });
  }

  obterEstabelecimento(id: string): Observable<Estabelecimento> {
    return this.http.get<Estabelecimento>(`${this.baseUrl}/estabelecimentos/${id}`);
  }

  atualizarEstabelecimento(id: string, apelido: string | null): Observable<Estabelecimento> {
    return this.http.patch<Estabelecimento>(`${this.baseUrl}/estabelecimentos/${id}`, { apelido });
  }
}
