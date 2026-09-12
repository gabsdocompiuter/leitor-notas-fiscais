export type SituacaoNota = 'lida' | 'em_revisao' | 'importada';
export type UnidadeMedida = 'UN' | 'KG' | 'G' | 'L' | 'ML';

export interface ErroApi {
  codigo: string;
  mensagem: string;
}

export interface Categoria {
  id: string;
  nome: string;
}

export interface Marca {
  id: string;
  nome: string;
}

export interface Produto {
  id: string;
  nome: string;
  categoria: Categoria;
  unidade_base: UnidadeMedida;
}

export interface ApresentacaoProduto {
  id: string;
  produto: Produto;
  marca: Marca | null;
  conteudo_embalagem: string | null;
  unidade_embalagem: UnidadeMedida | null;
  marca_confirmada: boolean;
}

export interface ItemNota {
  id: string;
  numero: number;
  codigo: string;
  descricao_original: string;
  quantidade: string;
  unidade_original: string;
  valor_unitario: string;
  valor_total: string;
  alertas: string[];
  apresentacao: ApresentacaoProduto | null;
  unidade_corrigida: UnidadeMedida | null;
  quantidade_normalizada: string | null;
  revisado: boolean;
}

export interface Estabelecimento {
  id: string;
  cnpj: string;
  razao_social: string;
  apelido: string | null;
  nome_exibicao: string;
}

export interface Nota {
  id: string;
  chave: string;
  numero: string;
  serie: string;
  estabelecimento: Estabelecimento;
  emissao: string;
  quantidade_itens: number;
  valor_total: string;
  desconto: string;
  valor_a_pagar: string;
  itens: ItemNota[];
  url_origem: string;
  situacao: SituacaoNota;
  importada_em: string | null;
}

export interface Leitura {
  id: string;
  url: string;
  nota: Nota | null;
  erro_consulta: string | null;
  criada_em: string;
}

export interface RevisaoItem {
  produto_id: string;
  marca_id: string | null;
  marca_confirmada: boolean;
  conteudo_embalagem: number | null;
  unidade_embalagem: UnidadeMedida | null;
  unidade_corrigida: UnidadeMedida;
  quantidade_normalizada: number;
}

export interface ProdutoRequest {
  nome: string;
  categoria_id: string;
  unidade_base: UnidadeMedida;
}
