import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Categoria,
  Leitura,
  Marca,
  Nota,
  Produto,
  ProdutoRequest,
  RevisaoItem,
  SituacaoNota,
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

  listarCategorias(): Observable<Categoria[]> {
    return this.http.get<Categoria[]>(`${this.baseUrl}/categorias`);
  }

  criarCategoria(nome: string): Observable<Categoria> {
    return this.http.post<Categoria>(`${this.baseUrl}/categorias`, { nome });
  }

  listarMarcas(): Observable<Marca[]> {
    return this.http.get<Marca[]>(`${this.baseUrl}/marcas`);
  }

  criarMarca(nome: string): Observable<Marca> {
    return this.http.post<Marca>(`${this.baseUrl}/marcas`, { nome });
  }

  listarProdutos(): Observable<Produto[]> {
    return this.http.get<Produto[]>(`${this.baseUrl}/produtos`);
  }

  criarProduto(produto: ProdutoRequest): Observable<Produto> {
    return this.http.post<Produto>(`${this.baseUrl}/produtos`, produto);
  }
}
