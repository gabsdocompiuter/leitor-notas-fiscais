import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Categoria,
  Estabelecimento,
  Leitura,
  Marca,
  Nota,
  Produto,
  ProdutoRequest,
  RevisaoItem,
  SituacaoNota,
  UnidadeMedidaInfo,
  VariacaoProduto,
  VariacaoProdutoRequest,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api';

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

  listarCategorias(busca?: string): Observable<Categoria[]> {
    const params = busca ? new HttpParams().set('busca', busca) : undefined;
    return this.http.get<Categoria[]>(`${this.baseUrl}/categorias`, { params });
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
    return this.http.post<VariacaoProduto>(`${this.baseUrl}/produtos/${produtoId}/variacoes`, valor);
  }

  atualizarVariacao(
    _produtoId: string,
    variacaoId: string,
    valor: VariacaoProdutoRequest,
  ): Observable<VariacaoProduto> {
    return this.http.patch<VariacaoProduto>(
      `${this.baseUrl}/variacoes/${variacaoId}`,
      valor,
    );
  }

  listarEstabelecimentos(busca?: string): Observable<Estabelecimento[]> {
    const params = busca ? new HttpParams().set('busca', busca) : undefined;
    return this.http.get<Estabelecimento[]>(`${this.baseUrl}/estabelecimentos`, { params });
  }

  atualizarEstabelecimento(id: string, apelido: string | null): Observable<Estabelecimento> {
    return this.http.patch<Estabelecimento>(`${this.baseUrl}/estabelecimentos/${id}`, { apelido });
  }
}
