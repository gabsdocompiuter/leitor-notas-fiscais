export type SituacaoNota = 'lida' | 'em_revisao' | 'importada';
export type UnidadeMedida = 'KG' | 'G' | 'L' | 'ML';

export interface ConfiguracaoBanco {
  permitir_importacao: boolean;
}

export interface ImportacaoBancoResponse {
  mensagem: string;
}

export interface ErroApi {
  codigo: string;
  mensagem: string;
}
export interface Categoria {
  id: string;
  nome: string;
}
export interface Tag {
  id: string;
  nome: string;
}
export interface Marca {
  id: string;
  nome: string;
}
export interface UnidadeMedidaInfo {
  codigo: UnidadeMedida;
  descricao: string;
}

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
  nome_exibicao: string;
}

export interface ApresentacaoProduto {
  id: string;
  produto: Produto;
  marca: Marca | null;
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
  variacao: VariacaoProduto | null;
  quantidade_confirmada: string | null;
  quantidade_pacotes: string | null;
  unidades_por_pacote: string | null;
  revisado: boolean;
  tags: Tag[];
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
  considerar_proximo_mes: boolean;
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
  marca_id?: string | null;
  variacao_id?: string | null;
  quantidade_confirmada: number;
  quantidade_pacotes?: number | null;
  unidades_por_pacote?: number | null;
}

export interface RestricoesProduto {
  pode_alterar_estrutura: boolean;
  pode_excluir: boolean;
  motivo_alteracao_estrutura: string | null;
  motivo_exclusao: string | null;
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
}

export interface GrupoRelatorio {
  id: string;
  nome: string;
  total_pago: string;
  quantidade_itens: number;
}

export interface RelatorioMensal {
  mes: string;
  total_pago: string;
  total_desconto: string;
  quantidade_notas: number;
  quantidade_itens: number;
  total_mes_anterior: string;
  categorias: GrupoRelatorio[];
  tags: GrupoRelatorio[];
}

export interface ItemRelatorio {
  id: string;
  chave_nota: string;
  numero_nota: string;
  emissao: string;
  estabelecimento: string;
  produto: string;
  categoria_id: string;
  categoria: string;
  valor_bruto: string;
  desconto_rateado: string;
  valor_pago: string;
  tags: Tag[];
  considerar_proximo_mes: boolean;
}

export interface ItensRelatorio {
  itens: ItemRelatorio[];
  total: number;
}
