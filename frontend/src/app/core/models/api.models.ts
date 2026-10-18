export type SituacaoNota = 'lida' | 'em_revisao' | 'importada' | 'ignorada';
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
  nao_solicitar_sabor?: boolean;
  tratar_apenas_como_unidades: boolean;
  contem_variacoes: boolean;
  unidade_medida: UnidadeMedida | null;
}

export interface SaborProduto {
  id: string;
  produto_id: string;
  nome: string;
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
  sabor?: SaborProduto | null;
  quantidade_confirmada: string | null;
  quantidade_pacotes: string | null;
  unidades_por_pacote: string | null;
  revisado: boolean;
  ignorado: boolean;
  tags: Tag[];
}

export interface Estabelecimento {
  id: string;
  cnpj: string | null;
  razao_social: string | null;
  apelido: string | null;
  nome_exibicao: string;
}

export interface Nota {
  origem?: 'sefaz' | 'manual';
  id: string;
  chave: string | null;
  numero: string | null;
  serie: string | null;
  estabelecimento: Estabelecimento;
  emissao: string;
  quantidade_itens: number;
  valor_total: string;
  desconto: string;
  valor_a_pagar: string;
  itens: ItemNota[];
  url_origem: string | null;
  situacao: SituacaoNota;
  importada_em: string | null;
  considerar_proximo_mes: boolean;
  ignorada: boolean;
}

export interface Leitura {
  id: string;
  url: string;
  nota: Nota | null;
  erro_consulta: string | null;
  criada_em: string;
}

export interface CompraManualRequest {
  estabelecimento_id: string;
  data: string;
  itens: (RevisaoItem & ({ valor_total: string } | { valor_unitario: string }))[];
}

export interface RevisaoItem {
  valor_total?: string;
  valor_unitario?: string;
  produto_id: string;
  marca_id?: string | null;
  sabor_id?: string | null;
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
  nao_solicitar_sabor?: boolean;
  tratar_apenas_como_unidades: boolean;
  contem_variacoes: boolean;
  unidade_medida: UnidadeMedida | null;
}

export interface VariacaoProdutoRequest {
  quantidade: number;
  unidade_medida: UnidadeMedida;
}

export type UnidadeQuantidade = 'UN' | UnidadeMedida;

export interface QuantidadeRelatorio {
  quantidade: string;
  unidade: UnidadeQuantidade;
}

export interface GrupoRelatorio {
  id: string;
  nome: string;
  total_pago: string;
  quantidade_itens: number;
  quantidades_compradas?: QuantidadeRelatorio[];
}

export interface RelatorioMensal {
  mes: string;
  total_pago: string;
  total_desconto: string;
  quantidade_notas: number;
  quantidade_itens: number;
  quantidades_compradas?: QuantidadeRelatorio[];
  total_mes_anterior: string;
  categorias: GrupoRelatorio[];
  tags: GrupoRelatorio[];
}

export interface ItemRelatorio {
  id: string;
  nota_id?: string | null;
  chave_nota: string | null;
  numero_nota: string | null;
  emissao: string;
  estabelecimento: string;
  produto: string;
  produto_id: string;
  categoria_id: string;
  categoria: string;
  valor_bruto: string;
  desconto_rateado: string;
  valor_pago: string;
  tags: Tag[];
  considerar_proximo_mes: boolean;
  quantidade_comprada?: string | null;
  unidade_quantidade?: UnidadeQuantidade | null;
  estabelecimento_id?: string | null;
  marca_id?: string | null;
  marca?: string | null;
  sabor_id?: string | null;
  variacao_id?: string | null;
  sabor?: string | null;
  variacao?: string | null;
  quantidade_unidades?: string | null;
}

export interface ItensRelatorio {
  itens: ItemRelatorio[];
  total: number;
}

export interface ProdutoRelatorio extends GrupoRelatorio {
  valor_bruto: string;
  desconto_rateado: string;
  quantidade_comprada?: string | null;
  unidade_quantidade?: UnidadeQuantidade | null;
}

export type AgrupadorRelatorio = 'marca' | 'estabelecimento' | 'variacao';

export interface AgrupamentoRelatorio {
  id: string | null;
  nome: string;
  quantidade_registros: number;
  quantidade_comprada: string | null;
  unidade_quantidade: UnidadeQuantidade | null;
  total_pago: string;
  media_por_compra: string;
  quantidade_unidades: string | null;
}
