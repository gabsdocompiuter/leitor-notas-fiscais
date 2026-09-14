export type SituacaoNota = 'lida' | 'em_revisao' | 'importada';
export type UnidadeMedida = 'KG' | 'G' | 'L' | 'ML';

export interface ErroApi { codigo: string; mensagem: string; }
export interface Categoria { id: string; nome: string; }
export interface Marca { id: string; nome: string; }
export interface UnidadeMedidaInfo { codigo: UnidadeMedida; descricao: string; }

export interface Produto {
  id: string;
  nome: string;
  categoria: Categoria;
  nao_solicitar_marca: boolean;
  tratar_apenas_como_unidades: boolean;
  contem_variacoes: boolean;
  unidade_medida: UnidadeMedida | null;
}

export interface VariacaoProduto {
  id: string;
  produto_id: string;
  quantidade: string;
  unidade_medida: UnidadeMedida;
  descricao: string | null;
  nome_exibicao: string;
}

export interface ApresentacaoProduto { id: string; produto: Produto; marca: Marca | null; }

export interface ItemNota {
  id: string; numero: number; codigo: string; descricao_original: string;
  quantidade: string; unidade_original: string; valor_unitario: string;
  valor_total: string; alertas: string[]; apresentacao: ApresentacaoProduto | null;
  variacao: VariacaoProduto | null; quantidade_confirmada: string | null; revisado: boolean;
}

export interface Estabelecimento {
  id: string; cnpj: string; razao_social: string; apelido: string | null; nome_exibicao: string;
}

export interface Nota {
  id: string; chave: string; numero: string; serie: string;
  estabelecimento: Estabelecimento; emissao: string; quantidade_itens: number;
  valor_total: string; desconto: string; valor_a_pagar: string;
  itens: ItemNota[]; url_origem: string; situacao: SituacaoNota; importada_em: string | null;
}

export interface Leitura {
  id: string; url: string; nota: Nota | null; erro_consulta: string | null; criada_em: string;
}

export interface RevisaoItem {
  produto_id: string;
  marca_id?: string | null;
  variacao_id?: string | null;
  quantidade_confirmada: number;
}

export interface ProdutoRequest {
  nome: string;
  categoria_id: string;
  nao_solicitar_marca: boolean;
  tratar_apenas_como_unidades: boolean;
  contem_variacoes: boolean;
  unidade_medida: UnidadeMedida | null;
}

export interface VariacaoProdutoRequest {
  quantidade: number;
  unidade_medida: UnidadeMedida;
  descricao?: string | null;
}
